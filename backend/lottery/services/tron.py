"""On-chain verification of ticket payments via TronGrid.

A ticket purchase is a real FUDSX TRC20 `transfer(treasury, amount)` signed by
the player in their own wallet (non-custodial). The backend never holds keys;
it only *verifies* that a given txid is such a transfer before recording the
ticket. Idempotency is guaranteed by the unique `txid` on Ticket.
"""

from __future__ import annotations

import requests
from django.conf import settings

# TRC20 transfer(address,uint256) selector.
_TRANSFER_SELECTOR = "a9059cbb"
# OnlyBall.buyTicket(uint8[6],string) selector.
_BUYTICKET_SELECTOR = "e2d5aea2"

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58decode(s: str) -> bytes:
    num = 0
    for ch in s:
        num = num * 58 + _B58_ALPHABET.index(ch)
    full = num.to_bytes((num.bit_length() + 7) // 8, "big")
    # restore leading zero bytes (encoded as leading '1's)
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + full


def base58_to_eth_hex(address: str) -> str:
    """Return the 20-byte address body (no 0x, no 41 prefix), lowercase hex.

    A TRON base58 address decodes to 0x41 + 20 bytes + 4-byte checksum.
    The 20-byte body is what appears (left-padded) inside TRC20 call data.
    """
    raw = _b58decode(address)
    body = raw[1:-4]  # drop 0x41 prefix and 4-byte checksum
    return body.hex().lower()


class TronVerifyError(Exception):
    pass


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if settings.TRONGRID_API_KEY:
        h["TRON-PRO-API-KEY"] = settings.TRONGRID_API_KEY
    return h


def _post(path: str, payload: dict) -> dict:
    url = f"{settings.TRON_HOST}{path}"
    resp = requests.post(url, json=payload, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def verify_ticket_payment(txid: str, from_address: str) -> dict:
    """Verify that `txid` is a confirmed FUDSX transfer of >= TICKET_PRICE
    from `from_address` to the treasury.

    Returns {"amount_fudsx": Decimal-friendly float, "to": str} on success.
    Raises TronVerifyError otherwise.
    """
    txid = (txid or "").strip().lower().removeprefix("0x")
    if not txid:
        raise TronVerifyError("Missing transaction id.")

    tx = _post("/wallet/gettransactionbyid", {"value": txid, "visible": True})
    if not tx or "raw_data" not in tx:
        raise TronVerifyError("Transaction not found on-chain yet.")

    ret = tx.get("ret") or [{}]
    if ret[0].get("contractRet") != "SUCCESS":
        raise TronVerifyError(
            f"Transaction did not succeed ({ret[0].get('contractRet', 'unknown')})."
        )

    contracts = tx["raw_data"].get("contract") or []
    if not contracts or contracts[0].get("type") != "TriggerSmartContract":
        raise TronVerifyError("Transaction is not a token transfer.")

    value = contracts[0]["parameter"]["value"]
    owner = value.get("owner_address", "")
    contract_addr = value.get("contract_address", "")
    data = (value.get("data") or "").lower()

    if owner != from_address:
        raise TronVerifyError("Transaction sender does not match the wallet.")

    # Contract mode: a buyTicket() call to the deployed OnlyBall contract. The
    # contract itself enforces the price/numbers, so a confirmed successful call
    # from this wallet is a valid ticket.
    if settings.ONLYBALL_ADDRESS and contract_addr == settings.ONLYBALL_ADDRESS:
        if not data.startswith(_BUYTICKET_SELECTOR):
            raise TronVerifyError("Transaction is not a buyTicket call.")
        info = _post("/wallet/gettransactioninfobyid", {"value": txid})
        if not info or "blockNumber" not in info:
            raise TronVerifyError("Transaction not yet confirmed. Try again shortly.")
        return {"amount_fudsx": float(settings.TICKET_PRICE_FUDSX), "to": settings.ONLYBALL_ADDRESS}

    # Direct-transfer mode (no contract): FUDSX transfer to the treasury.
    if contract_addr != settings.FUDSX_ADDRESS:
        raise TronVerifyError("Transaction does not use the FUDSX contract.")
    if not data.startswith(_TRANSFER_SELECTOR) or len(data) < 8 + 64 + 64:
        raise TronVerifyError("Transaction is not a FUDSX transfer.")

    to_body = data[8 + 24 : 8 + 64]  # last 20 bytes of the first arg
    amount_raw = int(data[8 + 64 : 8 + 128], 16)

    treasury_body = base58_to_eth_hex(settings.TREASURY_ADDRESS)
    if to_body != treasury_body:
        raise TronVerifyError("Transfer was not sent to the lottery treasury.")

    price_raw = settings.TICKET_PRICE_FUDSX * (10 ** settings.FUDSX_DECIMALS)
    if amount_raw < price_raw:
        raise TronVerifyError(
            f"Amount too low: need {settings.TICKET_PRICE_FUDSX} FUDSX."
        )

    # Confirmed in a block?
    info = _post("/wallet/gettransactioninfobyid", {"value": txid})
    if not info or "blockNumber" not in info:
        raise TronVerifyError("Transaction not yet confirmed. Try again shortly.")

    return {
        "amount_fudsx": amount_raw / (10 ** settings.FUDSX_DECIMALS),
        "to": settings.TREASURY_ADDRESS,
    }
