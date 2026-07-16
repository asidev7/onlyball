"""Append-only ledger operations. Every function here runs inside a DB
transaction and locks the acting user's row with select_for_update before
reading their derived balance, so concurrent requests (e.g. two buy_ball
calls racing) can't overspend a balance that only exists as a SUM() over
LedgerEntry rows.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from ..models import Config, JackpotPool, LedgerEntry, User, WithdrawalRequest


def weekly_deposits_usdt(user) -> Decimal:
    """Sum of a user's deposits in the trailing 7 days, for comparing
    against their self-imposed weekly_deposit_cap_usdt (responsible
    gaming). Deposits themselves can't be rejected -- the USDT has
    already arrived onchain by the time we see it -- so this is used to
    warn the user/notify rather than block a transfer already made.
    """
    cutoff = timezone.now() - timezone.timedelta(days=7)
    total = user.ledger_entries.filter(
        entry_type=LedgerEntry.EntryType.DEPOSIT, created_at__gte=cutoff,
    ).aggregate(total=Sum('usdt_delta'))['total']
    return total or Decimal('0')


def _create_entry(user, entry_type, usdt_delta=Decimal('0'), ball_delta=Decimal('0'), ref='', tx_hash=''):
    return LedgerEntry.objects.create(
        user=user,
        entry_type=entry_type,
        usdt_delta=usdt_delta,
        ball_delta=ball_delta,
        ref=ref,
        tx_hash=tx_hash,
    )


@transaction.atomic
def credit_deposit(user, amount_usdt: Decimal, tx_hash: str) -> LedgerEntry:
    return _create_entry(user, LedgerEntry.EntryType.DEPOSIT, usdt_delta=amount_usdt, ref=tx_hash, tx_hash=tx_hash)


@transaction.atomic
def buy_ball(user, usdt_amount: Decimal) -> LedgerEntry:
    """Debit usdt_balance, credit ball_balance at the configured rate, and
    route the purchase into the jackpot/rollover/fee pools per the
    configured basis-point split. Raises ValueError on insufficient funds.
    """
    if usdt_amount <= 0:
        raise ValueError('Amount must be positive.')

    locked_user = User.objects.select_for_update().get(pk=user.pk)
    if locked_user.usdt_balance < usdt_amount:
        raise ValueError('Insufficient USDT balance.')

    config = Config.get_solo()
    ball_amount = (usdt_amount / config.ball_price_usdt).quantize(Decimal('0.000001'))

    entry = _create_entry(
        locked_user, LedgerEntry.EntryType.BUY_BALL,
        usdt_delta=-usdt_amount, ball_delta=ball_amount,
    )

    pool = JackpotPool.objects.select_for_update().get(pk=JackpotPool.get_solo().pk)
    jackpot_share = (usdt_amount * config.jackpot_bps / Decimal('10000')).quantize(Decimal('0.000001'))
    rollover_share = (usdt_amount * config.rollover_bps / Decimal('10000')).quantize(Decimal('0.000001'))
    fee_share = usdt_amount - jackpot_share - rollover_share  # remainder avoids rounding leakage
    pool.jackpot_usdt += jackpot_share
    pool.rollover_usdt += rollover_share
    pool.fee_usdt += fee_share
    pool.save(update_fields=['jackpot_usdt', 'rollover_usdt', 'fee_usdt', 'updated_at'])

    return entry


@transaction.atomic
def request_withdrawal(user, address: str, amount_usdt: Decimal) -> WithdrawalRequest:
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    config = Config.get_solo()
    if amount_usdt < config.min_withdraw_usdt:
        raise ValueError(f'Minimum withdrawal is {config.min_withdraw_usdt} USDT.')
    if locked_user.usdt_balance < amount_usdt:
        raise ValueError('Insufficient USDT balance.')

    needs_kyc = (
        locked_user.cumulative_deposits_usdt >= config.kyc_threshold_usdt
        or amount_usdt >= config.kyc_threshold_usdt
    ) and locked_user.kyc_status != User.KycStatus.VERIFIED

    wr = WithdrawalRequest.objects.create(
        user=locked_user,
        address=address,
        amount_usdt=amount_usdt,
        status=WithdrawalRequest.Status.KYC_REQUIRED if needs_kyc else WithdrawalRequest.Status.PENDING,
    )
    _create_entry(locked_user, LedgerEntry.EntryType.WITHDRAW, usdt_delta=-amount_usdt, ref=str(wr.pk))
    return wr


@transaction.atomic
def reject_withdrawal(withdrawal: WithdrawalRequest):
    withdrawal.status = WithdrawalRequest.Status.REJECTED
    withdrawal.processed_at = timezone.now()
    withdrawal.save(update_fields=['status', 'processed_at'])
    _create_entry(withdrawal.user, LedgerEntry.EntryType.REFUND, usdt_delta=withdrawal.amount_usdt, ref=str(withdrawal.pk))


@transaction.atomic
def mark_withdrawal_sent(withdrawal: WithdrawalRequest, tx_hash: str):
    withdrawal.status = WithdrawalRequest.Status.SENT
    withdrawal.tx_hash = tx_hash
    withdrawal.processed_at = timezone.now()
    withdrawal.save(update_fields=['status', 'tx_hash', 'processed_at'])


@transaction.atomic
def credit_win(user, amount_usdt: Decimal, ref: str) -> LedgerEntry:
    return _create_entry(user, LedgerEntry.EntryType.WIN, usdt_delta=amount_usdt, ref=ref)


@transaction.atomic
def debit_for_payout(user, amount_usdt: Decimal, tx_hash: str, ref: str) -> LedgerEntry:
    """Records the automatic onchain payout of a win as an outgoing
    withdrawal against the user's internal balance.
    """
    return _create_entry(
        user, LedgerEntry.EntryType.WITHDRAW, usdt_delta=-amount_usdt, ref=ref, tx_hash=tx_hash,
    )
