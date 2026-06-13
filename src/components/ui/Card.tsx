import clsx from "clsx";
import type { ReactNode } from "react";

// On dark sections use the default (#1A1A1A card). Use `light` on white sections.
export default function Card({
  children,
  className,
  light = false,
}: {
  children: ReactNode;
  className?: string;
  light?: boolean;
}) {
  return (
    <div
      className={clsx(
        "rounded-[12px] border p-6",
        light
          ? "border-black/10 bg-white text-[#0D0D0D]"
          : "border-white/10 bg-[#1A1A1A] text-white",
        className
      )}
    >
      {children}
    </div>
  );
}
