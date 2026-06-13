"use client";

import { useWallet } from "@/context/WalletContext";
import { shortenAddress } from "@/lib/tron/formatters";

export default function WalletBadge() {
  const { address, fudsxBalance } = useWallet();
  if (!address) return null;

  return (
    <div className="flex items-center gap-2 rounded-[12px] border border-white/15 bg-[#1A1A1A] px-3 py-1.5">
      <span className="h-2 w-2 rounded-full bg-[#22C55E]" />
      <span className="hidden font-body text-xs text-white/90 sm:inline">
        {shortenAddress(address)}
      </span>
      <span className="font-display text-sm text-[#FFD700]">
        {fudsxBalance}
        <span className="ml-1 font-body text-[10px] text-[#6B7280]">FUDSX</span>
      </span>
    </div>
  );
}
