"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  isTronLinkInstalled,
  hasInjectedTron,
  waitForTronWeb,
  getReadOnlyTronWeb,
  detectNetwork,
} from "@/lib/tron/tronweb";
import { loadFUDSX, loadUSDT, loadOnlyBall } from "@/lib/tron/contract";
import { connectWallet, type WalletType } from "@/lib/tron/walletAdapters";
import { formatUnits, parseUnits } from "@/lib/tron/formatters";
import {
  captureReferralFromUrl,
  getStoredReferral,
} from "@/lib/affiliate/referral";
import {
  FUDSX_DECIMALS,
  USDT_DECIMALS,
  USDT_TRC20,
  FUDSX_ADDRESS,
  TREASURY_ADDRESS,
  ONLYBALL_ADDRESS,
} from "@/lib/constants/contract";
import { TICKET_PRICE_FUDSX } from "@/lib/constants/config";
import { api } from "@/lib/api/client";

type Network = "mainnet" | "shasta" | "unknown";

export interface LotteryStats {
  currentRound: number;
  jackpot: number; // FUDSX
  nextDrawTime: number; // epoch ms (0 = unknown → use midnight UTC)
}

export interface WalletContextType {
  address: string | null;
  walletType: WalletType | null;
  isConnected: boolean;
  isConnecting: boolean;
  isInstalled: boolean;
  network: Network;
  connect: (type: WalletType) => Promise<void>;
  disconnect: () => void;

  fudsxBalance: string;
  usdtBalance: string;
  trxBalance: string;

  lottery: LotteryStats;

  // actions
  buyFUDSX: (usdtAmount: string) => Promise<string>;
  buyTicket: (numbers: number[], referralCode: string) => Promise<string>;

  isLoading: boolean;
  error: string | null;
  txHash: string | null;
  refresh: () => Promise<void>;
}

const WalletCtx = createContext<WalletContextType | undefined>(undefined);
const REFRESH_MS = 15_000;

export function WalletProvider({ children }: { children: ReactNode }) {
  const [address, setAddress] = useState<string | null>(null);
  const [walletType, setWalletType] = useState<WalletType | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [network, setNetwork] = useState<Network>("unknown");

  const [fudsxBalance, setFudsx] = useState("0");
  const [usdtBalance, setUsdt] = useState("0");
  const [trxBalance, setTrx] = useState("0.00");

  const [lottery, setLottery] = useState<LotteryStats>({
    currentRound: 1,
    jackpot: 0,
    nextDrawTime: 0,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [txHash, setTxHash] = useState<string | null>(null);

  const tronWebRef = useRef<TronWebInstance | null>(null);
  const isConnected = Boolean(address);

  useEffect(() => {
    setIsInstalled(isTronLinkInstalled() || hasInjectedTron());
    captureReferralFromUrl();
  }, []);

  const getWeb = useCallback(async (): Promise<TronWebInstance | null> => {
    if (tronWebRef.current) return tronWebRef.current;
    let web: TronWebInstance | null = null;
    if (hasInjectedTron()) web = await waitForTronWeb();
    if (!web || !web.defaultAddress?.base58) web = await getReadOnlyTronWeb();
    tronWebRef.current = web;
    return web;
  }, []);

  // --- Read balances + lottery stats ---
  const refresh = useCallback(async () => {
    try {
      const web = await getWeb();
      if (!web) return;

      // Lottery stats: from the on-chain contract when deployed, else the
      // Django index (jackpot = sum of recorded tickets).
      if (ONLYBALL_ADDRESS) {
        try {
          const ob = await loadOnlyBall(web);
          if (ob) {
            const [round, jackpotRaw, nextRaw] = await Promise.all([
              ob.currentRound().call(),
              ob.jackpotPool().call(),
              ob.nextDrawTime().call(),
            ]);
            setLottery({
              currentRound: Number(round),
              jackpot: Number(formatUnits(String(jackpotRaw), FUDSX_DECIMALS, 2)),
              nextDrawTime: Number(nextRaw) * 1000,
            });
          }
        } catch {
          /* contract read optional */
        }
      } else {
        try {
          const round = await api.currentRound();
          setLottery({
            currentRound: round.index,
            jackpot: Number(round.jackpot_fudsx),
            nextDrawTime: new Date(round.draws_at).getTime(),
          });
        } catch {
          /* API optional on first paint */
        }
      }

      if (address && hasInjectedTron()) {
        try {
          const fudsx = await loadFUDSX(web);
          const fRaw = await fudsx.balanceOf(address).call();
          setFudsx(formatUnits(String(fRaw), FUDSX_DECIMALS, 2));
        } catch {
          /* ignore */
        }
        try {
          const usdt = await loadUSDT(web);
          const uRaw = await usdt.balanceOf(address).call();
          setUsdt(formatUnits(String(uRaw), USDT_DECIMALS, 2));
        } catch {
          /* ignore */
        }
        try {
          const trx = await web.trx.getBalance(address);
          setTrx((Number(trx) / 1_000_000).toFixed(2));
        } catch {
          /* ignore */
        }
      }
    } catch (e) {
      console.error("refresh:", e);
    }
  }, [address, getWeb]);

  const connect = useCallback(
    async (type: WalletType) => {
      setError(null);
      setIsConnecting(true);
      try {
        const addr = await connectWallet(type);
        const web = await waitForTronWeb();
        tronWebRef.current = web;
        setNetwork(detectNetwork(web));
        setWalletType(type);
        setAddress(addr);
        // Register the wallet in the backend (links any captured referral).
        api.registerAccount(addr, getStoredReferral()).catch(() => {});
      } catch (e) {
        setError(extractError(e));
      } finally {
        setIsConnecting(false);
      }
    },
    []
  );

  const disconnect = useCallback(() => {
    setAddress(null);
    setWalletType(null);
    setFudsx("0");
    setUsdt("0");
    setTrx("0.00");
    tronWebRef.current = null;
  }, []);

  // Auto-reconnect if a wallet is already unlocked.
  useEffect(() => {
    (async () => {
      if (!hasInjectedTron()) {
        await refresh();
        return;
      }
      const web = await waitForTronWeb();
      const addr = web?.defaultAddress?.base58;
      if (web && addr) {
        tronWebRef.current = web;
        setNetwork(detectNetwork(web));
        setWalletType("tronlink");
        setAddress(addr as string);
        api.registerAccount(addr as string, getStoredReferral()).catch(() => {});
      } else {
        await refresh();
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(id);
  }, [refresh]);

  // --- Buy FUDSX with USDT (approve + swap) ---
  const buyFUDSX = useCallback(
    async (usdtAmount: string): Promise<string> => {
      setError(null);
      setTxHash(null);
      if (!address) throw fail("Wallet not connected.", setError);
      setIsLoading(true);
      try {
        const web = await getWeb();
        if (!web) throw new Error("Wallet unavailable.");
        const usdtRaw = parseUnits(usdtAmount, USDT_DECIMALS);
        const usdt = await loadUSDT(web);
        const current = await usdt.allowance(address, FUDSX_ADDRESS).call();
        if (BigInt(String(current)) < BigInt(usdtRaw)) {
          await usdt.approve(FUDSX_ADDRESS, usdtRaw).send({ feeLimit: 100_000_000 });
        }
        const fudsx = await loadFUDSX(web);
        // Quote the expected FUDSX out and allow 2% slippage.
        let minOut = "0";
        try {
          const quote = await fudsx.getSwapAmount(USDT_TRC20, usdtRaw).call();
          minOut = ((BigInt(String(quote)) * BigInt(98)) / BigInt(100)).toString();
        } catch {
          /* fall back to no minimum if the quote view is unavailable */
        }
        const hash = await fudsx
          .swap(USDT_TRC20, usdtRaw, minOut)
          .send({ feeLimit: 200_000_000 });
        setTxHash(hash);
        setTimeout(refresh, 4000);
        return hash;
      } catch (e) {
        throw fail(extractError(e), setError);
      } finally {
        setIsLoading(false);
      }
    },
    [address, getWeb, refresh]
  );

  // --- Buy a lottery ticket ---
  // Non-custodial: the player signs the payment themselves. When the OnlyBall
  // contract is deployed the ticket goes through it (approve + buyTicket, fully
  // on-chain); otherwise it is a direct FUDSX transfer to the treasury. Either
  // way the backend verifies the tx and mirrors the ticket for the UI.
  const buyTicket = useCallback(
    async (numbers: number[], referralCode: string): Promise<string> => {
      setError(null);
      setTxHash(null);
      if (!address) throw fail("Wallet not connected.", setError);
      if (numbers.length !== 6)
        throw fail("Pick 6 numbers before buying.", setError);
      setIsLoading(true);
      try {
        const web = await getWeb();
        if (!web) throw new Error("Wallet unavailable.");
        const priceRaw = parseUnits(String(TICKET_PRICE_FUDSX), FUDSX_DECIMALS);
        const fudsx = await loadFUDSX(web);

        // Ensure the player can cover the ticket.
        const balRaw = await fudsx.balanceOf(address).call();
        if (BigInt(String(balRaw)) < BigInt(priceRaw)) {
          throw new Error(
            `Not enough FUDSX. A ticket costs ${TICKET_PRICE_FUDSX} FUDSX — buy some first.`
          );
        }

        const code = referralCode || getStoredReferral();
        let hash: string;

        if (ONLYBALL_ADDRESS) {
          // On-chain lottery: approve the contract, then buy through it.
          const allowance = await fudsx.allowance(address, ONLYBALL_ADDRESS).call();
          if (BigInt(String(allowance)) < BigInt(priceRaw)) {
            await fudsx
              .approve(ONLYBALL_ADDRESS, priceRaw)
              .send({ feeLimit: 100_000_000 });
          }
          const ob = await loadOnlyBall(web);
          if (!ob) throw new Error("OnlyBall contract unavailable.");
          hash = await ob
            .buyTicket(numbers, code)
            .send({ feeLimit: 300_000_000 });
        } else {
          // No contract yet: direct FUDSX transfer to the treasury.
          hash = await fudsx
            .transfer(TREASURY_ADDRESS, priceRaw)
            .send({ feeLimit: 150_000_000 });
        }
        setTxHash(hash);

        // Record + verify on the backend (retries while the tx confirms).
        let recorded = false;
        for (let i = 0; i < 6 && !recorded; i++) {
          try {
            await api.buyTicket({ address, numbers, txid: hash, referralCode: code });
            recorded = true;
          } catch (err) {
            // 409 = already recorded; treat as success.
            if (extractError(err).includes("already")) {
              recorded = true;
              break;
            }
            await new Promise((r) => setTimeout(r, 3000));
          }
        }
        if (!recorded) {
          throw new Error(
            "Payment sent, but confirmation is taking a while. Your ticket will appear once the transaction is confirmed."
          );
        }
        setTimeout(refresh, 2000);
        return hash;
      } catch (e) {
        throw fail(extractError(e), setError);
      } finally {
        setIsLoading(false);
      }
    },
    [address, getWeb, refresh]
  );

  const value: WalletContextType = {
    address,
    walletType,
    isConnected,
    isConnecting,
    isInstalled,
    network,
    connect,
    disconnect,
    fudsxBalance,
    usdtBalance,
    trxBalance,
    lottery,
    buyFUDSX,
    buyTicket,
    isLoading,
    error,
    txHash,
    refresh,
  };

  return <WalletCtx.Provider value={value}>{children}</WalletCtx.Provider>;
}

export function useWallet(): WalletContextType {
  const ctx = useContext(WalletCtx);
  if (!ctx) throw new Error("useWallet must be used within <WalletProvider>.");
  return ctx;
}

// helpers
function fail(msg: string, set: (m: string) => void): Error {
  set(msg);
  return new Error(msg);
}
function extractError(e: unknown): string {
  if (typeof e === "string") return e;
  if (e instanceof Error) return e.message;
  if (e && typeof e === "object" && "message" in e)
    return String((e as { message: unknown }).message);
  return "Something went wrong.";
}
