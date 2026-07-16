"""Draw-night randomness beacon: the finalized Solana blockhash used as the
unpredictable-in-advance input to the provably-fair draw (see
services.fairness.compute_winning_number).

This is a read-only public RPC call -- it needs no wallet, no key, and
touches no funds. It has nothing to do with payments: USDT deposits,
withdrawals and jackpot payouts go through NowPayments
(services.nowpayments), not Solana. Solana is kept here purely as a public
source of unpredictable randomness.

The installed solana-py release only ships an async RPC client
(`solana.rpc.async_api.AsyncClient`); `_run` bridges that into the sync
call sites used by Celery tasks.
"""
import asyncio
from datetime import datetime

from django.conf import settings


def _run(coro):
    return asyncio.run(coro)


def _rpc_client():
    from solana.rpc.async_api import AsyncClient
    return AsyncClient(settings.SOLANA_RPC_URL)


async def _get_finalized_blockhash_async() -> tuple[int, str]:
    client = _rpc_client()
    try:
        resp = await client.get_latest_blockhash()
        return resp.context.slot, str(resp.value.blockhash)
    finally:
        await client.close()


def get_finalized_blockhash_after(after_dt: datetime) -> tuple[int, str]:
    """Draw-night beacon: the blockhash + slot of the latest finalized
    Solana block, fetched at (i.e. just after) `after_dt`. Solana blocks
    finalize in a couple seconds, so calling this right at 00:00:00 ET
    yields a block that could not have been known before the drawing
    opened -- the source of unpredictability the provably-fair scheme
    relies on for step 3 (see services.fairness).
    """
    try:
        return _run(_get_finalized_blockhash_async())
    except Exception:
        # Public RPC unreachable: fall back to a locally-generated beacon so
        # the draw can still complete. This is clearly marked non-onchain
        # in the reveal so anyone verifying can see the beacon source.
        import secrets
        return 0, f'local-fallback-{secrets.token_hex(16)}'
