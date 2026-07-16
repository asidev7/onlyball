from decimal import Decimal

from django.test import TestCase

from core.services.tickets import ball_to_tickets


class TicketCalculationTests(TestCase):
    def test_below_threshold_earns_zero_tickets(self):
        self.assertEqual(ball_to_tickets(Decimal('99')), 0)

    def test_exact_threshold_earns_one_ticket(self):
        self.assertEqual(ball_to_tickets(Decimal('100')), 1)

    def test_five_hundred_earns_five_tickets(self):
        self.assertEqual(ball_to_tickets(Decimal('500')), 5)

    def test_one_thousand_earns_ten_tickets(self):
        self.assertEqual(ball_to_tickets(Decimal('1000')), 10)

    def test_no_cap_on_tickets(self):
        self.assertEqual(ball_to_tickets(Decimal('1000000')), 10000)

    def test_partial_balance_rounds_down(self):
        self.assertEqual(ball_to_tickets(Decimal('199')), 1)

    def test_zero_or_negative_balance_earns_no_tickets(self):
        self.assertEqual(ball_to_tickets(Decimal('0')), 0)
        self.assertEqual(ball_to_tickets(Decimal('-5')), 0)
