from django.contrib import admin

from .models import Account, ReferralCredit, Round, Ticket


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("address", "referral_code", "referred_by", "referral_earnings_fudsx", "created_at")
    search_fields = ("address", "referral_code")


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ("index", "status", "draws_at", "jackpot_fudsx", "winning_numbers")
    list_filter = ("status",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("account", "round", "numbers", "matched", "is_winner", "paid_fudsx", "created_at")
    list_filter = ("is_winner", "round")
    search_fields = ("account__address", "txid")


@admin.register(ReferralCredit)
class ReferralCreditAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referee", "amount_fudsx", "created_at")
    search_fields = ("referrer__address", "referee__address")
