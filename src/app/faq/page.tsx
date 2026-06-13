import type { Metadata } from "next";
import PageHero from "@/components/layout/PageHero";

export const metadata: Metadata = {
  title: "FAQ",
  description: "Frequently asked questions about OnlyBall — the daily decentralized lottery on TRON powered by FUDSX.",
};

const FAQ: { q: string; a: string }[] = [
  {
    q: "What is OnlyBall?",
    a: "A daily decentralized lottery on TRON using the FUDSX token.",
  },
  {
    q: "How do I take part?",
    a: "Connect your wallet, get FUDSX (1 USDT = 10 FUDSX), pick 6 numbers — that's it.",
  },
  {
    q: "When does the draw happen?",
    a: "Every day at midnight UTC. The result is published on-chain and visible on TronScan.",
  },
  {
    q: "What happens if nobody wins?",
    a: "The jackpot rolls over to the next round. It keeps growing until a winner appears.",
  },
  {
    q: "Can FUDSX lose value?",
    a: "The reference rate of 1 USDT = 10 FUDSX is guaranteed by the protocol. Your FUDSX stays usable in future rounds.",
  },
  {
    q: "How does the affiliate program work?",
    a: "Each account gets a unique code. When a friend uses it to play, you automatically receive 5 FUDSX in your wallet.",
  },
  {
    q: "Is the draw transparent?",
    a: "Yes. The winning numbers are recorded on-chain on TRON and verifiable on TronScan.",
  },
  {
    q: "Which wallets are supported?",
    a: "TronLink (browser extension), Trust Wallet (mobile), and any TRON TRC20-compatible wallet.",
  },
  {
    q: "Can I play multiple times per round?",
    a: "Yes — buy as many tickets as you like to increase your chances.",
  },
];

export default function FaqPage() {
  return (
    <div className="bg-[#0D0D0D]">
      <PageHero
        title="FAQ"
        subtitle="Everything you need to know before playing OnlyBall."
      />

      <section className="bg-[#0D0D0D]">
        <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
          <div className="space-y-3">
            {FAQ.map((item) => (
              <details
                key={item.q}
                className="group rounded-[12px] border border-white/10 bg-[#1A1A1A] p-5 [&_summary::-webkit-details-marker]:hidden"
              >
                <summary className="flex cursor-pointer items-center justify-between font-head text-base font-semibold text-white">
                  {item.q}
                  <span className="ml-4 font-display text-2xl text-[#E31C25] transition-transform group-open:rotate-45">
                    +
                  </span>
                </summary>
                <p className="mt-3 font-body text-sm text-[#9ca3af]">{item.a}</p>
              </details>
            ))}
          </div>

          <p className="mt-8 text-center font-body text-xs text-[#6B7280]">
            Play responsibly. OnlyBall is for users aged 18+.
          </p>
        </div>
      </section>
    </div>
  );
}
