"""Thin client for the NowPayments API (https://documenter.getpostman.com/view/7907941/S1a32n38)
covering the two things this app needs: taking USDT-TRC20 deposits (via the
Invoice API, which gives back a hosted payment link, + IPN webhook) and
sending USDT-TRC20 payouts (jackpot wins, approved withdrawals).

Unlike the old solana_client, HTTP/API errors are never swallowed here --
callers (Celery tasks, views) decide how to log/retry, since a payment
failure must stay visible.
"""
import hashlib
import hmac
import json
import time

import requests
from django.conf import settings

_jwt_cache = {'token': None, 'expires_at': 0}


def _headers() -> dict:
    return {'x-api-key': settings.NOWPAYMENTS_API_KEY, 'Content-Type': 'application/json'}


def _url(path: str) -> str:
    return f'{settings.NOWPAYMENTS_BASE_URL.rstrip("/")}/{path.lstrip("/")}'


def create_invoice(price_amount, order_id: str, ipn_callback_url: str, price_currency: str = 'usd') -> dict:
    """Creates a NowPayments invoice for `price_amount` (in `price_currency`,
    e.g. USD), fixed to settings.PAY_CURRENCY (USDT-TRC20) so the hosted
    page skips the currency picker. Returns the full API response,
    including `id` (invoice id) and `invoice_url` -- the link the user is
    sent to pay. NowPayments only assigns a `payment_id`/`pay_address` once
    the user actually opens that page and NowPayments creates the
    underlying payment, which is why deposits are looked up by `order_id`
    (known up-front) rather than `payment_id` (see services.deposits).
    """
    resp = requests.post(_url('invoice'), headers=_headers(), json={
        'price_amount': float(price_amount),
        'price_currency': price_currency,
        'pay_currency': settings.PAY_CURRENCY,
        'order_id': order_id,
        'order_description': f'OnlyBall deposit {order_id}',
        'ipn_callback_url': ipn_callback_url,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()


def create_payment(price_amount, order_id: str, ipn_callback_url: str, price_currency: str = 'usd') -> dict:
    """Creates a NowPayments payment directly (rather than an Invoice), so
    `pay_address`/`pay_amount`/`payment_id` come back immediately in the
    response instead of only after the user opens a hosted invoice_url
    page. Used instead of create_invoice so the deposit address and QR
    code can be shown on our own /deposit page right away.
    """
    resp = requests.post(_url('payment'), headers=_headers(), json={
        'price_amount': float(price_amount),
        'price_currency': price_currency,
        'pay_currency': settings.PAY_CURRENCY,
        'order_id': order_id,
        'order_description': f'OnlyBall deposit {order_id}',
        'ipn_callback_url': ipn_callback_url,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_payment_status(payment_id: str) -> dict:
    resp = requests.get(_url(f'payment/{payment_id}'), headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def _canonical_json(data) -> bytes:
    """NowPayments signs the IPN body as JSON with keys sorted
    alphabetically and no extra whitespace -- this must match byte-for-byte
    or the HMAC will never verify.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')


def verify_ipn_signature(raw_body: bytes, signature_header: str) -> bool:
    """Verifies the `x-nowpayments-sig` header: HMAC-SHA512 of the sorted-key
    JSON body, keyed with NOWPAYMENTS_IPN_SECRET.
    """
    if not signature_header:
        return False
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return False
    expected = hmac.new(
        settings.NOWPAYMENTS_IPN_SECRET.encode('utf-8'), _canonical_json(payload), hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _authenticate() -> str:
    """Logs in with the NowPayments payout sub-account (email/password) and
    caches the short-lived JWT in memory. Needed only for /payout calls.
    """
    if _jwt_cache['token'] and _jwt_cache['expires_at'] > time.monotonic():
        return _jwt_cache['token']

    resp = requests.post(_url('auth'), json={
        'email': settings.NOWPAYMENTS_PAYOUT_EMAIL,
        'password': settings.NOWPAYMENTS_PAYOUT_PASSWORD,
    }, timeout=15)
    resp.raise_for_status()
    token = resp.json()['token']
    _jwt_cache['token'] = token
    _jwt_cache['expires_at'] = time.monotonic() + 4 * 60  # NowPayments JWTs are short-lived (~5 min)
    return token


def create_payout(address: str, amount, unique_external_id: str) -> dict:
    """Requests a USDT-TRC20 payout to `address`. NowPayments payouts
    require a follow-up email verification code before they actually send
    (see verify_payout) -- this call only creates the pending batch.
    """
    token = _authenticate()
    resp = requests.post(_url('payout'), headers={
        'Authorization': f'Bearer {token}', 'x-api-key': settings.NOWPAYMENTS_API_KEY,
    }, json={
        'ipn_callback_url': settings.NOWPAYMENTS_PAYOUT_IPN_URL,
        'withdrawals': [{
            'address': address,
            'currency': settings.PAY_CURRENCY,
            'amount': float(amount),
            'unique_external_id': unique_external_id,
        }],
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()


def verify_payout(payout_id: str, verification_code: str) -> dict:
    """Confirms a pending payout batch with the 2FA code NowPayments emails
    to the payout sub-account. Required before funds actually move -- see
    the admin action wired to WithdrawalRequestAdmin.
    """
    token = _authenticate()
    resp = requests.post(_url(f'payout/{payout_id}/verify'), headers={
        'Authorization': f'Bearer {token}', 'x-api-key': settings.NOWPAYMENTS_API_KEY,
    }, json={'verification_code': verification_code}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_payout_status(payout_id: str) -> dict:
    token = _authenticate()
    resp = requests.get(_url(f'payout/{payout_id}'), headers={
        'Authorization': f'Bearer {token}', 'x-api-key': settings.NOWPAYMENTS_API_KEY,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()
