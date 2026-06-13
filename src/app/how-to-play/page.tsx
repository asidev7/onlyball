import type { Metadata } from "next";
import Link from "next/link";
import {
  Wallet,
  Coins,
  Hash,
  Clock,
  Trophy,
  Gift,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
import PageHero from "@/components/layout/PageHero";
import Button from "@/components/ui/Button";
import {
  FUDSX_PER_USDT,
  TICKET_PRICE_FUDSX,
  TICKET_PRICE_USDT,
  NUMBERS_TO_PICK,
  MAX_NUMBER,
  REFERRAL_REWARD_FUDSX,
} from "@/lib/constants/config";

export const metadata: Metadata = {
  title: "How to play",
  description: "Learn how to play OnlyBall: connect a TRON wallet, get FUDSX, pick 6 numbers, and win at the daily midnight UTC draw.",
};

const STEPS: { icon: ReactNode; title: string; body: string }[] = [
  {
    icon: <Wallet className="h-6 w-6" />,
    title: "Connect your wallet",
    body: "Use TronLink (Chrome extension) or Trust Wallet (mobile). Any wallet supporting TRON TRC20 works.",
  },
  {
    icon: <Coins className="h-6 w-6" />,
    title: "Get FUDSX",
    body: `1 USDT = ${FUDSX_PER_USDT} FUDSX — a fixed, guaranteed rate. Minimum to play: ${TICKET_PRICE_FUDSX} FUDSX (= ${TICKET_PRICE_USDT} USDT). FUDSX never loses its reference value.`,
  },
  {
    icon: <Hash className="h-6 w-6" />,
    title: `Pick ${NUMBERS_TO_PICK} numbers`,
    body: `Choose ${NUMBERS_TO_PICK} numbers between 1 and ${MAX_NUMBER}, or use quick pick. One ticket = ${TICKET_PRICE_FUDSX} FUDSX.`,
  },
  {
    icon: <Clock className="h-6 w-6" />,
    title: "Wait for the draw",
    body: "Every night at midnight UTC. The result is recorded on the TRON blockchain and verifiable on TronScan at any time.",
  },
  {
    icon: <Trophy className="h-6 w-6" />,
    title: "See if you won",
    body: "Match 6/6 to take the full jackpot. No winner? The jackpot rolls over to the next round — it grows every day until someone wins.",
  },
  {
    icon: <Gift className="h-6 w-6" />,
    title: "Earn by referring",
    body: `Share your unique link. Earn +${REFERRAL_REWARD_FUDSX} FUDSX for every friend who buys a ticket — paid instantly and automatically by the smart contract.`,
  },
];

export default function HowToPlayPage() {
  return (
    <div className="bg-[#0D0D0D]">
      <PageHero
        title="How to play"
        subtitle="From wallet to jackpot in a few steps — fully on-chain, no sign-up."
      />

      <section className="bg-[#0D0D0D]">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {STEPS.map((s, i) => (
              <div
                key={s.title}
                className="rounded-[12px] border border-white/10 bg-[#1A1A1A] p-6"
              >
                <div className="flex items-center justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-[12px] bg-[#E31C25] text-white">
                    {s.icon}
                  </span>
                  <span className="font-display text-4xl text-white/15">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                </div>
                <h3 className="mt-4 font-head text-base font-semibold text-white">
                  {s.title}
                </h3>
                <p className="mt-1 font-body text-sm text-[#9ca3af]">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why FUDSX never loses value */}
      <section className="border-t border-white/10 bg-white">
        <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-7 w-7 text-[#E31C25]" />
            <h2 className="font-head text-2xl font-semibold text-[#0D0D0D] sm:text-3xl">
              Why FUDSX never loses its value
            </h2>
          </div>
          <ul className="mt-6 space-y-3 font-body text-sm text-[#6B7280]">
            <li>
              • The USDT↔FUDSX reference rate is fixed by the protocol at 1 USDT =
              {" "}
              {FUDSX_PER_USDT} FUDSX.
            </li>
            <li>• Unspent FUDSX stays in your wallet — nothing is lost.</li>
            <li>• Reuse it in the next round, or swap it on SunSwap any time.</li>
          </ul>

          <div className="mt-8">
            <Link href="/play">
              <Button size="lg">Start playing</Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
