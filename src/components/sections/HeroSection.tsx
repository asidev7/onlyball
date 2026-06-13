"use client";

import Link from "next/link";
import { Ticket, BookOpen } from "lucide-react";
import { useWallet } from "@/context/WalletContext";
import JackpotMeter from "@/components/lottery/JackpotMeter";
import CountdownTimer from "@/components/lottery/CountdownTimer";
import Button from "@/components/ui/Button";
import { APP_TAGLINE } from "@/lib/constants/config";

export default function HeroSection() {
  const { lottery } = useWallet();

  return (
    <section className="hero-bg border-b border-white/10">
      <div className="mx-auto flex max-w-5xl flex-col items-center px-4 py-16 text-center sm:px-6 sm:py-24">
        <span className="mb-4 inline-flex items-center gap-2 rounded-[12px] border border-[#E31C25]/40 bg-[#E31C25]/10 px-3 py-1 font-body text-xs font-medium uppercase tracking-widest text-[#FF2D37]">
          Round #{lottery.currentRound} · Live on TRON
        </span>

        <h1 className="font-display text-5xl leading-none text-white sm:text-7xl">
          ONLY<span className="text-[#E31C25]">BALL</span>
        </h1>
        <p className="mt-3 font-head text-lg font-semibold text-white sm:text-2xl">
          {APP_TAGLINE}
        </p>
        <p className="mt-3 max-w-xl font-body text-sm text-[#9ca3af] sm:text-base">
          Pick 6 numbers from 1 to 49. Play in FUDSX. Win every day. The jackpot
          rolls over until someone matches all six.
        </p>

        <div className="mt-10 w-full max-w-lg">
          <JackpotMeter amount={lottery.jackpot} />
        </div>

        <div className="mt-10">
          <p className="mb-4 font-body text-xs uppercase tracking-widest text-[#6B7280]">
            Next draw in
          </p>
          <CountdownTimer />
        </div>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link href="/play">
            <Button size="lg" icon={<Ticket className="h-5 w-5" />}>
              Play now
            </Button>
          </Link>
          <Link href="/how-to-play">
            <Button
              size="lg"
              variant="outline"
              icon={<BookOpen className="h-5 w-5" />}
            >
              How it works
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
