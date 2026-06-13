"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";
import clsx from "clsx";
import Logo from "@/components/layout/Logo";
import WalletButton from "@/components/wallet/WalletButton";
import MobileMenu from "@/components/layout/MobileMenu";

export const NAV_LINKS = [
  { href: "/results", label: "Results" },
  { href: "/how-to-play", label: "How To Play" },
  { href: "/holders", label: "Holders" },
  { href: "/faq", label: "FAQ" },
];

export default function Header() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-[#0D0D0D]">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Logo />

        <div className="hidden items-center gap-6 lg:flex">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={clsx(
                "font-head text-sm transition-colors",
                pathname === l.href
                  ? "font-semibold text-white"
                  : "text-[#9ca3af] hover:text-white"
              )}
            >
              {l.label}
            </Link>
          ))}
          <Link
            href="/buy-fudsx"
            className="rounded-[12px] bg-[#E31C25] px-4 py-2 font-head text-sm font-semibold text-white transition-colors hover:bg-[#9B0E14]"
          >
            Get FUDSX
          </Link>
          <WalletButton />
        </div>

        <button
          className="rounded-lg p-2 text-white lg:hidden"
          onClick={() => setMenuOpen(true)}
          aria-label="Menu"
        >
          <Menu className="h-6 w-6" />
        </button>
      </nav>

      <MobileMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
    </header>
  );
}
