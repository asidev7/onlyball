"use client";

// Fetch FUDSX holders from the TronGrid API.
import { useEffect, useState } from "react";
import { TRON_HOST, TRONGRID_API_KEY } from "@/lib/constants/config";
import { FUDSX_ADDRESS, FUDSX_DECIMALS } from "@/lib/constants/contract";
import { normalizeAddress } from "@/lib/tron/tronweb";

export interface Holder {
  rank: number;
  address: string;
  balance: number;
  percent: number;
}

export interface HoldersData {
  holders: Holder[];
  totalSupply: number;
  holderCount: number;
  isLoading: boolean;
  error: string | null;
}

export function useHolders(limit = 50): HoldersData {
  const [data, setData] = useState<HoldersData>({
    holders: [],
    totalSupply: 0,
    holderCount: 0,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const url = `${TRON_HOST}/v1/contracts/${FUDSX_ADDRESS}/tokens?limit=${limit}`;
        const headers: Record<string, string> = {};
        if (TRONGRID_API_KEY) headers["TRON-PRO-API-KEY"] = TRONGRID_API_KEY;
        const res = await fetch(url, { headers });
        if (!res.ok) throw new Error(`TronGrid ${res.status}`);
        const json = await res.json();

        const rows: { holder_address?: string; balance?: string }[] =
          json.data || [];
        const div = 10 ** FUDSX_DECIMALS;
        const parsed = rows
          .map((r) => ({
            address: normalizeAddress(r.holder_address || ""),
            balance: Number(r.balance || "0") / div,
          }))
          .filter((r) => r.address && r.balance > 0)
          .sort((a, b) => b.balance - a.balance);

        const total = parsed.reduce((acc, r) => acc + r.balance, 0);
        const holders: Holder[] = parsed.map((r, i) => ({
          rank: i + 1,
          address: r.address,
          balance: r.balance,
          percent: total > 0 ? (r.balance / total) * 100 : 0,
        }));

        if (!cancelled) {
          setData({
            holders,
            totalSupply: total,
            holderCount: holders.length,
            isLoading: false,
            error: null,
          });
        }
      } catch (e) {
        if (!cancelled) {
          setData((d) => ({
            ...d,
            isLoading: false,
            error: e instanceof Error ? e.message : "Failed to load holders.",
          }));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [limit]);

  return data;
}
