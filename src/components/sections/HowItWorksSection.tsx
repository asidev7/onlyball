import { Wallet, Coins, Hash, Clock } from "lucide-react";
import type { ReactNode } from "react";

const STEPS: { icon: ReactNode; title: string; body: string }[] = [
  {
    icon: <Wallet className="h-6 w-6" />,
    title: "Connect your wallet",
    body: "Use TronLink, Trust Wallet or any TRON TRC20 wallet.",
  },
  {
    icon: <Coins className="h-6 w-6" />,
    title: "Get FUDSX",
    body: "1 USDT = 10 FUDSX. A ticket costs 200 FUDSX (≈ 20 USDT).",
  },
  {
    icon: <Hash className="h-6 w-6" />,
    title: "Pick 6 numbers",
    body: "Choose 6 numbers from 1 to 49, or use quick pick.",
  },
  {
    icon: <Clock className="h-6 w-6" />,
    title: "Wait for the draw",
    body: "Every midnight UTC, on-chain and verifiable on TronScan.",
  },
];

export default function HowItWorksSection() {
  return (
    <section className="border-b border-white/10 bg-[#0D0D0D]">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <h2 className="text-center font-head text-3xl font-semibold text-white sm:text-4xl">
          How to play
        </h2>
        <p className="mx-auto mt-2 max-w-md text-center font-body text-sm text-[#9ca3af]">
          Four steps from wallet to jackpot — no sign-up, fully on-chain.
        </p>

        <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
                  {i + 1}
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
  );
}
