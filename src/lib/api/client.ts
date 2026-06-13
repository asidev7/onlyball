// Typed client for the OnlyBall Django API.

import { API_URL } from "@/lib/constants/config";

export interface ApiAccount {
  address: string;
  referral_code: string;
  referred_by: string | null;
  referral_earnings_fudsx: string;
  tickets_count: number;
  referrals_count: number;
  created_at: string;
}

export interface ApiRound {
  index: number;
  status: "open" | "drawn";
  opens_at: string;
  draws_at: string;
  winning_numbers: number[] | null;
  jackpot_fudsx: string;
  tickets_count: number;
}

export interface ApiTicket {
  id: number;
  address: string;
  round_index: number;
  round_status: "open" | "drawn";
  winning_numbers: number[] | null;
  numbers: number[];
  txid: string;
  paid_fudsx: string;
  matched: number;
  is_winner: boolean;
  created_at: string;
}

export interface ApiResult extends ApiRound {
  winners: { address: string; matched: number }[];
}

export interface ApiAffiliate {
  address: string;
  referral_code: string;
  earnings_fudsx: string;
  referrals_count: number;
  referrals: { address: string; tickets: number }[];
}

export interface ApiHolder {
  address: string;
  tickets: number;
  earnings_fudsx: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...init,
  });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.error) message = body.error;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export const api = {
  registerAccount: (address: string, referralCode?: string) =>
    request<ApiAccount>("/accounts/register", {
      method: "POST",
      body: JSON.stringify({ address, referralCode: referralCode || "" }),
    }),

  getAccount: (address: string) =>
    request<ApiAccount>(`/accounts/${address}`),

  currentRound: () => request<ApiRound>("/rounds/current"),

  buyTicket: (payload: {
    address: string;
    numbers: number[];
    txid: string;
    referralCode?: string;
  }) =>
    request<ApiTicket>("/tickets/buy", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  myTickets: (address: string) =>
    request<ApiTicket[]>(`/tickets?address=${encodeURIComponent(address)}`),

  results: () => request<ApiResult[]>("/results"),

  affiliate: (address: string) =>
    request<ApiAffiliate>(`/affiliate/${address}`),

  holders: () => request<ApiHolder[]>("/holders"),
};
