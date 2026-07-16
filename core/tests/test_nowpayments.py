import json
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings

from core.models import Deposit, User
from core.services import deposits as deposit_service
from core.services import nowpayments


@override_settings(NOWPAYMENTS_IPN_SECRET='test-secret')
class IpnSignatureTests(TestCase):
    def test_valid_signature_verifies(self):
        payload = {'payment_id': '123', 'payment_status': 'finished'}
        raw_body = nowpayments._canonical_json(payload)
        import hashlib
        import hmac
        sig = hmac.new(b'test-secret', raw_body, hashlib.sha512).hexdigest()
        self.assertTrue(nowpayments.verify_ipn_signature(raw_body, sig))

    def test_tampered_body_fails_verification(self):
        payload = {'payment_id': '123', 'payment_status': 'finished'}
        raw_body = nowpayments._canonical_json(payload)
        import hashlib
        import hmac
        sig = hmac.new(b'test-secret', raw_body, hashlib.sha512).hexdigest()
        tampered = json.dumps({'payment_id': '123', 'payment_status': 'failed'}).encode('utf-8')
        self.assertFalse(nowpayments.verify_ipn_signature(tampered, sig))

    def test_missing_signature_fails(self):
        self.assertFalse(nowpayments.verify_ipn_signature(b'{}', ''))


class ApplyPaymentUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', email='alice@example.com')
        self.deposit = Deposit.objects.create(
            user=self.user, order_id='order-1', payment_id='pay-1', pay_address='T' + '1' * 33,
            price_amount=Decimal('25'), status=Deposit.Status.WAITING,
        )

    def test_finished_status_credits_ledger_once(self):
        deposit_service.apply_payment_update(self.deposit, {'payment_status': 'finished'})
        self.assertEqual(self.user.usdt_balance, Decimal('25'))

        # A duplicate webhook/poll delivery for the same finished payment
        # must not double-credit the ledger.
        deposit_service.apply_payment_update(self.deposit, {'payment_status': 'finished'})
        self.assertEqual(self.user.usdt_balance, Decimal('25'))

    def test_intermediate_status_does_not_credit(self):
        deposit_service.apply_payment_update(self.deposit, {'payment_status': 'confirming'})
        self.assertEqual(self.user.usdt_balance, Decimal('0'))
        self.deposit.refresh_from_db()
        self.assertEqual(self.deposit.status, Deposit.Status.CONFIRMING)

    def test_first_webhook_fills_in_payment_id_and_pay_address(self):
        deposit = Deposit.objects.create(
            user=self.user, order_id='order-2', price_amount=Decimal('10'), status=Deposit.Status.WAITING,
        )
        deposit_service.apply_payment_update(deposit, {
            'payment_id': 'np-999', 'payment_status': 'waiting',
            'pay_address': 'T' + '2' * 33, 'pay_amount': '10.5',
        })
        deposit.refresh_from_db()
        self.assertEqual(deposit.payment_id, 'np-999')
        self.assertEqual(deposit.pay_address, 'T' + '2' * 33)
