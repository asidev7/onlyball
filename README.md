# OnlyBall

A daily provably-fair USDT lottery. Users hold **$BALL** (an internal accounting
balance, not an onchain token); every 100 $BALL earns one ticket in that
night's drawing at midnight America/New_York. No smart contract is deployed —
fairness comes from a commit-reveal scheme combined with an unpredictable
public Solana blockhash (used purely as a randomness beacon). USDT deposits,
withdrawals, and jackpot payouts are all USDT-**TRC20** (Tron network),
processed through the [NowPayments](https://nowpayments.io) API — no funds
ever move on Solana.

See [`PROMPT.md`](PROMPT.md) for the full product specification this repo
implements.

## Stack

- Django 5 / Python 3.12+, PostgreSQL (SQLite fallback for local dev)
- Tailwind CSS + Alpine.js, both via CDN (no frontend build step)
- Celery + Redis for the deposit/payout polling fallbacks and the nightly draw pipeline
- [NowPayments](https://nowpayments.io) API (via `requests`) for USDT-TRC20 deposits, withdrawals, and jackpot payouts
- `solana-py` / `solders` for a single read-only RPC call: the draw-night randomness beacon (`core/services/beacon.py`) — no funds, no keys

## Quickstart (local dev, SQLite, no Celery/Redis needed)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set SECRET_KEY, and MASTER_WALLET_MNEMONIC to any placeholder
# string for devnet testing (see "Devnet / testnet mode" below)

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data      # optional: populate "Last winners" etc.
python manage.py runserver
```

Visit `http://localhost:8000/`. Django admin is at `/admin/`.

## Running the background workers

The nightly draw pipeline and the NowPayments polling fallbacks run as Celery
tasks. You need Redis running (`REDIS_URL` in `.env`, defaults to
`redis://localhost:6379/0`):

```bash
celery -A onlyball worker -l info
celery -A onlyball beat -l info
```

Beat fires `poll_pending_deposits` and `process_approved_withdrawals` every
60s (fallbacks around the NowPayments API -- deposits are actually credited
by the IPN webhook at `/api/webhooks/nowpayments/`, not by polling), and
fires `snapshot_tickets` / `run_draw` / `commit_next_seed` every minute; each
of the latter three checks the actual America/New_York wall-clock time
itself (via `zoneinfo`, so DST transitions are handled automatically) and is
a no-op outside its one-minute-per-day window. See `core/tasks.py` and
`core/services/schedule.py`.

## The provably-fair drawing, end to end

1. **Commit** (00:01 ET) — `core.services.fairness.commit_draw()` generates a
   32-byte `server_seed` and publishes only `server_seed_hash = SHA-256(server_seed)`.
2. **Snapshot** (23:50 ET) — `snapshot_tickets()` freezes every user's ticket
   range (ordered by user id) and publishes `snapshot_hash`.
3. **Beacon** (00:00 ET) — the latest finalized Solana blockhash is fetched;
   nobody could have known it before the snapshot closed.
4. **Draw** — `winning_number = HMAC_SHA256(key=server_seed, msg=snapshot_hash + beacon) mod total_tickets`.
5. **Reveal** — the seed, beacon, snapshot and winning number are published
   immediately on `/draws/<id>/`, `/api/draws/<id>/`, and are recomputable on
   `/fair` (in-browser, via `SubtleCrypto`) or offline with
   `static/verify_draw.py <draw_id> --base-url https://your-site`.

All of this is unit-tested with fixed vectors in `core/tests/test_fairness.py`
— if the byte layout of the HMAC input ever changes, every previously
published drawing becomes unverifiable, so that test is a hard regression gate.

## Sandbox mode (NowPayments) / devnet beacon

For local development, point at NowPayments' sandbox environment instead of
production:

```
NOWPAYMENTS_BASE_URL=https://api-sandbox.nowpayments.io/v1
NOWPAYMENTS_API_KEY=<sandbox key from https://account.nowpayments.io>
NOWPAYMENTS_IPN_SECRET=<sandbox IPN secret>
```

- To exercise the IPN webhook locally, expose your dev server with a tunnel
  (e.g. `ngrok http 8000`) and use that public URL when building
  `ipn_callback_url` (see `deposit_view` in `core/views.py`, which builds it
  from the incoming request).
- No real funds are needed to exercise the UI: use `manage.py shell` to call
  `core.services.ledger.credit_deposit(user, Decimal('10'), 'fake-tx')`
  directly instead of completing a real sandbox payment.
- Payouts (`services.nowpayments.create_payout`/`verify_payout`) require a
  NowPayments payout sub-account (`NOWPAYMENTS_PAYOUT_EMAIL`/
  `NOWPAYMENTS_PAYOUT_PASSWORD`) with payouts enabled -- see the "Legal
  checklist" below.
- `.env.example` still points `SOLANA_RPC_URL` at Solana **devnet** — this is
  only for the draw-night randomness beacon (`core/services/beacon.py`), not
  payments. If that RPC is unreachable the code falls back to a
  locally-generated, clearly-marked non-onchain beacon so the drawing can
  still complete (see `get_finalized_blockhash_after`).

`python manage.py seed_demo_data` backdates 10 days of fully-drawn, fully
verifiable demo drawings (with a synthetic, offline beacon) so the homepage's
"Last winners" table and stats aren't empty on a fresh install.

## Known limitations / before you touch real funds

- **NowPayments payouts require a manual 2FA confirmation step.**
  `services.nowpayments.create_payout` only opens a payout batch; NowPayments
  emails a verification code to the payout sub-account that an admin must
  enter via the "Verify & send" action on `WithdrawalRequest` (and the
  equivalent step for jackpot payouts) before funds actually move — see
  `core/admin.py`. This is not automated end-to-end.
- **WalletConnect v2** (for mobile Trust Wallet / MetaMask without a browser
  extension) is not wired up — it needs a project ID from
  `cloud.walletconnect.com` plus the relay/QR SDK. The connect-wallet modal
  (used only for account sign-in, not for payouts — see below) currently
  talks to each wallet's injected browser-extension provider
  (`window.solana`, `window.ethereum`), which is fully functional for
  desktop Phantom / Trust Wallet / MetaMask today.
- **Wallet-connect is sign-in only, not a payout destination.** Jackpot
  payouts and withdrawals go to `User.usdt_trc20_payout_address`, a
  user-submitted Tron address (format-validated, not signature-verified) —
  distinct from the Solana/EVM wallet-connect login flow.
- **Geo-blocking** is IP/header based (Cloudflare `CF-IPCountry`, or a
  `GEOIP_PATH` MaxMind database if configured) and is a compliance signal,
  not a security boundary — a determined user can route around it.

## Legal checklist before mainnet

This is a reference implementation, not a licensed product. Before accepting
real money:

- [ ] Obtain a valid gaming/lottery license in every jurisdiction you intend
      to operate in, and have counsel review `/legal` and your actual terms
      of service.
- [ ] Confirm `BLOCKED_COUNTRIES` reflects every jurisdiction where this
      activity is restricted or unlicensed (the default only blocks `US`).
- [ ] Move `NOWPAYMENTS_API_KEY` / `NOWPAYMENTS_IPN_SECRET` /
      `NOWPAYMENTS_PAYOUT_EMAIL` / `NOWPAYMENTS_PAYOUT_PASSWORD` into a
      proper secrets manager — never a plain `.env` file — and switch
      `NOWPAYMENTS_BASE_URL` from sandbox to production.
- [ ] Set real `JACKPOT_BPS` / `ROLLOVER_BPS` / `FEE_BPS` / `KYC_THRESHOLD_USDT`
      / `MIN_WITHDRAW` values via the admin (`Config`), and confirm
      `ConfigChangeLog` is being reviewed as an audit trail.
- [ ] Wire KYC verification to a real identity provider — `User.kyc_status`
      is currently a plain enum with no verification flow attached.
- [ ] Decide whether the manual NowPayments payout 2FA step (see "Known
      limitations") is acceptable at your expected payout volume, or whether
      it needs a more automated confirmation path.
- [ ] Switch `USE_MANIFEST_STATICFILES=True` and run `collectstatic` as part
      of your deploy, put Postgres + Redis behind proper backups/monitoring,
      and set `DEBUG=False` with a real `ALLOWED_HOSTS`.
- [ ] Review responsible-gaming copy and self-exclusion/deposit-cap flows
      against the specific regulator's requirements you're operating under.

## Tests

```bash
python manage.py test core
```

Covers: ledger atomicity/append-only enforcement, ticket-threshold math, the
provably-fair algorithm (fixed HMAC vectors + full commit→snapshot→draw→payout
pipeline), America/New_York scheduling across DST transitions, geo-blocking,
self-exclusion, and the 18+ signup gate.
