"use client";

import { useEffect, useState } from "react";
import { Wallet, Ticket, Gift, Loader2 } from "lucide-react";
import { useWallet } from "@/context/WalletContext";
import DashboardNav from "@/components/dashboard/DashboardNav";
import ConnectGate from "@/components/dashboard/ConnectGate";
import ReferralCard from "@/components/affiliate/ReferralCard";
import StatCard from "@/components/ui/StatCard";
import TicketCard, { type TicketCardData } from "@/components/lottery/TicketCard";
import { api, type ApiTicket } from "@/lib/api/client";
import { formatNumber, shortenAddress } from "@/lib/tron/formatters";

function toCard(t: ApiTicket): TicketCardData {
  return {
    label: `Round #${t.round_index}`,
    numbers: t.numbers,
    txHash: t.txid,
    status: t.is_winner
      ? "win"
      : t.round_status === "drawn"
        ? "loss"
        : "pending",
    winningNumbers: t.winning_numbers ?? undefined,
  };
}

function DashboardBody() {
  const { address, fudsxBalance } = useWallet();
  const [tickets, setTickets] = useState<ApiTicket[]>([]);
  const [referral, setReferral] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!address) return;
    setLoading(true);
    Promise.all([
      api.myTickets(address).catch(() => [] as ApiTicket[]),
      api.affiliate(address).catch(() => null),
    ])
      .then(([t, aff]) => {
        setTickets(t);
        setReferral(Number(aff?.earnings_fudsx ?? 0));
      })
      .finally(() => setLoading(false));
  }, [address]);

  return (
    <>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          gold
          label="FUDSX balance"
          value={fudsxBalance}
          unit="FUDSX"
          icon={<Wallet className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Tickets played"
          value={loading ? "…" : String(tickets.length)}
          icon={<Ticket className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Referral earned"
          value={loading ? "…" : formatNumber(referral)}
          unit="FUDSX"
          icon={<Gift className="h-3.5 w-3.5" />}
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ReferralCard />

        <div>
          <h2 className="font-head text-lg font-semibold text-white">
            Recent tickets
          </h2>
          {loading ? (
            <div className="mt-4 flex items-center gap-2 font-body text-sm text-[#6B7280]">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : tickets.length === 0 ? (
            <p className="mt-4 font-body text-sm text-[#6B7280]">
              No tickets yet.{" "}
              <a href="/play" className="text-[#FF2D37] hover:underline">
                Play your first round →
              </a>
            </p>
          ) : (
            <div className="mt-4 space-y-3">
              {tickets.slice(0, 3).map((t) => (
                <TicketCard key={t.id} {...toCard(t)} />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default function DashboardPage() {
  const { address } = useWallet();

  return (
    <div className="bg-[#0D0D0D]">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <h1 className="font-head text-2xl font-semibold text-white sm:text-3xl">
          {address ? <>Hello {shortenAddress(address)} 👋</> : <>Dashboard</>}
        </h1>

        <div className="mt-6">
          <DashboardNav />
        </div>

        <div className="mt-8">
          <ConnectGate>
            <DashboardBody />
          </ConnectGate>
        </div>
      </div>
    </div>
  );
}
