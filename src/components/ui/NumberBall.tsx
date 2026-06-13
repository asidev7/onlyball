"use client";

import clsx from "clsx";

type Variant = "default" | "selected" | "winning" | "gold" | "muted";
type Size = "sm" | "md" | "lg";

const sizes: Record<Size, string> = {
  sm: "h-8 w-8 text-base",
  md: "h-12 w-12 text-xl",
  lg: "h-16 w-16 text-3xl",
};

const variants: Record<Variant, string> = {
  default: "bg-[#1A1A1A] text-white border border-white/15",
  selected: "bg-[#E31C25] text-white border border-[#E31C25]",
  winning: "bg-[#E31C25] text-white border border-[#FF2D37]",
  gold: "bg-[#FFD700] text-[#0D0D0D] border border-[#FFD700]",
  muted: "bg-white/5 text-[#6B7280] border border-white/10",
};

export default function NumberBall({
  n,
  variant = "default",
  size = "md",
  onClick,
  disabled,
  className,
}: {
  n: number;
  variant?: Variant;
  size?: Size;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}) {
  const Tag = onClick ? "button" : "span";
  return (
    <Tag
      onClick={onClick}
      disabled={onClick ? disabled : undefined}
      className={clsx(
        "ob-ball font-display leading-none transition-transform",
        sizes[size],
        variants[variant],
        onClick && !disabled && "cursor-pointer hover:scale-110",
        onClick && disabled && "cursor-not-allowed opacity-40",
        className
      )}
    >
      {n}
    </Tag>
  );
}
