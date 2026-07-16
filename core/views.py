from decimal import Decimal
from io import BytesIO

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from . import forms
from .models import (
    Config, Deposit, Draw, JackpotPool, LedgerEntry, SelfExclusion, User,
    WithdrawalRequest,
)
from .services import deposits as deposit_service
from .services import ledger as ledger_service
from .services.schedule import next_draw_at_utc
from .services.tickets import ball_to_tickets
from .tokens import email_verification_token


FAQ = [
    ('Do I need crypto experience to play?', 'No. You can sign up with just an email and buy $BALL with a card-funded USDT deposit, or connect a wallet like Phantom, Trust Wallet, or MetaMask.'),
    ('How do I get tickets?', 'Every 100 $BALL you hold earns one ticket in that night\'s drawing, automatically, with no cap. You don\'t spend your $BALL to enter -- holding it is what counts.'),
    ('When is the drawing?', 'Every night at midnight Eastern Time (America/New_York). The countdown on this page always shows the exact time remaining.'),
    ('How do I know the draw isn\'t rigged?', 'OnlyBall runs no smart contract, so fairness comes from a commit-reveal scheme instead: the server publishes a seed hash before tickets close and reveals the seed only after, combined with a public Solana blockhash nobody could predict in advance -- used only as a randomness source, never for moving funds. See /fair to verify any past drawing yourself.'),
    ('How do I withdraw my winnings?', 'Winners with a USDT-TRC20 payout address set are paid automatically. Without one set, winnings are credited to your OnlyBall balance and you\'ll be emailed to set an address and withdraw.'),
    ('Is there a minimum withdrawal?', 'Yes, see /legal for the current minimum and any KYC thresholds that apply above certain deposit or withdrawal amounts.'),
]


def home(request):
    pool = JackpotPool.get_solo()
    last_draws = Draw.objects.filter(status__in=[Draw.Status.DRAWN, Draw.Status.PAID]).order_by('-draw_date')[:10]
    stats = {
        'players': User.objects.count(),
        'usdt_distributed': LedgerEntry.objects.filter(entry_type=LedgerEntry.EntryType.WIN).aggregate(
            total=Sum('usdt_delta'))['total'] or Decimal('0'),
        'tickets_tonight': sum(ball_to_tickets(u.ball_balance) for u in User.objects.all()),
    }
    context = {
        'jackpot_usdt': pool.total_jackpot_usdt,
        'next_draw_at_utc': next_draw_at_utc().isoformat(),
        'last_draws': last_draws,
        'stats': stats,
        'faq': FAQ,
    }
    return render(request, 'core/home.html', context)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('account')
    if request.method == 'POST':
        form = forms.EmailSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_verification_email(request, user)
            login(request, user)
            messages.success(request, 'Welcome to OnlyBall! Check your email to verify your address.')
            return redirect('account')
    else:
        form = forms.EmailSignupForm()
    return render(request, 'core/auth/signup.html', {'form': form})


def _send_verification_email(request, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    path = reverse('verify_email', kwargs={'uidb64': uidb64, 'token': token})
    verify_url = request.build_absolute_uri(path)
    send_mail(
        subject='Verify your OnlyBall account',
        message=f'Click to verify your email: {verify_url}',
        from_email=None,
        recipient_list=[user.email],
        fail_silently=True,
    )


def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        user.email_verified_at = timezone.now()
        user.save(update_fields=['email_verified_at'])
        messages.success(request, 'Your email has been verified.')
    else:
        messages.error(request, 'That verification link is invalid or has expired.')
    return redirect('account' if request.user.is_authenticated else 'login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('account')
    if request.method == 'POST':
        form = forms.EmailLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return redirect(request.GET.get('next') or 'account')
            messages.error(request, 'Invalid email or password.')
    else:
        form = forms.EmailLoginForm()
    return render(request, 'core/auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def account_view(request):
    user = request.user
    tickets = ball_to_tickets(user.ball_balance)
    total_tickets_tonight = sum(ball_to_tickets(u.ball_balance) for u in User.objects.all())
    odds = f'{tickets} in {total_tickets_tonight}' if total_tickets_tonight else 'no tickets sold yet'
    context = {
        'usdt_balance': user.usdt_balance,
        'ball_balance': user.ball_balance,
        'tickets_tonight': tickets,
        'odds': odds,
        'ledger_entries': user.ledger_entries.all()[:50],
        'wallets': user.wallets.all(),
        'withdrawals': user.withdrawal_requests.all()[:20],
        'self_exclusion_form': forms.SelfExclusionForm(),
        'deposit_cap_form': forms.DepositCapForm(initial={'weekly_deposit_cap_usdt': user.weekly_deposit_cap_usdt}),
        'payout_address_form': forms.PayoutAddressForm(
            initial={'usdt_trc20_payout_address': user.usdt_trc20_payout_address},
        ),
    }
    return render(request, 'core/account.html', context)


@login_required
def set_payout_address_view(request):
    if request.method == 'POST':
        form = forms.PayoutAddressForm(request.POST)
        if form.is_valid():
            request.user.usdt_trc20_payout_address = form.cleaned_data['usdt_trc20_payout_address']
            request.user.save(update_fields=['usdt_trc20_payout_address'])
            messages.success(request, 'Your payout address has been updated.')
        else:
            messages.error(request, 'Enter a valid USDT-TRC20 (Tron) address.')
    return redirect('account')


_OPEN_DEPOSIT_STATUSES = ['waiting', 'confirming', 'confirmed', 'sending', 'partially_paid', 'pending_review']


@login_required
def deposit_view(request):
    config = Config.get_solo()
    open_deposit = request.user.deposits.filter(status__in=_OPEN_DEPOSIT_STATUSES).first()
    form = forms.DepositForm()
    manual_form = forms.ManualDepositForm()

    if request.method == 'POST' and not open_deposit:
        if request.POST.get('method') == 'manual':
            manual_form = forms.ManualDepositForm(request.POST)
            if manual_form.is_valid():
                tx_hash = manual_form.cleaned_data['tx_hash']
                duplicate = Deposit.objects.filter(
                    method=Deposit.Method.MANUAL, tx_hash=tx_hash,
                ).exclude(status=Deposit.Status.FAILED).exists()
                if duplicate:
                    manual_form.add_error('tx_hash', 'This transaction hash was already submitted.')
                else:
                    open_deposit = deposit_service.create_manual_deposit(
                        request.user, manual_form.cleaned_data['usdt_amount'], tx_hash,
                        config.manual_deposit_address,
                    )
                    messages.success(request, 'Thanks — your manual deposit is now pending admin review.')
        else:
            form = forms.DepositForm(request.POST)
            if form.is_valid():
                callback_url = request.build_absolute_uri(reverse('api_nowpayments_webhook'))
                try:
                    open_deposit = deposit_service.create_deposit(
                        request.user, form.cleaned_data['usdt_amount'], callback_url,
                    )
                except Exception:
                    messages.error(request, 'Could not start the deposit right now. Please try again shortly.')

    qr_svg = None
    if open_deposit and open_deposit.pay_address:
        img = qrcode.make(open_deposit.pay_address, image_factory=qrcode.image.svg.SvgImage)
        buf = BytesIO()
        img.save(buf)
        qr_svg = buf.getvalue().decode('utf-8')

    manual_qr_svg = None
    if config.manual_deposit_address:
        img = qrcode.make(config.manual_deposit_address, image_factory=qrcode.image.svg.SvgImage)
        buf = BytesIO()
        img.save(buf)
        manual_qr_svg = buf.getvalue().decode('utf-8')

    weekly_deposits = ledger_service.weekly_deposits_usdt(request.user)
    context = {
        'form': form,
        'manual_form': manual_form,
        'open_deposit': open_deposit,
        'qr_svg': qr_svg,
        'manual_qr_svg': manual_qr_svg,
        'manual_deposit_address': config.manual_deposit_address,
        'weekly_deposits': weekly_deposits,
        'over_weekly_cap': bool(
            request.user.weekly_deposit_cap_usdt and weekly_deposits >= request.user.weekly_deposit_cap_usdt
        ),
    }
    return render(request, 'core/deposit.html', context)


@login_required
def buy_view(request):
    config = Config.get_solo()
    if request.method == 'POST':
        form = forms.BuyBallForm(request.POST)
        if form.is_valid():
            try:
                ledger_service.buy_ball(request.user, form.cleaned_data['usdt_amount'])
                messages.success(request, 'Purchase complete.')
                return redirect('account')
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = forms.BuyBallForm()
    context = {
        'form': form,
        'ball_price_usdt': config.ball_price_usdt,
        'ticket_threshold': config.ticket_threshold,
        'usdt_balance': request.user.usdt_balance,
    }
    return render(request, 'core/buy.html', context)


@login_required
def withdraw_view(request):
    config = Config.get_solo()
    if request.method == 'POST':
        form = forms.WithdrawalForm(request.POST)
        if form.is_valid():
            try:
                wr = ledger_service.request_withdrawal(
                    request.user, form.cleaned_data['address'], form.cleaned_data['amount_usdt'],
                )
                if wr.status == WithdrawalRequest.Status.KYC_REQUIRED:
                    messages.warning(request, 'Withdrawal received -- KYC verification is required before it can be sent.')
                else:
                    messages.success(request, 'Withdrawal request submitted.')
                return redirect('account')
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = forms.WithdrawalForm()
    context = {
        'form': form,
        'usdt_balance': request.user.usdt_balance,
        'min_withdraw_usdt': config.min_withdraw_usdt,
    }
    return render(request, 'core/withdraw.html', context)


def draws_list_view(request):
    draws = Draw.objects.exclude(status=Draw.Status.COMMITTED).order_by('-draw_date')[:100]
    return render(request, 'core/draws.html', {'draws': draws})


def draw_detail_view(request, pk):
    draw = get_object_or_404(Draw, pk=pk)
    revealed = draw.status in (Draw.Status.DRAWN, Draw.Status.PAID)
    return render(request, 'core/draw_detail.html', {'draw': draw, 'revealed': revealed})


def fair_view(request):
    recent_draws = Draw.objects.filter(status__in=[Draw.Status.DRAWN, Draw.Status.PAID]).order_by('-draw_date')[:5]
    return render(request, 'core/fair.html', {'recent_draws': recent_draws})


def legal_view(request):
    config = Config.get_solo()
    return render(request, 'core/legal.html', {'config': config})


@login_required
def self_exclude_view(request):
    if request.method == 'POST':
        form = forms.SelfExclusionForm(request.POST)
        if form.is_valid():
            days = form.cleaned_data['days']
            ends_at = timezone.now() + timezone.timedelta(days=days)
            SelfExclusion.objects.create(user=request.user, days=days, ends_at=ends_at)
            request.user.self_excluded_until = ends_at
            request.user.save(update_fields=['self_excluded_until'])
            logout(request)
            messages.success(request, f'You have been self-excluded until {ends_at:%Y-%m-%d}.')
            return redirect('home')
    return redirect('account')


@login_required
def set_deposit_cap_view(request):
    if request.method == 'POST':
        form = forms.DepositCapForm(request.POST)
        if form.is_valid():
            request.user.weekly_deposit_cap_usdt = form.cleaned_data['weekly_deposit_cap_usdt'] or None
            request.user.save(update_fields=['weekly_deposit_cap_usdt'])
            messages.success(request, 'Your weekly deposit cap has been updated.')
    return redirect('account')


def blocked_view(request):
    return render(request, 'core/blocked.html', {'country': getattr(request, 'geo_country', None)})
