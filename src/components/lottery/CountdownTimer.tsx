"use client";

import { useWallet } from "@/context/WalletContext";
import { useCountdown } from "@/lib/hooks/useCountdown";

function Block({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex flex-col items-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-[12px] border border-white/10 bg-[#1A1A1A] sm:h-24 sm:w-24">
        <span className="font-display text-4xl text-white sm:text-5xl">
          {String(value).padStart(2, "0")}
        </span>
      </div>
      <span className="mt-2 font-body text-xs uppercase tracking-widest text-[#6B7280]">
        {label}
      </span>
    </div>
  );
}

export default function CountdownTimer() {
  const { lottery } = useWallet();
  const { h, m, s } = useCountdown(lottery.nextDrawTime);

  return (
    <div className="flex items-center gap-3 sm:gap-4">
      <Block value={h} label="Hrs" />
      <span className="font-display text-3xl text-[#E31C25]">:</span>
      <Block value={m} label="Mins" />
      <span className="font-display text-3xl text-[#E31C25]">:</span>
      <Block value={s} label="Secs" />
    </div>
  );
}
