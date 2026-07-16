"""Seeds demo data: a handful of players plus 10 days of completed past
drawings, so the "Last winners" section and stats have something to show
out of the box. Uses the real ledger/fairness services throughout (not
raw JSON fixtures) so every hash, ticket range and balance is internally
consistent and independently verifiable on /fair -- exactly like a real
drawing would produce.

The nightly beacon is monkeypatched to a synthetic (non-onchain) value so
this command works offline; that's clearly the case here since these
draws are backdated, not run live at midnight ET.
"""
import datetime
import random
import secrets
from decimal import Decimal
from unittest import mock

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import User
from core.services import fairness, ledger

DEMO_USERS = [
    'nova', 'atlas', 'juniper', 'sable', 'quill', 'ember', 'orbit', 'flux',
]

# A single, log-in-able demo account (the DEMO_USERS above get
# set_unusable_password() -- they only exist to populate "Last winners").
# Pre-funded so a visitor can try buying $BALL / withdrawing without
# making a real NowPayments deposit first.
DEMO_LOGIN_EMAIL = 'demo@onlyball.example'
DEMO_LOGIN_PASSWORD = 'OnlyBallDemo!1'
DEMO_LOGIN_USDT_FLOOR = Decimal('500')
DEMO_LOGIN_BALL_SPEND = Decimal('300')  # -> 3000 $BALL -> 30 tickets tonight


class Command(BaseCommand):
    help = 'Seed demo users, balances, 10 days of completed past drawings, and one log-in-able demo account for local/demo use.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=10, help='How many past drawings to generate.')

    def handle(self, *args, **options):
        days = options['days']
        users = self._seed_users()
        self._seed_draws(users, days)
        self._seed_demo_login_account()
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(users)} demo users and {days} past drawings.'))
        self.stdout.write(self.style.SUCCESS(
            f'Demo login account: {DEMO_LOGIN_EMAIL} / {DEMO_LOGIN_PASSWORD} '
            f'(${DEMO_LOGIN_USDT_FLOOR} USDT balance, some already converted to $BALL).'
        ))

    def _seed_demo_login_account(self):
        user, created = User.objects.get_or_create(
            username=DEMO_LOGIN_EMAIL,
            defaults={'email': DEMO_LOGIN_EMAIL, 'birth_date': datetime.date(1995, 1, 1)},
        )
        if created:
            user.set_password(DEMO_LOGIN_PASSWORD)
            user.save()

        if user.usdt_balance < DEMO_LOGIN_USDT_FLOOR:
            ledger.credit_deposit(user, DEMO_LOGIN_USDT_FLOOR - user.usdt_balance, secrets.token_hex(16))
        if user.ball_balance == 0:
            ledger.buy_ball(user, DEMO_LOGIN_BALL_SPEND)
        return user

    def _seed_users(self):
        users = []
        for name in DEMO_USERS:
            email = f'{name}@demo.onlyball.example'
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email, 'birth_date': datetime.date(1995, 1, 1)},
            )
            if created:
                user.set_unusable_password()
                user.save()
            users.append(user)

            # Give each demo user a plausible, varied deposit + $BALL balance.
            if user.usdt_balance == 0 and user.ball_balance == 0:
                deposit_amount = Decimal(random.choice([20, 50, 100, 250, 500]))
                ledger.credit_deposit(user, deposit_amount, secrets.token_hex(16))
                spend = (deposit_amount * Decimal(random.choice(['0.4', '0.6', '0.8', '1']))).quantize(Decimal('0.01'))
                if spend > 0:
                    ledger.buy_ball(user, spend)
        return users

    def _seed_draws(self, users, days):
        today = datetime.date.today()
        with mock.patch('core.services.fairness.beacon.get_finalized_blockhash_after') as mock_beacon:
            for i in range(days, 0, -1):
                draw_date = today - datetime.timedelta(days=i - 1)
                mock_beacon.return_value = (random.randint(200_000_000, 300_000_000), _fake_blockhash())

                with transaction.atomic():
                    draw = fairness.commit_draw(draw_date)
                    draw = fairness.snapshot_tickets(draw)
                    if draw.status != draw.Status.SNAPSHOT:
                        continue  # no tickets that day, nothing to draw
                    draw = fairness.run_draw(draw)
                    fairness.payout_draw(draw)

                # Top up a random player's $BALL between drawings so jackpots vary night to night.
                lucky = random.choice(users)
                topup = Decimal(random.choice([10, 20, 30, 50]))
                if lucky.usdt_balance < topup:
                    ledger.credit_deposit(lucky, topup, secrets.token_hex(16))
                ledger.buy_ball(lucky, topup)


def _fake_blockhash() -> str:
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    return ''.join(random.choice(alphabet) for _ in range(44))
