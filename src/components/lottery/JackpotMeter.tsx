"use client";

import { useEffect, useState } from "react";
import { Trophy } from "lucide-react";
import { formatNumber } from "@/lib/tron/formatters";
import { FUDSX_PER_USDT } from "@/lib/constants/config";

// Count-up animation on mount / when the amount changes.
function useCountUp(target: number, duration = 1200) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(Math.round(from + (target - from) * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

export default function JackpotMeter({ amount }: { amount: number }) {
  const animated = useCountUp(amount);
  const usdt = Math.round(amount / FUDSX_PER_USDT);

  return (
    <div className="rounded-[12px] border border-[#FFD700]/30 bg-[#1A1A1A] px-6 py-6 text-center sm:px-12">
      <div className="flex items-center justify-center gap-2 font-body text-xs uppercase tracking-widest text-[#FFD700]/80">
        <Trophy className="h-4 w-4" /> Today&apos;s Jackpot
      </div>
      <p className="mt-2 font-display text-6xl leading-none text-[#FFD700] sm:text-8xl">
        {formatNumber(animated)}
      </p>
      <p className="mt-1 font-head text-sm font-medium text-white">
        FUDSX{" "}
        <span className="text-[#6B7280]">
          ≈ {formatNumber(usdt)} USDT
        </span>
      </p>
    </div>
  );
}
