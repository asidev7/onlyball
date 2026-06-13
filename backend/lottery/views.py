from decimal import Decimal

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Account, ReferralCredit, Ticket
from .serializers import AccountSerializer, RoundSerializer, TicketSerializer
from .services.rounds import get_or_create_current_round
from .services.tron import TronVerifyError, verify_ticket_payment


def _get_account(address: str) -> Account | None:
    return Account.objects.filter(address=address).first()


def _link_referrer(account: Account, referral_code: str) -> None:
    """Attach a referrer to a fresh account (once, never self)."""
    if not referral_code or account.referred_by_id:
        return
    referrer = Account.objects.filter(referral_code=referral_code).first()
    if referrer and referrer.id != account.id:
        account.referred_by = referrer
        account.save(update_fields=["referred_by"])


@api_view(["POST"])
def register_account(request):
    address = (request.data.get("address") or "").strip()
    if not address:
        return Response({"error": "address is required"}, status=400)
    referral_code = (request.data.get("referralCode") or "").strip()

    account, created = Account.objects.get_or_create(address=address)
    if created:
        _link_referrer(account, referral_code)
    return Response(AccountSerializer(account).data, status=201 if created else 200)


@api_view(["GET"])
def account_detail(request, address):
    account = _get_account(address)
    if not account:
        return Response({"error": "not found"}, status=404)
    return Response(AccountSerializer(account).data)


@api_view(["GET"])
def current_round(request):
    rnd = get_or_create_current_round()
    return Response(RoundSerializer(rnd).data)


@api_view(["GET"])
def results(request):
    from .models import Round

    drawn = Round.objects.filter(status=Round.DRAWN).order_by("-index")[:30]
    data = []
    for rnd in drawn:
        winners = rnd.tickets.filter(is_winner=True).select_related("account")
        data.append(
            {
                **RoundSerializer(rnd).data,
                "winners": [
                    {"address": w.account.address, "matched": w.matched}
                    for w in winners
                ],
            }
        )
    return Response(data)


@api_view(["GET"])
def tickets_list(request):
    address = (request.query_params.get("address") or "").strip()
    qs = Ticket.objects.select_related("account", "round")
    if address:
        qs = qs.filter(account__address=address)
    return Response(TicketSerializer(qs[:100], many=True).data)


@api_view(["POST"])
def buy_ticket(request):
    """Record a ticket after verifying its on-chain FUDSX payment."""
    address = (request.data.get("address") or "").strip()
    numbers = request.data.get("numbers")
    txid = (request.data.get("txid") or "").strip()
    referral_code = (request.data.get("referralCode") or "").strip()

    if not address or not txid:
        return Response({"error": "address and txid are required"}, status=400)
    if not isinstance(numbers, list) or len(numbers) != 6:
        return Response({"error": "numbers must be a list of 6"}, status=400)
    try:
        numbers = sorted({int(n) for n in numbers})
    except (TypeError, ValueError):
        return Response({"error": "numbers must be integers"}, status=400)
    if len(numbers) != 6 or any(n < 1 or n > 49 for n in numbers):
        return Response({"error": "pick 6 distinct numbers from 1-49"}, status=400)

    if Ticket.objects.filter(txid=txid).exists():
        return Response({"error": "this transaction was already used"}, status=409)

    # On-chain verification (non-custodial: the player already paid & signed).
    try:
        payment = verify_ticket_payment(txid, address)
    except TronVerifyError as exc:
        return Response({"error": str(exc)}, status=400)
    except Exception:
        return Response(
            {"error": "Could not reach the TRON network. Try again."}, status=502
        )

    account, created = Account.objects.get_or_create(address=address)
    if created:
        _link_referrer(account, referral_code)

    reward = Decimal(settings.REFERRAL_REWARD_FUDSX)
    paid = Decimal(str(payment["amount_fudsx"]))

    with transaction.atomic():
        rnd = get_or_create_current_round()
        ticket = Ticket.objects.create(
            account=account,
            round=rnd,
            numbers=numbers,
            txid=txid,
            paid_fudsx=paid,
        )
        rnd.jackpot_fudsx = (rnd.jackpot_fudsx or Decimal(0)) + paid
        rnd.save(update_fields=["jackpot_fudsx"])

        # Credit the referrer (off-chain ledger; payout is operator-side).
        if account.referred_by_id:
            referrer = account.referred_by
            ReferralCredit.objects.create(
                referrer=referrer,
                referee=account,
                amount_fudsx=reward,
                txid=txid,
            )
            referrer.referral_earnings_fudsx = (
                referrer.referral_earnings_fudsx or Decimal(0)
            ) + reward
            referrer.save(update_fields=["referral_earnings_fudsx"])

    return Response(TicketSerializer(ticket).data, status=201)


@api_view(["GET"])
def affiliate(request, address):
    account = _get_account(address)
    if not account:
        return Response({"error": "not found"}, status=404)
    referees = account.referrals.all()
    return Response(
        {
            "address": account.address,
            "referral_code": account.referral_code,
            "earnings_fudsx": account.referral_earnings_fudsx,
            "referrals_count": referees.count(),
            "referrals": [
                {"address": r.address, "tickets": r.tickets.count()} for r in referees
            ],
        }
    )


@api_view(["GET"])
def holders(request):
    # Rank by ticket count (most active players).
    from django.db.models import Count

    ranked = (
        Account.objects.annotate(n=Count("tickets"))
        .filter(n__gt=0)
        .order_by("-n")[:50]
    )
    return Response(
        [
            {"address": a.address, "tickets": a.n, "earnings_fudsx": a.referral_earnings_fudsx}
            for a in ranked
        ]
    )
