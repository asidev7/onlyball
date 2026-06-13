"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { NAV_LINKS } from "@/components/layout/Header";
import WalletButton from "@/components/wallet/WalletButton";

export default function MobileMenu({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  if (!open) return null;

  const links = [
    { href: "/play", label: "Play" },
    ...NAV_LINKS,
    { href: "/buy-fudsx", label: "Get FUDSX" },
    { href: "/dashboard", label: "Dashboard" },
  ];

  return (
    <div className="fixed inset-0 z-50 lg:hidden" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70" />
      <div
        className="absolute right-0 top-0 h-full w-72 border-l border-white/10 bg-[#0D0D0D] p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-8 flex justify-end">
          <button onClick={onClose} aria-label="Close" className="text-white">
            <X className="h-6 w-6" />
          </button>
        </div>
        <div className="flex flex-col gap-4">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={onClose}
              className="font-head text-base text-white transition-colors hover:text-[#FF2D37]"
            >
              {l.label}
            </Link>
          ))}
          <div className="pt-4">
            <WalletButton />
          </div>
        </div>
      </div>
    </div>
  );
}
