import uuid
from decimal import Decimal

from django.db import transaction

from ..models import Deposit
from . import ledger as ledger_service
from . import nowpayments


@transaction.atomic
def create_deposit(user, price_amount, ipn_callback_url: str) -> Deposit:
    """Creates a USDT-TRC20 deposit via NowPayments' Payment API (not the
    Invoice API) for a chosen USD amount, so pay_address/pay_amount come
    back immediately and can be shown as a QR code on our own /deposit
    page -- no redirect to a NowPayments-hosted page required. The
    deposit is credited to the user's ledger later, either by the IPN
    webhook or the poll_pending_deposits fallback task, once NowPayments
    reports it 'finished' (see core.tasks).
    """
    order_id = uuid.uuid4().hex
    payment = nowpayments.create_payment(price_amount, order_id, ipn_callback_url)
    return Deposit.objects.create(
        user=user,
        order_id=order_id,
        payment_id=str(payment.get('payment_id', '')),
        pay_address=payment.get('pay_address', ''),
        pay_amount=payment.get('pay_amount'),
        price_amount=price_amount,
        status=payment.get('payment_status', Deposit.Status.WAITING),
    )


@transaction.atomic
def create_manual_deposit(user, price_amount, tx_hash: str, pay_address: str) -> Deposit:
    """Records a user's claim that they already sent `price_amount` USDT-TRC20
    to `pay_address` (the platform's fixed manual-deposit address), pending
    an admin's manual review of the on-chain transaction -- see
    approve_manual_deposit. Unlike create_deposit, no NowPayments API call
    happens here.
    """
    order_id = uuid.uuid4().hex
    return Deposit.objects.create(
        user=user,
        method=Deposit.Method.MANUAL,
        order_id=order_id,
        pay_address=pay_address,
        tx_hash=tx_hash,
        price_amount=price_amount,
        status=Deposit.Status.PENDING_REVIEW,
    )


@transaction.atomic
def approve_manual_deposit(deposit: Deposit) -> Deposit:
    """Admin-only: credits the ledger for a manual deposit once its on-chain
    transaction has been verified by eye. Mirrors the 'finished' branch of
    apply_payment_update; idempotent as long as callers only pass rows still
    in PENDING_REVIEW (see admin.DepositAdmin.approve_manual_deposits).
    """
    deposit = Deposit.objects.select_for_update().get(pk=deposit.pk)
    if deposit.status != Deposit.Status.PENDING_REVIEW:
        return deposit
    deposit.status = Deposit.Status.FINISHED
    deposit.save(update_fields=['status', 'updated_at'])
    ledger_service.credit_deposit(deposit.user, Decimal(str(deposit.price_amount)), deposit.tx_hash or deposit.order_id)
    return deposit


@transaction.atomic
def apply_payment_update(deposit: Deposit, payment_data: dict) -> Deposit:
    """Applies a NowPayments payment payload (from the IPN webhook or the
    poll_pending_deposits fallback) to `deposit`, crediting the user's
    ledger exactly once when the payment first reaches 'finished'.
    Re-applying the same or an earlier status is a safe no-op. Also fills
    in payment_id/pay_address/pay_amount the first time they appear, since
    those aren't known at invoice-creation time.
    """
    deposit = Deposit.objects.select_for_update().get(pk=deposit.pk)
    new_status = payment_data.get('payment_status', deposit.status)
    was_finished = deposit.status == Deposit.Status.FINISHED

    deposit.status = new_status
    deposit.tx_hash = payment_data.get('payin_hash') or deposit.tx_hash
    if payment_data.get('payment_id'):
        deposit.payment_id = str(payment_data['payment_id'])
    if payment_data.get('pay_address'):
        deposit.pay_address = payment_data['pay_address']
    if payment_data.get('pay_amount'):
        deposit.pay_amount = payment_data['pay_amount']
    deposit.save(update_fields=[
        'status', 'tx_hash', 'payment_id', 'pay_address', 'pay_amount', 'updated_at',
    ])

    if new_status == Deposit.Status.FINISHED and not was_finished:
        ledger_service.credit_deposit(
            deposit.user, Decimal(str(deposit.price_amount)), deposit.payment_id or deposit.order_id,
        )

    return deposit
