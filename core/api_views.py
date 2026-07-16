import json
import logging
from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .models import Config, Deposit, Draw, JackpotPool, User, WalletLink
from .services import deposits as deposit_service
from .services import nowpayments, wallet_auth
from .services.schedule import current_draw_date, next_draw_at_utc
from .services.tickets import ball_to_tickets

logger = logging.getLogger(__name__)


def _decimal(value) -> str:
    return str(value) if isinstance(value, Decimal) else value


@require_GET
def next_draw(request):
    pool = JackpotPool.get_solo()
    draw = Draw.objects.filter(draw_date=current_draw_date()).first()
    total_tickets = sum(ball_to_tickets(u.ball_balance) for u in User.objects.all())
    return JsonResponse({
        'scheduled_at_utc': next_draw_at_utc().isoformat(),
        'jackpot_usdt': str(pool.total_jackpot_usdt),
        'total_tickets': total_tickets,
        'server_seed_hash': draw.server_seed_hash if draw else None,
    })


@require_GET
def me_tickets(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Authentication required.'}, status=401)
    user = request.user
    config = Config.get_solo()
    return JsonResponse({
        'ball_balance': str(user.ball_balance),
        'tickets': ball_to_tickets(user.ball_balance),
        'ticket_threshold': config.ticket_threshold,
    })


@require_POST
@csrf_protect
def wallet_nonce(request):
    try:
        payload = json.loads(request.body)
        address = payload['address']
        provider = payload.get('provider', WalletLink.Provider.PHANTOM)
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'detail': 'address is required.'}, status=400)

    owner_id = request.user.id if request.user.is_authenticated else _placeholder_user_id()
    wallet, _ = WalletLink.objects.get_or_create(
        address=address,
        defaults={'provider': provider, 'user_id': owner_id},
    )
    if wallet.verified_at is not None and request.user.is_authenticated and wallet.user_id != request.user.id:
        return JsonResponse({'detail': 'This wallet is already linked to another account.'}, status=409)

    wallet.provider = provider
    nonce = wallet.generate_nonce()
    return JsonResponse({'message': wallet_auth.nonce_message(nonce)})


def _placeholder_user_id():
    """WalletLink.user is NOT NULL; for a brand-new address we need a row
    to hang the nonce off of before the signature is verified. We create a
    fresh, unusable User immediately and either keep it (new wallet-only
    account) or discard it in favor of request.user once verify succeeds.
    """
    user = User.objects.create_user(username=f'wallet-pending-{timezone.now().timestamp()}')
    user.set_unusable_password()
    user.save()
    return user.id


@require_POST
@csrf_protect
def wallet_verify(request):
    try:
        payload = json.loads(request.body)
        address = payload['address']
        signature = payload['signature']
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'detail': 'address and signature are required.'}, status=400)

    wallet = get_object_or_404(WalletLink, address=address)
    if not wallet_auth.is_nonce_fresh(wallet):
        return JsonResponse({'detail': 'Nonce expired, request a new one.'}, status=400)

    message = wallet_auth.nonce_message(wallet.nonce)
    if not wallet_auth.verify_wallet_signature(wallet.provider, address, message, signature):
        return JsonResponse({'detail': 'Signature verification failed.'}, status=401)

    wallet.verified_at = timezone.now()

    if request.user.is_authenticated:
        # Linking a wallet to an already-logged-in (e.g. email) account:
        # drop the throwaway placeholder user and attach to request.user.
        placeholder = wallet.user
        wallet.user = request.user
        wallet.save(update_fields=['verified_at', 'user', 'provider'])
        if placeholder.pk != request.user.pk and not placeholder.wallets.exists():
            placeholder.delete()
        target_user = request.user
    else:
        wallet.save(update_fields=['verified_at', 'provider'])
        target_user = wallet.user
        login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')

    return JsonResponse({'ok': True, 'redirect': '/account/'})


@require_GET
def draw_detail(request, pk):
    draw = get_object_or_404(Draw, pk=pk)
    revealed = draw.status in (Draw.Status.DRAWN, Draw.Status.PAID)
    data = {
        'draw_date': draw.draw_date.isoformat(),
        'status': draw.status,
        'server_seed_hash': draw.server_seed_hash,
        'snapshot_hash': draw.snapshot_hash,
        'total_tickets': draw.total_tickets,
        'jackpot_usdt': str(draw.jackpot_usdt),
    }
    if revealed:
        data.update({
            'server_seed': draw.server_seed,
            'beacon_slot': draw.beacon_slot,
            'beacon_blockhash': draw.beacon_blockhash,
            'winning_number': draw.winning_number,
            'winner': draw.winner.username if draw.winner else None,
            'payout_tx': draw.payout_tx,
            'snapshot': [
                {'user_id': s.user_id, 'ticket_start': s.ticket_start, 'ticket_end': s.ticket_end}
                for s in draw.snapshots.order_by('ticket_start')
            ],
        })
    return JsonResponse(data)


@require_GET
@login_required
def deposit_status(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk, user=request.user)
    return JsonResponse({
        'status': deposit.status,
        'pay_address': deposit.pay_address,
        'pay_amount': str(deposit.pay_amount) if deposit.pay_amount is not None else None,
        'price_amount': str(deposit.price_amount),
    })


@csrf_exempt
@require_POST
def nowpayments_webhook(request):
    """NowPayments IPN callback: verifies the x-nowpayments-sig header
    before trusting the payload, then applies the status update. See
    services.nowpayments.verify_ipn_signature and services.deposits.
    apply_payment_update for the actual logic.
    """
    signature = request.headers.get('x-nowpayments-sig', '')
    if not nowpayments.verify_ipn_signature(request.body, signature):
        return HttpResponse(status=401)

    payload = json.loads(request.body)
    order_id = str(payload.get('order_id', ''))
    deposit = Deposit.objects.filter(order_id=order_id).first()
    if deposit is None:
        logger.warning('NowPayments IPN for unknown order_id %s', order_id)
        return HttpResponse(status=404)

    deposit_service.apply_payment_update(deposit, payload)
    return HttpResponse(status=200)
