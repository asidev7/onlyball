import Link from "next/link";
import Logo from "@/components/layout/Logo";
import TronScanLink from "@/components/ui/TronScanLink";
import { FUDSX_ADDRESS, ONLYBALL_ADDRESS } from "@/lib/constants/contract";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-[#0D0D0D]">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-8 md:flex-row md:justify-between">
          <div className="max-w-xs">
            <Logo />
            <p className="mt-3 font-body text-sm text-[#6B7280]">
              The daily decentralized lottery on TRON, powered by the FUDSX token.
              Transparent, on-chain draws every midnight UTC.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
            <FooterCol
              title="Play"
              links={[
                { href: "/play", label: "Play now" },
                { href: "/results", label: "Results" },
                { href: "/buy-fudsx", label: "Get FUDSX" },
              ]}
            />
            <FooterCol
              title="Learn"
              links={[
                { href: "/how-to-play", label: "How to play" },
                { href: "/faq", label: "FAQ" },
                { href: "/holders", label: "Holders" },
              ]}
            />
            <FooterCol
              title="Account"
              links={[
                { href: "/dashboard", label: "Dashboard" },
                { href: "/dashboard/affiliate", label: "Affiliate" },
                { href: "/dashboard/rewards", label: "Rewards" },
              ]}
            />
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-3 border-t border-white/10 pt-6 text-xs text-[#6B7280] sm:flex-row sm:items-center sm:justify-between">
          <span className="font-body">
            © 2026 OnlyBall — TRON Blockchain · FUDSX · Play responsibly (18+).
          </span>
          <span className="flex items-center gap-4">
            <TronScanLink value={FUDSX_ADDRESS} kind="token" label="FUDSX" />
            {ONLYBALL_ADDRESS && (
              <TronScanLink
                value={ONLYBALL_ADDRESS}
                kind="contract"
                label="Contract"
              />
            )}
          </span>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({
  title,
  links,
}: {
  title: string;
  links: { href: string; label: string }[];
}) {
  return (
    <div>
      <p className="mb-3 font-head text-xs font-semibold uppercase tracking-wide text-white">
        {title}
      </p>
      <ul className="space-y-2">
        {links.map((l) => (
          <li key={l.href}>
            <Link
              href={l.href}
              className="font-body text-sm text-[#6B7280] transition-colors hover:text-white"
            >
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
