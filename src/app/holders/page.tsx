"use client";

import { Loader2, Users, Coins, AlertCircle } from "lucide-react";
import { useHolders } from "@/lib/hooks/useHolders";
import PageHero from "@/components/layout/PageHero";
import StatCard from "@/components/ui/StatCard";
import CopyButton from "@/components/ui/CopyButton";
import TronScanLink from "@/components/ui/TronScanLink";
import { FUDSX_ADDRESS } from "@/lib/constants/contract";
import { formatNumber, shortenAddress } from "@/lib/tron/formatters";

export default function HoldersPage() {
  const { holders, totalSupply, holderCount, isLoading, error } = useHolders(50);

  return (
    <div className="bg-[#0D0D0D]">
      <PageHero
        title="FUDSX holders"
        subtitle="Live holder distribution of the FUDSX token, fetched directly from the TronGrid API."
      />

      <section className="bg-[#0D0D0D]">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          {/* Global stats */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              gold
              label="Total supply (top 50)"
              value={formatNumber(Math.round(totalSupply))}
              unit="FUDSX"
              icon={<Coins className="h-3.5 w-3.5" />}
            />
            <StatCard
              label="Holders"
              value={formatNumber(holderCount)}
              icon={<Users className="h-3.5 w-3.5" />}
            />
            <div className="rounded-[12px] border border-white/10 bg-[#1A1A1A] p-6">
              <p className="font-body text-xs uppercase tracking-wide text-white/50">
                Contract
              </p>
              <p className="mt-2 font-mono text-sm text-white/90">
                {shortenAddress(FUDSX_ADDRESS, 6)}
              </p>
              <div className="mt-2 flex items-center gap-2">
                <CopyButton value={FUDSX_ADDRESS} label="Copy" />
                <TronScanLink value={FUDSX_ADDRESS} kind="token" label="TronScan" />
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="mt-8 overflow-x-auto rounded-[12px] border border-white/10 bg-[#1A1A1A]">
            {isLoading ? (
              <div className="flex items-center justify-center gap-2 py-16 font-body text-sm text-[#6B7280]">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading holders…
              </div>
            ) : error ? (
              <div className="flex items-center justify-center gap-2 py-16 font-body text-sm text-[#FF2D37]">
                <AlertCircle className="h-4 w-4" /> {error}
              </div>
            ) : holders.length === 0 ? (
              <div className="py-16 text-center font-body text-sm text-[#6B7280]">
                No holders found.
              </div>
            ) : (
              <table className="w-full min-w-[560px]">
                <thead>
                  <tr className="border-b border-white/10 text-left font-body text-xs uppercase tracking-wide text-[#6B7280]">
                    <th className="px-4 py-3">#</th>
                    <th className="px-4 py-3">Address</th>
                    <th className="px-4 py-3 text-right">Balance</th>
                    <th className="px-4 py-3 text-right">% supply</th>
                  </tr>
                </thead>
                <tbody>
                  {holders.map((h) => (
                    <tr
                      key={h.address}
                      className="border-b border-white/5 last:border-0 hover:bg-white/5"
                    >
                      <td className="px-4 py-3 font-display text-lg text-white/60">
                        {h.rank}
                      </td>
                      <td className="px-4 py-3">
                        <TronScanLink
                          value={h.address}
                          kind="address"
                          label={shortenAddress(h.address, 6)}
                        />
                      </td>
                      <td className="px-4 py-3 text-right font-display text-lg text-white">
                        {formatNumber(Math.round(h.balance))}
                      </td>
                      <td className="px-4 py-3 text-right font-head text-sm text-[#FFD700]">
                        {h.percent.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
