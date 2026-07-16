from django import forms as django_forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import path

from .models import (
    Config,
    ConfigChangeLog,
    Deposit,
    Draw,
    JackpotPool,
    LedgerEntry,
    SelfExclusion,
    TicketSnapshot,
    User,
    WalletLink,
    WithdrawalRequest,
)


@admin.register(User)
class OnlyBallUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'kyc_status', 'is_self_excluded_display', 'usdt_balance', 'ball_balance', 'is_staff')
    list_filter = ('kyc_status', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('OnlyBall', {
            'fields': (
                'birth_date', 'kyc_status', 'email_verified_at', 'country_code',
                'self_excluded_until', 'weekly_deposit_cap_usdt', 'usdt_trc20_payout_address',
            ),
        }),
    )

    @admin.display(description='Self-excluded?', boolean=True)
    def is_self_excluded_display(self, obj):
        return obj.is_self_excluded

    @admin.display(description='USDT balance')
    def usdt_balance(self, obj):
        return obj.usdt_balance

    @admin.display(description='$BALL balance')
    def ball_balance(self, obj):
        return obj.ball_balance


@admin.register(WalletLink)
class WalletLinkAdmin(admin.ModelAdmin):
    list_display = ('address', 'user', 'provider', 'chain', 'verified_at', 'created_at')
    list_filter = ('provider', 'chain')
    search_fields = ('address', 'user__username', 'user__email')
    readonly_fields = ('nonce', 'nonce_created_at')


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'method', 'price_amount', 'pay_amount', 'status', 'tx_hash', 'created_at')
    list_filter = ('status', 'method')
    search_fields = ('order_id', 'payment_id', 'pay_address', 'tx_hash', 'user__username', 'user__email')
    actions = ['approve_manual_deposits', 'reject_manual_deposits']

    def has_add_permission(self, request):
        return False

    @admin.action(description='Approve manual deposit (credits balance immediately)')
    def approve_manual_deposits(self, request, queryset):
        from .services import deposits as deposit_service
        count = 0
        for deposit in queryset.filter(method=Deposit.Method.MANUAL, status=Deposit.Status.PENDING_REVIEW):
            deposit_service.approve_manual_deposit(deposit)
            count += 1
        self.message_user(request, f'{count} manual deposit(s) approved and credited.')

    @admin.action(description='Reject manual deposit')
    def reject_manual_deposits(self, request, queryset):
        updated = queryset.filter(
            method=Deposit.Method.MANUAL, status=Deposit.Status.PENDING_REVIEW,
        ).update(status=Deposit.Status.FAILED)
        self.message_user(request, f'{updated} manual deposit(s) rejected.')


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'entry_type', 'usdt_delta', 'ball_delta', 'ref', 'tx_hash')
    list_filter = ('entry_type',)
    search_fields = ('user__username', 'user__email', 'ref', 'tx_hash')
    readonly_fields = [f.name for f in LedgerEntry._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    list_display = ('draw_date', 'status', 'total_tickets', 'jackpot_usdt', 'winner', 'drawn_at')
    list_filter = ('status',)
    readonly_fields = (
        'server_seed_hash', 'server_seed', 'snapshot_hash', 'beacon_slot',
        'beacon_blockhash', 'winning_number', 'winner', 'jackpot_usdt',
        'total_tickets', 'created_at', 'snapshotted_at', 'drawn_at', 'paid_at',
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TicketSnapshot)
class TicketSnapshotAdmin(admin.ModelAdmin):
    list_display = ('draw', 'user', 'ball_balance', 'ticket_start', 'ticket_end')
    search_fields = ('user__username', 'user__email')

    def has_change_permission(self, request, obj=None):
        return False


class PayoutVerificationForm(django_forms.Form):
    verification_code = django_forms.CharField(
        max_length=16, help_text='The code NowPayments emailed to the payout sub-account.',
    )


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'address', 'amount_usdt', 'status', 'payout_id', 'tx_hash')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email', 'address', 'tx_hash', 'payout_id')
    actions = ['approve_withdrawals', 'reject_withdrawals']

    @admin.action(description='Approve (opens a NowPayments payout batch on the next tick)')
    def approve_withdrawals(self, request, queryset):
        queryset.filter(status=WithdrawalRequest.Status.PENDING).update(status=WithdrawalRequest.Status.APPROVED)

    @admin.action(description='Reject (refunds the internal balance)')
    def reject_withdrawals(self, request, queryset):
        from .services.ledger import reject_withdrawal
        for wr in queryset.exclude(status=WithdrawalRequest.Status.SENT):
            reject_withdrawal(wr)

    def get_urls(self):
        return [
            path(
                '<int:pk>/verify-payout/',
                self.admin_site.admin_view(self.verify_payout_view),
                name='core_withdrawalrequest_verify_payout',
            ),
        ] + super().get_urls()

    def verify_payout_view(self, request, pk):
        from .services import ledger as ledger_service
        from .services import nowpayments

        wr = self.get_object(request, pk)
        if wr is None or not wr.payout_id:
            raise Http404('No pending payout batch for this withdrawal.')

        form = PayoutVerificationForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            try:
                result = nowpayments.verify_payout(wr.payout_id, form.cleaned_data['verification_code'])
                withdrawals = result.get('withdrawals') or [{}]
                tx_hash = withdrawals[0].get('hash', '') or wr.payout_id
                ledger_service.mark_withdrawal_sent(wr, tx_hash)
                self.message_user(request, 'Payout verified -- withdrawal marked as sent.')
                return redirect('admin:core_withdrawalrequest_changelist')
            except Exception as exc:
                self.message_user(request, f'Verification failed: {exc}', level=messages.ERROR)

        return render(request, 'admin/core/withdrawalrequest/verify_payout.html', {
            'form': form, 'withdrawal': wr, 'opts': self.model._meta,
        })


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('ball_price_usdt', 'ticket_threshold', 'jackpot_bps', 'rollover_bps', 'fee_bps', 'min_withdraw_usdt', 'kyc_threshold_usdt', 'manual_deposit_address')

    def has_add_permission(self, request):
        return not Config.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        from .services.config import update_config
        changes = {field: form.cleaned_data[field] for field in form.changed_data}
        update_config(changes, changed_by=request.user)


@admin.register(ConfigChangeLog)
class ConfigChangeLogAdmin(admin.ModelAdmin):
    list_display = ('changed_at', 'field_name', 'old_value', 'new_value', 'changed_by')
    readonly_fields = [f.name for f in ConfigChangeLog._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(JackpotPool)
class JackpotPoolAdmin(admin.ModelAdmin):
    list_display = ('jackpot_usdt', 'rollover_usdt', 'fee_usdt', 'updated_at')

    def has_add_permission(self, request):
        return not JackpotPool.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SelfExclusion)
class SelfExclusionAdmin(admin.ModelAdmin):
    list_display = ('user', 'days', 'starts_at', 'ends_at')
    search_fields = ('user__username', 'user__email')
