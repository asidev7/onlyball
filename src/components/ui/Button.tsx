"use client";

import clsx from "clsx";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";

type Variant = "primary" | "gold" | "outline" | "ghost" | "dark";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
}

const base =
  "inline-flex items-center justify-center gap-2 rounded-[12px] font-head font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed select-none";

const variants: Record<Variant, string> = {
  primary: "bg-[#E31C25] text-white hover:bg-[#9B0E14]",
  gold: "bg-[#FFD700] text-[#0D0D0D] hover:bg-[#e6c200]",
  outline:
    "border border-white/25 bg-transparent text-white hover:border-[#E31C25] hover:text-[#FF2D37]",
  ghost: "bg-transparent text-white hover:bg-white/10",
  dark: "bg-[#1A1A1A] text-white hover:bg-[#262626] border border-white/10",
};

const sizes: Record<Size, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-5 py-2.5 text-sm",
  lg: "px-7 py-3.5 text-base",
};

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  children,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(base, variants[variant], sizes[size], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}
