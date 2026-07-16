"""Provably-fair draw algorithm.

    1. Commit   -- commit_draw():   generate & store server_seed, publish its SHA-256 hash.
    2. Snapshot -- snapshot_tickets(): freeze ticket ranges, publish snapshot_hash.
    3. Beacon   -- run_draw():      fetch an unpredictable-in-advance Solana blockhash.
    4. Draw     -- run_draw():      winning_number = HMAC_SHA256(server_seed, snapshot_hash + beacon) % total_tickets.
    5. Reveal   -- everything above is stored on the immutable Draw row and
                   surfaced by /fair and /api/draws/<id>/ once status is DRAWN/PAID.

Anyone can recompute step 4 independently given the revealed server_seed,
snapshot_hash, beacon_blockhash and total_tickets -- see templates/core/fair.html
(SubtleCrypto verifier) and scripts/verify_draw.py (downloadable equivalent).
"""
import hashlib
import hmac
import json
import logging
import secrets
from decimal import Decimal

from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from ..models import Draw, JackpotPool, TicketSnapshot, User
from . import beacon
from . import ledger as ledger_service
from . import nowpayments
from .tickets import ball_to_tickets

logger = logging.getLogger(__name__)


def generate_server_seed() -> bytes:
    return secrets.token_bytes(32)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@transaction.atomic
def commit_draw(draw_date) -> Draw:
    """Step 1: commit. Idempotent -- if a Draw already exists for
    `draw_date` it is returned unchanged rather than re-seeded.
    """
    existing = Draw.objects.filter(draw_date=draw_date).first()
    if existing:
        return existing
    seed = generate_server_seed()
    return Draw.objects.create(
        draw_date=draw_date,
        server_seed=seed.hex(),
        server_seed_hash=sha256_hex(seed),
        status=Draw.Status.COMMITTED,
    )


def canonical_snapshot_json(rows: list) -> bytes:
    """Deterministic byte representation of the snapshot so anyone can
    recompute snapshot_hash themselves: sorted keys, no whitespace, rows
    pre-sorted by user_id by the caller.
    """
    return json.dumps(rows, sort_keys=True, separators=(',', ':')).encode('utf-8')


@transaction.atomic
def snapshot_tickets(draw: Draw) -> Draw:
    """Step 2: snapshot. Freezes ticket ranges for every user with
    tickets >= 1, ordered by user_id, and publishes
    snapshot_hash = SHA256(canonical_json(snapshot)).
    """
    if draw.status != Draw.Status.COMMITTED:
        return draw

    cursor = 0
    rows = []
    snap_objs = []
    for user in User.objects.order_by('id').iterator():
        tickets = ball_to_tickets(user.ball_balance)
        if tickets <= 0:
            continue
        start, end = cursor, cursor + tickets
        snap_objs.append(TicketSnapshot(
            draw=draw, user=user, ball_balance=user.ball_balance,
            ticket_start=start, ticket_end=end,
        ))
        rows.append({'user_id': user.id, 'ticket_start': start, 'ticket_end': end})
        cursor = end

    TicketSnapshot.objects.bulk_create(snap_objs)
    snapshot_hash = sha256_hex(canonical_snapshot_json(rows))

    draw.total_tickets = cursor
    draw.snapshot_hash = snapshot_hash
    draw.status = Draw.Status.SNAPSHOT if cursor > 0 else Draw.Status.VOID
    draw.snapshotted_at = timezone.now()
    draw.save(update_fields=['total_tickets', 'snapshot_hash', 'status', 'snapshotted_at'])
    return draw


def compute_winning_number(server_seed_hex: str, snapshot_hash_hex: str, beacon_blockhash: str, total_tickets: int) -> int:
    """winning_number = int(HMAC_SHA256(key=server_seed, msg=snapshot_hash||beacon), 16) % total_tickets

    `key` is the raw bytes of the hex-encoded server_seed. `msg` is the
    UTF-8 concatenation of the snapshot_hash hex string and the beacon
    blockhash string. This exact byte layout is what both the /fair page's
    JS verifier (SubtleCrypto) and scripts/verify_draw.py reproduce.
    """
    if total_tickets <= 0:
        raise ValueError('total_tickets must be positive.')
    key = bytes.fromhex(server_seed_hex)
    msg = (snapshot_hash_hex + beacon_blockhash).encode('utf-8')
    digest = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return int(digest, 16) % total_tickets


@transaction.atomic
def run_draw(draw: Draw) -> Draw:
    """Steps 3-5: beacon, draw, reveal. Determines the winning ticket and
    credits the jackpot to the winner's internal balance. Sending the
    onchain payout to a linked wallet is handled separately by
    core.tasks.payout_draw so a temporary RPC outage never blocks the
    drawing itself from completing on schedule.
    """
    if draw.status != Draw.Status.SNAPSHOT or draw.total_tickets == 0:
        return draw

    slot, blockhash = beacon.get_finalized_blockhash_after(timezone.now())

    winning_number = compute_winning_number(
        draw.server_seed, draw.snapshot_hash, blockhash, draw.total_tickets,
    )
    winner_snapshot = draw.snapshots.filter(
        ticket_start__lte=winning_number, ticket_end__gt=winning_number,
    ).select_related('user').first()

    pool = JackpotPool.objects.select_for_update().get(pk=JackpotPool.get_solo().pk)
    jackpot_amount = pool.total_jackpot_usdt

    draw.beacon_slot = slot
    draw.beacon_blockhash = blockhash
    draw.winning_number = winning_number
    draw.winner = winner_snapshot.user if winner_snapshot else None
    draw.jackpot_usdt = jackpot_amount
    draw.status = Draw.Status.DRAWN
    draw.drawn_at = timezone.now()
    draw.save()

    if winner_snapshot:
        ledger_service.credit_win(winner_snapshot.user, jackpot_amount, ref=f'draw:{draw.pk}')
        pool.jackpot_usdt = Decimal('0')
        pool.rollover_usdt = Decimal('0')
        pool.save(update_fields=['jackpot_usdt', 'rollover_usdt', 'updated_at'])

    return draw


@transaction.atomic
def payout_draw(draw: Draw) -> Draw:
    """Automatic USDT-TRC20 payout to the winner's payout address via
    NowPayments. The win is already reflected in the winner's internal
    balance by run_draw(); this step additionally requests a real payout
    when the winner has set a payout address, recording the request as an
    outgoing ledger entry so the internal balance stays in sync with what
    actually left the treasury. If no payout address is set, the win
    simply stays as spendable/withdrawable internal balance and the winner
    is emailed to set one.

    NowPayments payouts require a follow-up email verification code (see
    services.nowpayments.verify_payout, wired to a WithdrawalRequestAdmin-
    style admin action) before funds actually move -- this call only opens
    the batch and records its id; the actual send happens once an admin
    confirms the code.

    Idempotent and safe to re-run: a Draw only leaves status DRAWN once
    this completes successfully, so a transient API failure just leaves it
    DRAWN for the next tick to retry.
    """
    if draw.status != Draw.Status.DRAWN or not draw.winner:
        return draw

    winner = draw.winner
    payout_address = winner.usdt_trc20_payout_address

    if payout_address:
        try:
            payout = nowpayments.create_payout(payout_address, draw.jackpot_usdt, unique_external_id=f'draw:{draw.pk}')
        except Exception:
            logger.exception('Payout request failed for draw %s (winner %s)', draw.pk, winner.pk)
            return draw
        ledger_service.debit_for_payout(winner, draw.jackpot_usdt, tx_hash='', ref=f'draw:{draw.pk}')
        draw.payout_id = str(payout.get('id', ''))
    else:
        _notify_winner_no_payout_address(winner, draw)

    draw.status = Draw.Status.PAID
    draw.paid_at = timezone.now()
    draw.save(update_fields=['payout_id', 'status', 'paid_at'])
    return draw


def _notify_winner_no_payout_address(winner: User, draw: Draw):
    if not winner.email:
        return
    send_mail(
        subject='You won the OnlyBall jackpot!',
        message=(
            f'Congratulations! You won {draw.jackpot_usdt} USDT in the {draw.draw_date} drawing. '
            'It has been credited to your OnlyBall balance. Set your USDT-TRC20 payout address on '
            '/account/ and visit /withdraw/ to cash out.'
        ),
        from_email=None,
        recipient_list=[winner.email],
        fail_silently=True,
    )
