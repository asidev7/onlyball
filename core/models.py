import secrets
import uuid
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class ImmutableQuerySet(models.QuerySet):
    """Blocks bulk update()/delete(). Overriding a model's own save()/
    delete() (see LedgerEntry, ConfigChangeLog below) does NOT stop
    `Model.objects.filter(...).delete()` or `.update(...)` -- Django's bulk
    queryset operations bypass per-instance methods entirely. For an
    append-only financial ledger that gap defeats the whole point, so it's
    closed here too.
    """

    def delete(self):
        raise ValueError(f'{self.model.__name__} rows are append-only and cannot be bulk deleted.')

    def update(self, **kwargs):
        raise ValueError(f'{self.model.__name__} rows are append-only and cannot be bulk updated.')


class ImmutableManager(models.Manager.from_queryset(ImmutableQuerySet)):
    pass


class User(AbstractUser):
    """Auth identity. Email is optional (wallet-only accounts); a wallet
    can be linked to any account via WalletLink. Balances are NEVER stored
    on this model directly -- see services.ledger for the append-only
    LedgerEntry journal that is the single source of truth.
    """

    class KycStatus(models.TextChoices):
        NONE = 'none', 'None'
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'

    email = models.EmailField(unique=True, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    kyc_status = models.CharField(max_length=16, choices=KycStatus.choices, default=KycStatus.NONE)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    country_code = models.CharField(max_length=2, blank=True, help_text='ISO-3166 alpha-2, captured at signup')

    # Responsible gaming
    self_excluded_until = models.DateTimeField(null=True, blank=True)
    weekly_deposit_cap_usdt = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    # Where automatic jackpot payouts and withdrawals are sent. TRC20 (Tron)
    # addresses start with 'T' followed by 33 base58 characters.
    usdt_trc20_payout_address = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.email or self.username

    def save(self, *args, **kwargs):
        # Django's UserManager.normalize_email() turns a missing email into
        # '' rather than None (create_user(username=...) with no email
        # kwarg hits this). Since email is unique=True, two such users would
        # collide on '' -- normalize back to None so NULL-vs-NULL uniqueness
        # rules apply instead, which is what "email optional" requires for
        # wallet-only accounts.
        if self.email == '':
            self.email = None
        super().save(*args, **kwargs)

    @property
    def is_self_excluded(self):
        return bool(self.self_excluded_until and self.self_excluded_until > timezone.now())

    @property
    def is_adult(self):
        if not self.birth_date:
            return False
        today = timezone.localdate()
        age = today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
        return age >= 18

    @property
    def usdt_balance(self) -> Decimal:
        total = self.ledger_entries.aggregate(total=Sum('usdt_delta'))['total']
        return total or Decimal('0')

    @property
    def ball_balance(self) -> Decimal:
        total = self.ledger_entries.aggregate(total=Sum('ball_delta'))['total']
        return total or Decimal('0')

    @property
    def tickets_tonight(self) -> int:
        from .services.tickets import ball_to_tickets
        return ball_to_tickets(self.ball_balance)

    @property
    def primary_wallet(self):
        return self.wallets.filter(verified_at__isnull=False).order_by('created_at').first()

    @property
    def cumulative_deposits_usdt(self) -> Decimal:
        total = self.ledger_entries.filter(entry_type=LedgerEntry.EntryType.DEPOSIT).aggregate(
            total=Sum('usdt_delta')
        )['total']
        return total or Decimal('0')

    @property
    def kyc_required(self) -> bool:
        from .models import Config
        threshold = Config.get_solo().kyc_threshold_usdt
        return self.cumulative_deposits_usdt >= threshold


class WalletLink(models.Model):
    class Provider(models.TextChoices):
        PHANTOM = 'phantom', 'Phantom'
        SOLFLARE = 'solflare', 'Solflare'
        TRUST_WALLET = 'trust_wallet', 'Trust Wallet'
        METAMASK = 'metamask', 'MetaMask'
        TRONLINK = 'tronlink', 'TronLink'
        WALLETCONNECT = 'walletconnect', 'WalletConnect'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    address = models.CharField(max_length=128, unique=True, db_index=True)
    chain = models.CharField(max_length=32, default='solana')
    provider = models.CharField(max_length=32, choices=Provider.choices)
    nonce = models.CharField(max_length=64, blank=True)
    nonce_created_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.address[:6]}...{self.address[-4:]} ({self.provider})'

    def generate_nonce(self):
        self.nonce = secrets.token_hex(16)
        self.nonce_created_at = timezone.now()
        self.save(update_fields=['nonce', 'nonce_created_at'])
        return self.nonce


class Deposit(models.Model):
    """One USDT-TRC20 deposit created via the NowPayments Invoice API
    (services.nowpayments.create_invoice). `order_id` is generated
    up-front and is what the IPN webhook uses to find this row -- the
    NowPayments `payment_id` (and pay_address/pay_amount) aren't assigned
    until the user actually opens `invoice_url` and picks a payment
    method, so they start blank. `status` mirrors NowPayments'
    payment_status values; the ledger is credited once (idempotently, see
    services.deposits.apply_payment_update) when it reaches 'finished'.
    """

    class Status(models.TextChoices):
        WAITING = 'waiting', 'Waiting for payment'
        CONFIRMING = 'confirming', 'Confirming'
        CONFIRMED = 'confirmed', 'Confirmed'
        SENDING = 'sending', 'Sending'
        PARTIALLY_PAID = 'partially_paid', 'Partially paid'
        PENDING_REVIEW = 'pending_review', 'Pending admin review'
        FINISHED = 'finished', 'Finished'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
        EXPIRED = 'expired', 'Expired'

    class Method(models.TextChoices):
        NOWPAYMENTS = 'nowpayments', 'NowPayments'
        MANUAL = 'manual', 'Manual USDT-TRC20'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    method = models.CharField(max_length=16, choices=Method.choices, default=Method.NOWPAYMENTS)
    order_id = models.CharField(max_length=64, unique=True, db_index=True)
    invoice_url = models.URLField(max_length=255, blank=True)
    payment_id = models.CharField(max_length=64, blank=True, db_index=True)
    pay_address = models.CharField(max_length=128, blank=True)
    pay_amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    price_amount = models.DecimalField(max_digits=18, decimal_places=6)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.WAITING)
    tx_hash = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_id} ({self.status})'


class LedgerEntry(models.Model):
    """Append-only accounting journal. Balances are derived by summing
    usdt_delta / ball_delta over a user's entries -- never mutate a field
    on User directly. Rows are immutable once created (see save()/delete()).
    """

    class EntryType(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        BUY_BALL = 'buy_ball', 'Buy $BALL'
        WIN = 'win', 'Draw win'
        WITHDRAW = 'withdraw', 'Withdrawal'
        FEE = 'fee', 'Platform fee'
        REFUND = 'refund', 'Refund'
        ADJUSTMENT = 'adjustment', 'Manual adjustment'

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ledger_entries')
    entry_type = models.CharField(max_length=16, choices=EntryType.choices)
    usdt_delta = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    ball_delta = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    ref = models.CharField(max_length=128, blank=True, help_text='e.g. draw id, withdrawal id, tx hash')
    tx_hash = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ImmutableManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'entry_type']),
        ]
        verbose_name_plural = 'Ledger entries'

    def __str__(self):
        return f'{self.user} {self.entry_type} usdt={self.usdt_delta} ball={self.ball_delta}'

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError('LedgerEntry rows are append-only and cannot be modified.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('LedgerEntry rows are append-only and cannot be deleted.')


class JackpotPool(models.Model):
    """Singleton tracking the live jackpot/rollover/fee pools that accrue
    from the 70/20/10 split of every $BALL purchase (see services.ledger).
    Not part of the model list in the product brief verbatim, but required
    to realize the "70% jackpot / 20% rollover / 10% fee" rule since that
    money isn't credited to any single user's ledger.
    """

    jackpot_usdt = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    rollover_usdt = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    fee_usdt = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'jackpot={self.jackpot_usdt} rollover={self.rollover_usdt}'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def total_jackpot_usdt(self) -> Decimal:
        return self.jackpot_usdt + self.rollover_usdt


class Draw(models.Model):
    class Status(models.TextChoices):
        COMMITTED = 'committed', 'Seed committed'
        SNAPSHOT = 'snapshot', 'Tickets snapshotted'
        DRAWN = 'drawn', 'Drawn'
        PAID = 'paid', 'Paid out'
        VOID = 'void', 'Void (no tickets)'

    draw_date = models.DateField(unique=True, help_text='ET calendar date this drawing is for')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.COMMITTED)

    # 1. Commit
    server_seed_hash = models.CharField(max_length=64)
    server_seed = models.CharField(max_length=64, blank=True)  # revealed after the draw

    # 2. Snapshot
    snapshot_hash = models.CharField(max_length=64, blank=True)
    total_tickets = models.PositiveBigIntegerField(default=0)

    # 3. Beacon
    beacon_slot = models.BigIntegerField(null=True, blank=True)
    beacon_blockhash = models.CharField(max_length=128, blank=True)

    # 4. Draw
    winning_number = models.PositiveBigIntegerField(null=True, blank=True)
    winner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='wins')
    jackpot_usdt = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))

    # 5. Reveal / payout
    payout_id = models.CharField(max_length=64, blank=True, help_text='NowPayments payout batch id')
    payout_tx = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    snapshotted_at = models.DateTimeField(null=True, blank=True)
    drawn_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-draw_date']

    def __str__(self):
        return f'Draw {self.draw_date} ({self.status})'


class TicketSnapshot(models.Model):
    draw = models.ForeignKey(Draw, on_delete=models.CASCADE, related_name='snapshots')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_snapshots')
    ball_balance = models.DecimalField(max_digits=18, decimal_places=6)
    ticket_start = models.PositiveBigIntegerField()
    ticket_end = models.PositiveBigIntegerField()

    class Meta:
        ordering = ['ticket_start']
        unique_together = [('draw', 'user')]

    def __str__(self):
        return f'{self.user} tickets [{self.ticket_start},{self.ticket_end}) in {self.draw}'


class WithdrawalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        KYC_REQUIRED = 'kyc_required', 'KYC required'
        APPROVED = 'approved', 'Approved'
        SENT = 'sent', 'Sent'
        REJECTED = 'rejected', 'Rejected'

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='withdrawal_requests')
    address = models.CharField(max_length=128)
    amount_usdt = models.DecimalField(max_digits=18, decimal_places=6)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    payout_id = models.CharField(max_length=64, blank=True, help_text='NowPayments payout batch id')
    tx_hash = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} withdraw {self.amount_usdt} USDT ({self.status})'


class Config(models.Model):
    """Singleton runtime configuration. Every change is mirrored into
    ConfigChangeLog by services.config.update_config() -- never edit
    fields directly outside of that helper.
    """

    ball_price_usdt = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0.10'))
    ticket_threshold = models.PositiveIntegerField(default=100)
    jackpot_bps = models.PositiveIntegerField(default=7000)
    rollover_bps = models.PositiveIntegerField(default=2000)
    fee_bps = models.PositiveIntegerField(default=1000)
    min_withdraw_usdt = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('5'))
    kyc_threshold_usdt = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('100'))
    manual_deposit_address = models.CharField(
        max_length=128, blank=True,
        help_text='USDT-TRC20 address shown for manual deposits (admin-reviewed instead of NowPayments).',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuration'
        verbose_name_plural = 'Configuration'

    def __str__(self):
        return 'Site configuration'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class ConfigChangeLog(models.Model):
    field_name = models.CharField(max_length=64)
    old_value = models.CharField(max_length=256)
    new_value = models.CharField(max_length=256)
    changed_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='config_changes')
    changed_at = models.DateTimeField(auto_now_add=True)

    objects = ImmutableManager()

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.field_name}: {self.old_value} -> {self.new_value}'

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError('ConfigChangeLog rows are append-only and cannot be modified.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('ConfigChangeLog rows are append-only and cannot be deleted.')


class SelfExclusion(models.Model):
    """History of self-exclusion periods a user has enacted (7/30/90 days).
    User.self_excluded_until always mirrors the latest active record.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='self_exclusions')
    days = models.PositiveIntegerField()
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} excluded {self.days}d until {self.ends_at}'
