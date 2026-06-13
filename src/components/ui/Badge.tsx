import clsx from "clsx";
import type { ReactNode } from "react";

type Tone = "red" | "gold" | "green" | "neutral" | "win" | "loss";

const tones: Record<Tone, string> = {
  red: "bg-[#E31C25] text-white border-[#E31C25]",
  gold: "bg-[#FFD700]/15 text-[#FFD700] border-[#FFD700]/40",
  green: "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/40",
  neutral: "bg-white/5 text-[#9ca3af] border-white/15",
  win: "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/40",
  loss: "bg-white/5 text-[#6B7280] border-white/15",
};

export default function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-[12px] border px-2.5 py-1 font-body text-xs font-medium",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
