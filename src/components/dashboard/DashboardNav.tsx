"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { LayoutDashboard, Ticket, Link2, Trophy } from "lucide-react";

const ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/tickets", label: "My tickets", icon: Ticket },
  { href: "/dashboard/affiliate", label: "Affiliate", icon: Link2 },
  { href: "/dashboard/rewards", label: "Rewards", icon: Trophy },
];

export default function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-wrap gap-2">
      {ITEMS.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "inline-flex items-center gap-2 rounded-[12px] border px-4 py-2 font-head text-sm font-semibold transition-colors",
              active
                ? "border-[#E31C25] bg-[#E31C25] text-white"
                : "border-white/10 bg-[#1A1A1A] text-[#9ca3af] hover:border-[#E31C25] hover:text-white"
            )}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
