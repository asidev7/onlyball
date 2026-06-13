// TronWeb helpers: detection, async injection wait, read-only instance.

import { TRON_HOST, TRONGRID_API_KEY } from "@/lib/constants/config";

export function isTronLinkInstalled(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.tronWeb !== "undefined" &&
    typeof window.tronLink !== "undefined"
  );
}

export function hasInjectedTron(): boolean {
  return typeof window !== "undefined" && typeof window.tronWeb !== "undefined";
}

export function waitForTronWeb(timeoutMs = 3000): Promise<TronWebInstance | null> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") return resolve(null);
    if (window.tronWeb) return resolve(window.tronWeb);
    const interval = setInterval(() => {
      if (window.tronWeb) {
        clearInterval(interval);
        clearTimeout(timer);
        resolve(window.tronWeb);
      }
    }, 100);
    const timer = setTimeout(() => {
      clearInterval(interval);
      resolve(window.tronWeb ?? null);
    }, timeoutMs);
  });
}

let readOnly: TronWebInstance | null = null;

export async function getReadOnlyTronWeb(): Promise<TronWebInstance | null> {
  if (readOnly) return readOnly;
  if (typeof window === "undefined") return null;
  try {
    const mod = await import("tronweb");
    const TronWeb =
      (mod as unknown as { TronWeb?: unknown }).TronWeb ??
      (mod as unknown as { default?: unknown }).default ??
      mod;
    const headers = TRONGRID_API_KEY
      ? { "TRON-PRO-API-KEY": TRONGRID_API_KEY }
      : undefined;
    readOnly = new (TronWeb as new (opts: unknown) => TronWebInstance)({
      fullHost: TRON_HOST,
      headers,
    });
    return readOnly;
  } catch (e) {
    console.error("read-only TronWeb init failed:", e);
    return null;
  }
}

export function detectNetwork(
  tronWeb: TronWebInstance | null | undefined
): "mainnet" | "shasta" | "unknown" {
  const host = tronWeb?.fullNode?.host || "";
  if (host.includes("shasta")) return "shasta";
  if (host.includes("trongrid.io")) return "mainnet";
  return "unknown";
}

export function normalizeAddress(value: unknown): string {
  if (!value) return "";
  const str = String(value);
  if (str.startsWith("41") && typeof window !== "undefined" && window.tronWeb) {
    try {
      return window.tronWeb.address.fromHex(str);
    } catch {
      return str;
    }
  }
  return str;
}
