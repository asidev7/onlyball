// Wallet adapters: TronLink, TrustWallet (WalletConnect), and generic
// injected providers (TokenPocket / BitKeep). Each returns the TRON base58
// address once connected.

import { waitForTronWeb, isTronLinkInstalled } from "@/lib/tron/tronweb";
import { WALLETCONNECT_PROJECT_ID } from "@/lib/constants/config";

export type WalletType = "tronlink" | "trustwallet" | "tokenpocket" | "bitkeep";

export interface WalletOption {
  type: WalletType;
  name: string;
  description: string;
  installUrl: string;
}

export const WALLET_OPTIONS: WalletOption[] = [
  {
    type: "tronlink",
    name: "TronLink",
    description: "Browser extension",
    installUrl: "https://www.tronlink.org/",
  },
  {
    type: "trustwallet",
    name: "Trust Wallet",
    description: "Mobile · WalletConnect",
    installUrl: "https://trustwallet.com/",
  },
  {
    type: "tokenpocket",
    name: "TokenPocket",
    description: "Multi-chain",
    installUrl: "https://www.tokenpocket.pro/",
  },
  {
    type: "bitkeep",
    name: "Bitget Wallet",
    description: "Multi-chain",
    installUrl: "https://web3.bitget.com/",
  },
];

/** Connect via TronLink (or any injected window.tronLink provider). */
export async function connectTronLink(): Promise<string> {
  if (!isTronLinkInstalled()) {
    throw new Error("TronLink is not installed.");
  }
  await window.tronLink!.request({ method: "tron_requestAccounts" });
  const web = await waitForTronWeb();
  const addr = web?.defaultAddress?.base58;
  if (!addr) throw new Error("Wallet locked or no address available.");
  return addr as string;
}

/** Generic injected TRON provider (TokenPocket, BitKeep, in-app browsers). */
export async function connectInjected(): Promise<string> {
  const web = await waitForTronWeb();
  const addr = web?.defaultAddress?.base58;
  if (web && addr) return addr as string;
  // Some wallets expose request similarly to TronLink.
  if (window.tronLink) return connectTronLink();
  throw new Error("No injected TRON wallet detected.");
}

/**
 * Trust Wallet connects to TRON through WalletConnect v2 (Reown).
 * This requires a project id. Without one we surface a clear message so the
 * UI can fall back to the QR/instructions or another wallet.
 */
export async function connectTrustWallet(): Promise<string> {
  if (!WALLETCONNECT_PROJECT_ID) {
    throw new Error(
      "WalletConnect is not configured. Set NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID, or open OnlyBall inside the Trust Wallet browser to use the injected provider."
    );
  }
  // If Trust Wallet's in-app browser injected a TRON provider, use it directly.
  if (typeof window !== "undefined" && window.tronWeb) {
    return connectInjected();
  }
  throw new Error(
    "Open OnlyBall in the Trust Wallet in-app browser to connect, or use TronLink on desktop."
  );
}

export async function connectWallet(type: WalletType): Promise<string> {
  switch (type) {
    case "tronlink":
      return connectTronLink();
    case "trustwallet":
      return connectTrustWallet();
    case "tokenpocket":
    case "bitkeep":
      return connectInjected();
    default:
      return connectInjected();
  }
}
