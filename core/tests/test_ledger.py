from decimal import Decimal

from django.test import TestCase

from core.models import Config, LedgerEntry, User, WithdrawalRequest
from core.services import ledger


class LedgerAtomicityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', email='alice@example.com')

    def test_deposit_credits_usdt_balance(self):
        ledger.credit_deposit(self.user, Decimal('25'), 'tx-1')
        self.assertEqual(self.user.usdt_balance, Decimal('25'))

    def test_buy_ball_debits_usdt_and_credits_ball_at_configured_rate(self):
        ledger.credit_deposit(self.user, Decimal('50'), 'tx-1')
        ledger.buy_ball(self.user, Decimal('10'))
        self.assertEqual(self.user.usdt_balance, Decimal('40'))
        self.assertEqual(self.user.ball_balance, Decimal('100'))  # 10 / 0.10

    def test_buy_ball_rejects_insufficient_balance(self):
        with self.assertRaises(ValueError):
            ledger.buy_ball(self.user, Decimal('10'))
        self.assertEqual(self.user.usdt_balance, Decimal('0'))

    def test_buy_ball_splits_into_jackpot_pool_per_config_bps(self):
        ledger.credit_deposit(self.user, Decimal('100'), 'tx-1')
        ledger.buy_ball(self.user, Decimal('100'))
        pool = Config.get_solo()
        from core.models import JackpotPool
        p = JackpotPool.get_solo()
        self.assertEqual(p.jackpot_usdt, Decimal('70'))   # 70%
        self.assertEqual(p.rollover_usdt, Decimal('20'))  # 20%
        self.assertEqual(p.fee_usdt, Decimal('10'))       # 10%

    def test_ledger_entry_is_append_only(self):
        entry = ledger.credit_deposit(self.user, Decimal('5'), 'tx-2')
        entry.usdt_delta = Decimal('999')
        with self.assertRaises(ValueError):
            entry.save()
        with self.assertRaises(ValueError):
            entry.delete()

    def test_ledger_entry_bulk_delete_and_update_are_also_blocked(self):
        # Overriding Model.delete()/save() alone does NOT stop bulk
        # queryset .delete()/.update() calls -- Django routes those
        # around the instance methods entirely, so the append-only
        # guarantee has to be enforced at the queryset/manager level too.
        ledger.credit_deposit(self.user, Decimal('5'), 'tx-3')
        with self.assertRaises(ValueError):
            LedgerEntry.objects.filter(user=self.user).delete()
        with self.assertRaises(ValueError):
            LedgerEntry.objects.filter(user=self.user).update(usdt_delta=Decimal('0'))
        self.assertEqual(self.user.usdt_balance, Decimal('5'))

    def test_withdrawal_requires_kyc_above_threshold(self):
        ledger.credit_deposit(self.user, Decimal('200'), 'tx-3')
        wr = ledger.request_withdrawal(self.user, 'SomeSolanaAddress111', Decimal('150'))
        self.assertEqual(wr.status, WithdrawalRequest.Status.KYC_REQUIRED)
        # the internal balance is still debited immediately (funds reserved)
        self.assertEqual(self.user.usdt_balance, Decimal('50'))

    def test_withdrawal_below_kyc_threshold_is_pending(self):
        ledger.credit_deposit(self.user, Decimal('50'), 'tx-4')
        wr = ledger.request_withdrawal(self.user, 'SomeSolanaAddress111', Decimal('10'))
        self.assertEqual(wr.status, WithdrawalRequest.Status.PENDING)

    def test_reject_withdrawal_refunds_balance(self):
        ledger.credit_deposit(self.user, Decimal('50'), 'tx-5')
        wr = ledger.request_withdrawal(self.user, 'SomeSolanaAddress111', Decimal('10'))
        ledger.reject_withdrawal(wr)
        self.assertEqual(self.user.usdt_balance, Decimal('50'))
        self.assertEqual(wr.status, 'rejected')

    def test_credit_win_and_debit_for_payout(self):
        ledger.credit_win(self.user, Decimal('30'), ref='draw:1')
        self.assertEqual(self.user.usdt_balance, Decimal('30'))
        ledger.debit_for_payout(self.user, Decimal('30'), 'onchain-tx', ref='draw:1')
        self.assertEqual(self.user.usdt_balance, Decimal('0'))

    def test_weekly_deposits_only_counts_recent_deposits(self):
        from django.utils import timezone
        from django.db import connection

        ledger.credit_deposit(self.user, Decimal('10'), 'tx-recent')
        old_entry = LedgerEntry.objects.create(
            user=self.user, entry_type=LedgerEntry.EntryType.DEPOSIT, usdt_delta=Decimal('999'),
        )
        # Ledger rows are append-only even in bulk (see test above), so
        # backdating this row for the test has to go around the ORM entirely.
        with connection.cursor() as cursor:
            cursor.execute(
                'UPDATE core_ledgerentry SET created_at = %s WHERE id = %s',
                [timezone.now() - timezone.timedelta(days=10), old_entry.pk],
            )
        self.assertEqual(ledger.weekly_deposits_usdt(self.user), Decimal('10'))
