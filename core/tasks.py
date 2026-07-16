"""Celery tasks. Beat fires poll_pending_deposits and
process_approved_withdrawals every 60s (both are fallbacks/next-steps
around the NowPayments API, not the primary deposit-crediting path -- that
happens via the IPN webhook, see core.api_views.nowpayments_webhook), and
the ET-scheduled tasks (snapshot_tickets, run_draw, commit_next_seed) every
minute; each of the latter checks the actual America/New_York wall-clock
time itself (via zoneinfo, DST-safe) and is a no-op outside its
one-minute-per-day window, so it fires exactly once per real event
regardless of beat's own timezone.
"""
import logging

from celery import shared_task

from .models import Deposit, Draw, WithdrawalRequest
from .services import deposits as deposit_service
from .services import fairness, nowpayments
from .services.schedule import current_draw_date, now_et

logger = logging.getLogger(__name__)

_TERMINAL_DEPOSIT_STATUSES = {
    Deposit.Status.FINISHED, Deposit.Status.FAILED, Deposit.Status.REFUNDED, Deposit.Status.EXPIRED,
}


@shared_task
def poll_pending_deposits():
    """Fallback safety net for the NowPayments IPN webhook: re-checks any
    non-terminal Deposit against the API in case a webhook call was
    missed. Deposits without a payment_id yet haven't had a payment
    method chosen on the invoice page, so there's nothing to poll -- only
    the webhook can progress those.
    """
    for deposit in Deposit.objects.exclude(status__in=_TERMINAL_DEPOSIT_STATUSES).exclude(payment_id='').iterator():
        try:
            payment = nowpayments.get_payment_status(deposit.payment_id)
            deposit_service.apply_payment_update(deposit, payment)
        except Exception:
            logger.exception('Failed to poll NowPayments status for deposit %s', deposit.payment_id)


@shared_task
def process_approved_withdrawals():
    """Opens a NowPayments payout batch for every WithdrawalRequest an
    admin has approved. NowPayments payouts require a follow-up email
    verification code before funds actually move (see
    services.nowpayments.verify_payout) -- that confirmation step is a
    manual admin action, not automated here.
    """
    for wr in WithdrawalRequest.objects.filter(status=WithdrawalRequest.Status.APPROVED, payout_id=''):
        try:
            payout = nowpayments.create_payout(wr.address, wr.amount_usdt, unique_external_id=f'withdrawal:{wr.pk}')
            wr.payout_id = str(payout.get('id', ''))
            wr.save(update_fields=['payout_id'])
        except Exception:
            logger.exception('Failed to open payout batch for withdrawal %s', wr.pk)


@shared_task
def commit_next_seed():
    """Fires at 00:01 ET: commits the server_seed for tonight's drawing
    (draw_date = today + 1, i.e. the drawing that fires at the *next*
    midnight) and publishes its hash.
    """
    et_now = now_et()
    if et_now.hour == 0 and et_now.minute == 1:
        fairness.commit_draw(current_draw_date(et_now))


@shared_task
def snapshot_tickets():
    """Fires at 23:50 ET: freezes ticket ranges for tonight's drawing."""
    et_now = now_et()
    if et_now.hour == 23 and et_now.minute == 50:
        draw_date = current_draw_date(et_now)
        draw = Draw.objects.filter(draw_date=draw_date, status=Draw.Status.COMMITTED).first()
        if draw:
            fairness.snapshot_tickets(draw)


@shared_task
def run_draw():
    """Fires at 00:00 ET: beacon, draw, and payout for the drawing dated
    today (the one committed and snapshotted over the preceding day).
    """
    et_now = now_et()
    if et_now.hour == 0 and et_now.minute == 0:
        draw_date = et_now.date()
        draw = Draw.objects.filter(draw_date=draw_date, status=Draw.Status.SNAPSHOT).first()
        if draw:
            fairness.run_draw(draw)
            fairness.payout_draw(draw)

    # Retry payout for any earlier drawing that was drawn but whose payout
    # request failed / hadn't been attempted yet.
    for pending in Draw.objects.filter(status=Draw.Status.DRAWN):
        fairness.payout_draw(pending)
