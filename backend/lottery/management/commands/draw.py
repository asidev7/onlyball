"""Operator command: close the open round, draw winning numbers, mark winners.

Usage:
    python manage.py draw                  # random 6 numbers
    python manage.py draw --numbers 4 8 15 16 23 42

Payouts of FUDSX to winners stay operator-side (sent manually from the
treasury wallet) so the server never holds private keys.
"""

import secrets

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from lottery.models import Round
from lottery.services.rounds import get_or_create_current_round


def _draw_numbers() -> list[int]:
    pool = list(range(1, 50))
    picks = set()
    while len(picks) < 6:
        picks.add(secrets.choice(pool))
    return sorted(picks)


class Command(BaseCommand):
    help = "Close the open round and draw the winning numbers."

    def add_arguments(self, parser):
        parser.add_argument("--numbers", nargs=6, type=int, default=None)

    def handle(self, *args, **options):
        rnd = Round.objects.filter(status=Round.OPEN).order_by("-index").first()
        if not rnd:
            raise CommandError("No open round to draw.")

        numbers = options["numbers"]
        if numbers:
            numbers = sorted(set(numbers))
            if len(numbers) != 6 or any(n < 1 or n > 49 for n in numbers):
                raise CommandError("Provide 6 distinct numbers in 1-49.")
        else:
            numbers = _draw_numbers()

        winning = set(numbers)
        with transaction.atomic():
            rnd.winning_numbers = numbers
            rnd.status = Round.DRAWN
            rnd.save(update_fields=["winning_numbers", "status"])

            winners = []
            for ticket in rnd.tickets.select_related("account"):
                matched = len(winning & set(ticket.numbers))
                ticket.matched = matched
                ticket.is_winner = matched == 6
                ticket.save(update_fields=["matched", "is_winner"])
                if ticket.is_winner:
                    winners.append(ticket)

            new_round = get_or_create_current_round()

        self.stdout.write(self.style.SUCCESS(f"Round #{rnd.index} drawn: {numbers}"))
        if winners:
            share = rnd.jackpot_fudsx / len(winners)
            self.stdout.write(
                self.style.WARNING(
                    f"{len(winners)} jackpot winner(s) — pay {share} FUDSX each "
                    f"from the treasury:"
                )
            )
            for w in winners:
                self.stdout.write(f"  {w.account.address}  ({w.txid})")
        else:
            self.stdout.write("No jackpot winner. Pool rolls into the next round.")
            new_round.jackpot_fudsx = rnd.jackpot_fudsx
            new_round.save(update_fields=["jackpot_fudsx"])
        self.stdout.write(self.style.SUCCESS(f"Opened round #{new_round.index}."))
