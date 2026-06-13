// Affiliate helpers: referral links + capturing inbound ?ref= codes.

import { APP_URL } from "@/lib/constants/config";

const REF_KEY = "onlyball_ref";

export function getReferralLink(code: string): string {
  return `${APP_URL}/?ref=${code}`;
}

/** Read ?ref=CODE from the URL and persist it. Call once on app mount. */
export function captureReferralFromUrl(): void {
  if (typeof window === "undefined") return;
  const params = new URLSearchParams(window.location.search);
  const ref = params.get("ref");
  if (ref && /^[A-Za-z0-9]{4,16}$/.test(ref)) {
    localStorage.setItem(REF_KEY, ref.toUpperCase());
  }
}

export function getStoredReferral(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(REF_KEY) || "";
}

export function clearStoredReferral(): void {
  if (typeof window !== "undefined") localStorage.removeItem(REF_KEY);
}

/** Derive an 8-char code from a TRON address (mirrors the contract logic). */
export function deriveCodeFromAddress(address: string): string {
  let hash = 0;
  for (let i = 0; i < address.length; i++) {
    hash = (hash * 31 + address.charCodeAt(i)) >>> 0;
  }
  return hash.toString(16).toUpperCase().padStart(8, "0").slice(0, 8);
}
