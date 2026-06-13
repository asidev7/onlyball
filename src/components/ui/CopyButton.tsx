"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import clsx from "clsx";

export default function CopyButton({
  value,
  label,
  className,
}: {
  value: string;
  label?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label="Copy"
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-lg px-2 py-1 font-body text-xs transition-colors hover:bg-white/10",
        className
      )}
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-[#22C55E]" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
      {label && <span>{copied ? "Copied" : label}</span>}
    </button>
  );
}
