"use client";

import { useEffect, useState } from "react";
import { Trophy, Gift, Loader2 } from "lucide-react";
import DashboardNav from "@/components/dashboard/DashboardNav";
import ConnectGate from "@/components/dashboard/ConnectGate";
import StatCard from "@/components/ui/StatCard";
import Badge from "@/components/ui/Badge";
import TronScanLink from "@/components/ui/TronScanLink";
import { useWallet } from "@/context/WalletContext";
import { api, type ApiTicket } from "@/lib/api/client";
import { formatDate, formatNumber } from "@/lib/tron/formatters";

function RewardsBody() {
  const { address } = useWallet();
  const [referralEarned, setReferralEarned] = useState(0);
  const [wins, setWins] = useState<ApiTicket[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!address) return;
    setLoading(true);
    Promise.all([
      api.affiliate(address).catch(() => null),
      api.myTickets(address).catch(() => [] as ApiTicket[]),
    ])
      .then(([aff, tickets]) => {
        setReferralEarned(Number(aff?.earnings_fudsx ?? 0));
        setWins(tickets.filter((t) => t.is_winner));
      })
      .finally(() => setLoading(false));
  }, [address]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 font-body text-sm text-[#6B7280]">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading rewards…
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatCard
          gold
          label="Referral rewards"
          value={formatNumber(referralEarned)}
          unit="FUDSX"
          icon={<Gift className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Jackpot wins"
          value={String(wins.length)}
          icon={<Trophy className="h-3.5 w-3.5" />}
        />
      </div>

      <div className="mt-8">
        <h2 className="font-head text-lg font-semibold text-white">
          Jackpot history
        </h2>
        {wins.length === 0 ? (
          <p className="mt-4 font-body text-sm text-[#6B7280]">
            No jackpot wins yet. Referral rewards are paid out from the treasury.
          </p>
        ) : (
          <div className="mt-4 space-y-3">
            {wins.map((w) => (
              <div
                key={w.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-white/10 bg-[#1A1A1A] px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <Badge tone="gold">Jackpot</Badge>
                  <span className="font-head text-sm font-semibold text-white">
                    Round #{w.round_index} won
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-body text-xs text-[#6B7280]">
                    {formatDate(new Date(w.created_at).getTime())}
                  </span>
                  <TronScanLink value={w.txid} kind="transaction" label="Tx" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

export default function RewardsPage() {
  return (
    <div className="bg-[#0D0D0D]">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <h1 className="font-head text-2xl font-semibold text-white sm:text-3xl">
          Rewards
        </h1>

        <div className="mt-6">
          <DashboardNav />
        </div>

        <div className="mt-8">
          <ConnectGate>
            <RewardsBody />
          </ConnectGate>
        </div>
      </div>
    </div>
  );
}
