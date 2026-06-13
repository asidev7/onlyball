"use client";

import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

export default function Modal({
  open,
  onClose,
  title,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-[12px] border border-[#E31C25]/50 bg-[#1A1A1A]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
          <h2 className="font-head text-base font-semibold text-white">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1 text-[#9ca3af] transition-colors hover:bg-white/10"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="px-6 py-5 font-body text-sm text-white">{children}</div>
        {footer && (
          <div className="flex justify-end gap-2 border-t border-white/10 px-6 py-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
