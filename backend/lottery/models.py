from django.db import models
from django.utils import timezone


def derive_code_from_address(address: str) -> str:
    """Deterministic 8-char code from a TRON address.

    Mirrors the frontend `deriveCodeFromAddress` (src/lib/affiliate/referral.ts)
    so referral links generated client-side match what we store and look up.
    """
    h = 0
    for ch in address:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return format(h, "X").rjust(8, "0")[:8]


class Account(models.Model):
    """A player, identified by their TRON wallet address (non-custodial)."""

    address = models.CharField(max_length=64, unique=True, db_index=True)
    referral_code = models.CharField(max_length=12, unique=True, db_index=True)
    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals",
    )
    referral_earnings_fudsx = models.DecimalField(
        max_digits=30, decimal_places=8, default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = derive_code_from_address(self.address)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.address


class Round(models.Model):
    OPEN = "open"
    DRAWN = "drawn"
    STATUS_CHOICES = [(OPEN, "Open"), (DRAWN, "Drawn")]

    index = models.PositiveIntegerField(unique=True, db_index=True)
    opens_at = models.DateTimeField(default=timezone.now)
    draws_at = models.DateTimeField()
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=OPEN)
    winning_numbers = models.JSONField(null=True, blank=True)
    jackpot_fudsx = models.DecimalField(max_digits=30, decimal_places=8, default=0)

    class Meta:
        ordering = ["-index"]

    def __str__(self):
        return f"Round #{self.index} ({self.status})"


class Ticket(models.Model):
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="tickets"
    )
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="tickets")
    numbers = models.JSONField()  # list of 6 ints
    txid = models.CharField(max_length=128, unique=True, db_index=True)
    paid_fudsx = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    matched = models.PositiveSmallIntegerField(default=0)
    is_winner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account.address} R#{self.round.index} {self.numbers}"


class ReferralCredit(models.Model):
    referrer = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="credits_received"
    )
    referee = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="credits_generated"
    )
    amount_fudsx = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    txid = models.CharField(max_length=128, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.referrer.address} <- {self.amount_fudsx} FUDSX"
