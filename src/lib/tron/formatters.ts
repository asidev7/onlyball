// Formatting helpers: TRC20 amounts, addresses, durations, dates.

import { FUDSX_DECIMALS } from "@/lib/constants/contract";

export function formatUnits(
  raw: bigint | string | number,
  decimals = FUDSX_DECIMALS,
  displayDecimals = 2
): string {
  let bn: bigint;
  try {
    bn = BigInt(raw.toString());
  } catch {
    return "0";
  }
  const divisor = BigInt(10) ** BigInt(decimals);
  const whole = bn / divisor;
  const fraction = bn % divisor;
  const fracStr = fraction
    .toString()
    .padStart(decimals, "0")
    .slice(0, displayDecimals)
    .replace(/0+$/, "");
  const wholeFmt = whole.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return fracStr ? `${wholeFmt}.${fracStr}` : wholeFmt;
}

/** Plain integer-ish number from raw uint256 (for math/comparisons). */
export function toNumber(raw: bigint | string | number, decimals = FUDSX_DECIMALS): number {
  try {
    return Number(BigInt(raw.toString())) / 10 ** decimals;
  } catch {
    return 0;
  }
}

export function parseUnits(amount: string, decimals = FUDSX_DECIMALS): string {
  const cleaned = amount.trim().replace(/,/g, "");
  if (cleaned === "" || isNaN(Number(cleaned))) return "0";
  const [whole, fraction = ""] = cleaned.split(".");
  const fracPadded = (fraction + "0".repeat(decimals)).slice(0, decimals);
  const wholePart = BigInt(whole || "0") * BigInt(10) ** BigInt(decimals);
  return (wholePart + BigInt(fracPadded || "0")).toString();
}

export function shortenAddress(addr?: string | null, chars = 4): string {
  if (!addr) return "—";
  if (addr.length <= chars * 2 + 3) return addr;
  return `${addr.slice(0, chars + 1)}...${addr.slice(-chars)}`;
}

export function isTronAddress(addr: string): boolean {
  return /^T[1-9A-HJ-NP-Za-km-z]{33}$/.test(addr.trim());
}

export function formatDate(timestampMs: number): string {
  return new Date(timestampMs).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatTrx(sun: number): string {
  return (sun / 1_000_000).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/** Compact number e.g. 48500 -> "48,500". */
export function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}
