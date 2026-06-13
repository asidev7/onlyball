import clsx from "clsx";
import type { ReactNode } from "react";

export default function StatCard({
  label,
  value,
  unit,
  icon,
  light = false,
  gold = false,
}: {
  label: string;
  value: string;
  unit?: string;
  icon?: ReactNode;
  light?: boolean;
  gold?: boolean;
}) {
  return (
    <div
      className={clsx(
        "rounded-[12px] border p-6",
        light ? "border-black/10 bg-white" : "border-white/10 bg-[#1A1A1A]"
      )}
    >
      <div
        className={clsx(
          "flex items-center gap-2 font-body text-xs uppercase tracking-wide",
          light ? "text-[#6B7280]" : "text-white/50"
        )}
      >
        {icon}
        {label}
      </div>
      <p
        className={clsx(
          "mt-2 font-display text-4xl leading-none",
          gold ? "text-[#FFD700]" : light ? "text-[#0D0D0D]" : "text-white"
        )}
      >
        {value}
        {unit && (
          <span className="ml-2 font-head text-sm font-medium text-[#6B7280]">
            {unit}
          </span>
        )}
      </p>
    </div>
  );
}
