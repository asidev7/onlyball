import datetime
from unittest import mock

from django.test import TestCase

from core.models import Draw, JackpotPool, User
from core.services import fairness, ledger


class WinningNumberFixedVectorTests(TestCase):
    """Pins the exact byte layout of the provably-fair algorithm: if this
    ever silently changes, every previously-published drawing becomes
    unverifiable, so these vectors must never need updating.
    """

    def test_known_vector(self):
        server_seed_hex = '00' * 32
        snapshot_hash = 'a' * 64
        beacon = 'FAKEBLOCKHASH123'
        total_tickets = 1000

        result = fairness.compute_winning_number(server_seed_hex, snapshot_hash, beacon, total_tickets)

        self.assertEqual(result, 161)

    def test_deterministic_for_same_inputs(self):
        args = ('11' * 32, 'deadbeef' * 8, 'SomeBlockhash', 500)
        self.assertEqual(fairness.compute_winning_number(*args), fairness.compute_winning_number(*args))

    def test_changing_beacon_changes_result(self):
        base = ('22' * 32, 'cafebabe' * 8, 500)
        r1 = fairness.compute_winning_number(base[0], base[1], 'beaconA', base[2])
        r2 = fairness.compute_winning_number(base[0], base[1], 'beaconB', base[2])
        self.assertNotEqual(r1, r2)

    def test_result_always_within_range(self):
        for total in (1, 2, 7, 999):
            n = fairness.compute_winning_number('ab' * 32, 'cd' * 32, 'beacon', total)
            self.assertGreaterEqual(n, 0)
            self.assertLess(n, total)


class CanonicalSnapshotJsonTests(TestCase):
    def test_key_order_does_not_affect_hash(self):
        rows_a = [{'user_id': 1, 'ticket_start': 0, 'ticket_end': 1}]
        rows_b = [{'ticket_end': 1, 'ticket_start': 0, 'user_id': 1}]
        self.assertEqual(
            fairness.canonical_snapshot_json(rows_a),
            fairness.canonical_snapshot_json(rows_b),
        )


class DrawPipelineTests(TestCase):
    def setUp(self):
        self.tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    def test_commit_draw_is_idempotent(self):
        draw1 = fairness.commit_draw(self.tomorrow)
        draw2 = fairness.commit_draw(self.tomorrow)
        self.assertEqual(draw1.pk, draw2.pk)
        self.assertEqual(draw1.server_seed, draw2.server_seed)

    def test_commit_draw_publishes_hash_matching_seed(self):
        import hashlib
        draw = fairness.commit_draw(self.tomorrow)
        self.assertEqual(draw.server_seed_hash, hashlib.sha256(bytes.fromhex(draw.server_seed)).hexdigest())

    def test_snapshot_with_no_tickets_marks_draw_void(self):
        draw = fairness.commit_draw(self.tomorrow)
        draw = fairness.snapshot_tickets(draw)
        self.assertEqual(draw.status, Draw.Status.VOID)
        self.assertEqual(draw.total_tickets, 0)

    def test_snapshot_assigns_contiguous_ticket_ranges(self):
        from decimal import Decimal
        alice = User.objects.create_user(username='alice')
        bob = User.objects.create_user(username='bob')
        ledger.credit_deposit(alice, Decimal('100'), 'tx1')
        ledger.buy_ball(alice, Decimal('100'))  # 1000 $BALL -> 10 tickets
        ledger.credit_deposit(bob, Decimal('20'), 'tx2')
        ledger.buy_ball(bob, Decimal('20'))  # 200 $BALL -> 2 tickets

        draw = fairness.commit_draw(self.tomorrow)
        draw = fairness.snapshot_tickets(draw)

        self.assertEqual(draw.total_tickets, 12)
        snaps = {s.user_id: s for s in draw.snapshots.all()}
        self.assertEqual((snaps[alice.id].ticket_start, snaps[alice.id].ticket_end), (0, 10))
        self.assertEqual((snaps[bob.id].ticket_start, snaps[bob.id].ticket_end), (10, 12))

    @mock.patch('core.services.fairness.beacon.get_finalized_blockhash_after')
    def test_run_draw_picks_winner_and_credits_jackpot(self, mock_beacon):
        from decimal import Decimal
        mock_beacon.return_value = (123, 'FIXEDBEACON')

        alice = User.objects.create_user(username='alice')
        ledger.credit_deposit(alice, Decimal('10'), 'tx1')
        ledger.buy_ball(alice, Decimal('10'))  # sole ticket holder

        draw = fairness.commit_draw(self.tomorrow)
        draw = fairness.snapshot_tickets(draw)
        draw = fairness.run_draw(draw)

        self.assertEqual(draw.status, Draw.Status.DRAWN)
        self.assertEqual(draw.winner_id, alice.id)
        self.assertEqual(draw.beacon_blockhash, 'FIXEDBEACON')
        expected_number = fairness.compute_winning_number(
            draw.server_seed, draw.snapshot_hash, 'FIXEDBEACON', draw.total_tickets,
        )
        self.assertEqual(draw.winning_number, expected_number)
        self.assertEqual(alice.usdt_balance, draw.jackpot_usdt)
        self.assertEqual(JackpotPool.get_solo().jackpot_usdt, Decimal('0'))

    @mock.patch('core.services.fairness.beacon.get_finalized_blockhash_after')
    def test_payout_draw_without_wallet_stays_credited_internally(self, mock_beacon):
        from decimal import Decimal
        mock_beacon.return_value = (1, 'BEACON')
        alice = User.objects.create_user(username='alice', email='alice@example.com')
        ledger.credit_deposit(alice, Decimal('10'), 'tx1')
        ledger.buy_ball(alice, Decimal('10'))

        draw = fairness.commit_draw(self.tomorrow)
        draw = fairness.snapshot_tickets(draw)
        draw = fairness.run_draw(draw)
        draw = fairness.payout_draw(draw)

        self.assertEqual(draw.status, Draw.Status.PAID)
        self.assertEqual(draw.payout_tx, '')
        self.assertGreater(alice.usdt_balance, Decimal('0'))

    @mock.patch('core.services.fairness.nowpayments.create_payout')
    @mock.patch('core.services.fairness.beacon.get_finalized_blockhash_after')
    def test_payout_draw_with_payout_address_requests_nowpayments_payout(self, mock_beacon, mock_payout):
        from decimal import Decimal
        mock_beacon.return_value = (1, 'BEACON')
        mock_payout.return_value = {'id': 'payout-123'}

        alice = User.objects.create_user(
            username='alice', email='alice@example.com', usdt_trc20_payout_address='T' + '1' * 33,
        )
        ledger.credit_deposit(alice, Decimal('10'), 'tx1')
        ledger.buy_ball(alice, Decimal('10'))

        draw = fairness.commit_draw(self.tomorrow)
        draw = fairness.snapshot_tickets(draw)
        draw = fairness.run_draw(draw)
        draw = fairness.payout_draw(draw)

        mock_payout.assert_called_once()
        self.assertEqual(draw.status, Draw.Status.PAID)
        self.assertEqual(draw.payout_id, 'payout-123')
        self.assertEqual(alice.usdt_balance, Decimal('0'))  # credited then immediately debited for the payout
