import type { Metadata } from "next";
import PageHero from "@/components/layout/PageHero";
import BuyFUDSXForm from "@/components/buy/BuyFUDSXForm";
import CopyButton from "@/components/ui/CopyButton";
import TronScanLink from "@/components/ui/TronScanLink";
import { USDT_TRC20, FUDSX_ADDRESS } from "@/lib/constants/contract";
import { shortenAddress } from "@/lib/tron/formatters";

export const metadata: Metadata = {
  title: "Buy FUDSX",
  description: "Buy FUDSX with USDT (TRC20) at the fixed rate 1 USDT = 10 FUDSX. Instant on-chain swap on TRON.",
};

const STEPS = [
  "Approve OnlyBall to spend your USDT (TRC20).",
  "Your USDT is transferred to the FUDSX contract.",
  "FUDSX is sent to your wallet instantly at the fixed rate.",
];

export default function BuyFudsxPage() {
  return (
    <div className="bg-[#0D0D0D]">
      <PageHero
        title="Buy FUDSX"
        subtitle="Guaranteed fixed rate: 1 USDT = 10 FUDSX. FUDSX is the token used to play OnlyBall."
      />

      <section className="bg-[#0D0D0D]">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[420px_1fr]">
          <div className="rounded-[12px] border border-white/10 bg-[#1A1A1A] p-6">
            <BuyFUDSXForm />
          </div>

          <div>
            <h2 className="font-head text-xl font-semibold text-white">
              How it works
            </h2>
            <ol className="mt-4 space-y-3">
              {STEPS.map((s, i) => (
                <li key={i} className="flex gap-3">
                  <span className="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-[#E31C25] font-display text-sm text-white">
                    {i + 1}
                  </span>
                  <span className="font-body text-sm text-[#9ca3af]">{s}</span>
                </li>
              ))}
            </ol>

            <div className="mt-8 space-y-3 rounded-[12px] border border-white/10 bg-[#1A1A1A] p-5">
              <AddressRow
                label="USDT (TRC20) accepted"
                value={USDT_TRC20}
                kind="token"
              />
              <AddressRow
                label="FUDSX contract"
                value={FUDSX_ADDRESS}
                kind="token"
              />
            </div>

            <p className="mt-6 font-body text-xs text-[#6B7280]">
              FUDSX keeps its reference value: unspent tokens stay in your wallet
              and can be reused next round or swapped on SunSwap.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function AddressRow({
  label,
  value,
  kind,
}: {
  label: string;
  value: string;
  kind: "token" | "contract";
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div>
        <p className="font-body text-xs uppercase tracking-wide text-[#6B7280]">
          {label}
        </p>
        <p className="font-mono text-sm text-white/90">
          {shortenAddress(value, 6)}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <CopyButton value={value} />
        <TronScanLink value={value} kind={kind} label="View" />
      </div>
    </div>
  );
}
