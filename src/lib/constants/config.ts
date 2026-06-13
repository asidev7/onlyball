// Network + app configuration for OnlyBall.

export type TronNetwork = "mainnet" | "shasta";

export const NETWORK: TronNetwork =
  (process.env.NEXT_PUBLIC_NETWORK as TronNetwork) || "mainnet";

export const TRON_HOST =
  NETWORK === "shasta"
    ? "https://api.shasta.trongrid.io"
    : "https://api.trongrid.io";

export const TRONSCAN_BASE =
  process.env.NEXT_PUBLIC_TRONSCAN_BASE ||
  (NETWORK === "shasta"
    ? "https://shasta.tronscan.org/#"
    : "https://tronscan.org/#");

export const TRONGRID_API_KEY = process.env.NEXT_PUBLIC_TRONGRID_API_KEY || "";

export const WALLETCONNECT_PROJECT_ID =
  process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "";

// Lottery economics (mirrors the OnlyBall contract).
export const FUDSX_PER_USDT = 10; // 1 USDT = 10 FUDSX
export const TICKET_PRICE_FUDSX = 1; // TEMP TEST PRICE — revert to 200 after testing
export const TICKET_PRICE_USDT = 20;
export const NUMBERS_TO_PICK = 6;
export const MAX_NUMBER = 49;
export const REFERRAL_REWARD_FUDSX = 5;

// Django API base URL.
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const APP_NAME = "OnlyBall";
export const APP_TAGLINE = "The Daily TRON Drawing";
export const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://onlyball.io";
