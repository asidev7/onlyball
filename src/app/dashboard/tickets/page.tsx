"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import DashboardNav from "@/components/dashboard/DashboardNav";
import ConnectGate from "@/components/dashboard/ConnectGate";
import TicketCard, { type TicketCardData } from "@/components/lottery/TicketCard";
import { useWallet } from "@/context/WalletContext";
import { api, type ApiTicket } from "@/lib/api/client";

function toCard(t: ApiTicket): TicketCardData {
  const status: TicketCardData["status"] = t.is_winner
    ? "win"
    : t.round_status === "drawn"
      ? "loss"
      : "pending";
  return {
    label: `Round #${t.round_index}`,
    numbers: t.numbers,
    txHash: t.txid,
    status,
    winningNumbers: t.winning_numbers ?? undefined,
  };
}

function TicketList() {
  const { address } = useWallet();
  const [tickets, setTickets] = useState<TicketCardData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!address) return;
    setLoading(true);
    api
      .myTickets(address)
      .then((rows) => setTickets(rows.map(toCard)))
      .catch(() => setTickets([]))
      .finally(() => setLoading(false));
  }, [address]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-12 font-body text-sm text-[#6B7280]">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading your tickets…
      </div>
    );
  }
  if (tickets.length === 0) {
    return (
      <div className="rounded-[12px] border border-white/10 bg-[#1A1A1A] p-8 text-center font-body text-sm text-[#6B7280]">
        No tickets yet. Head to{" "}
        <a href="/play" className="text-[#FF2D37] hover:underline">
          Play
        </a>{" "}
        to buy your first one.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {tickets.map((t, i) => (
        <TicketCard key={i} {...t} />
      ))}
    </div>
  );
}

export default function TicketsPage() {
  return (
    <div className="bg-[#0D0D0D]">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <h1 className="font-head text-2xl font-semibold text-white sm:text-3xl">
          My tickets
        </h1>

        <div className="mt-6">
          <DashboardNav />
        </div>

        <div className="mt-8">
          <ConnectGate>
            <TicketList />
          </ConnectGate>
        </div>
      </div>
    </div>
  );
}
