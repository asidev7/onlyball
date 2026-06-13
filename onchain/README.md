# OnlyBall on-chain lottery

`OnlyBall.sol` is a fully on-chain daily 6/49 lottery paid in **FUDSX**:

- `buyTicket(uint8[6] numbers, string referralCode)` — pulls `ticketPrice` FUDSX
  into the contract (needs a prior FUDSX `approve`) and records the ticket.
- `executeDraw()` — **permissionless** once `nextDrawTime` has passed. Picks 6
  numbers from block data, pays every ticket matching all six an equal share of
  the pot, rolls the pot over when nobody wins, then opens the next round.
- Every ticket and draw is an **event** (`TicketPurchased`, `DrawCompleted`,
  `JackpotWon`, `Rollover`) and is stored on-chain — fully traceable on TronScan.

A jackpot win = matching **all 6** numbers (odds ≈ 1 in 13.98 M), so the prize
is real and rolls over until someone hits it.

> ⚠️ Randomness comes from block data and is only *pseudo*-random — a block
> producer could in theory bias a draw. Fine at small scale; move to an oracle
> for large pots. This contract is **unaudited**: test on Shasta first.

## Deploy

1. `cd onchain && npm install`
2. `cp .env.example .env` and fill in:
   - `PRIVATE_KEY_SHASTA` / `PRIVATE_KEY_MAINNET` (deployer = owner; needs TRX)
   - `TICKET_PRICE` (use `1` for a cheap first test), `DRAW_INTERVAL` (`300` = 5 min to test)
3. **Test on Shasta first** (free TRX from the Shasta faucet):
   ```
   npm run deploy:shasta
   ```
4. When validated, deploy for real:
   ```
   npm run deploy:mainnet
   ```
   The command prints the deployed **contract address** (base58, `T...`).
5. Put that address in the frontend: `NEXT_PUBLIC_ONLYBALL_ADDRESS=T...` in
   `onlyball/.env.local`, and in the backend `.env` as `ONLYBALL_ADDRESS=T...`.

## After deploy

- Trigger a draw once the interval elapses: in `npm run console:mainnet`
  ```js
  const c = await OnlyBall.deployed(); await c.executeDraw().send();
  ```
  (or wire a cron to call it — anyone can).
- Read state: `currentRound()`, `jackpotPool()`, `getDraw(round)`, `getTimeUntilDraw()`.
