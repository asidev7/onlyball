"use client";

import { useEffect, useState } from "react";
import { Users, Coins, Loader2 } from "lucide-react";
import DashboardNav from "@/components/dashboard/DashboardNav";
import ConnectGate from "@/components/dashboard/ConnectGate";
import ReferralCard from "@/components/affiliate/ReferralCard";
import StatCard from "@/components/ui/StatCard";
import Badge from "@/components/ui/Badge";
import TronScanLink from "@/components/ui/TronScanLink";
import { useWallet } from "@/context/WalletContext";
import { api, type ApiAffiliate } from "@/lib/api/client";
import { formatNumber, shortenAddress } from "@/lib/tron/formatters";
import { REFERRAL_REWARD_FUDSX } from "@/lib/constants/config";

function AffiliateBody() {
  const { address } = useWallet();
  const [data, setData] = useState<ApiAffiliate | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!address) return;
    setLoading(true);
    api
      .affiliate(address)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [address]);

  const totalReferrals = data?.referrals_count ?? 0;
  const totalRewards = Number(data?.earnings_fudsx ?? 0);
  const recent = data?.referrals ?? [];

  return (
    <>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatCard
          label="Friends referred"
          value={String(totalReferrals)}
          icon={<Users className="h-3.5 w-3.5" />}
        />
        <StatCard
          gold
          label="FUDSX earned"
          value={formatNumber(totalRewards)}
          unit="FUDSX"
          icon={<Coins className="h-3.5 w-3.5" />}
        />
      </div>

      <div className="mt-6">
        <ReferralCard />
      </div>

      <div className="mt-8">
        <h2 className="font-head text-lg font-semibold text-white">
          Recent referrals
        </h2>
        {loading ? (
          <div className="mt-4 flex items-center gap-2 font-body text-sm text-[#6B7280]">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </div>
        ) : recent.length === 0 ? (
          <p className="mt-4 font-body text-sm text-[#6B7280]">
            No referrals yet. Share your link to start earning{" "}
            {REFERRAL_REWARD_FUDSX} FUDSX per friend who buys a ticket.
          </p>
        ) : (
          <div className="mt-4 space-y-3">
            {recent.map((r) => (
              <div
                key={r.address}
                className="flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-white/10 bg-[#1A1A1A] px-4 py-3"
              >
                <TronScanLink
                  value={r.address}
                  kind="address"
                  label={shortenAddress(r.address, 6)}
                />
                <span className="font-body text-xs text-[#6B7280]">
                  {r.tickets} ticket{r.tickets === 1 ? "" : "s"}
                </span>
                <Badge tone="green">+{REFERRAL_REWARD_FUDSX} FUDSX</Badge>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

export default function AffiliatePage() {
  return (
    <div className="bg-[#0D0D0D]">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <h1 className="font-head text-2xl font-semibold text-white sm:text-3xl">
          Affiliate program
        </h1>

        <div className="mt-6">
          <DashboardNav />
        </div>

        <div className="mt-8">
          <ConnectGate>
            <AffiliateBody />
          </ConnectGate>
        </div>
      </div>
    </div>
  );
}
