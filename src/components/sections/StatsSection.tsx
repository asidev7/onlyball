"use client";

import { useEffect, useState } from "react";
import { Trophy, Ticket, Hash } from "lucide-react";
import { useWallet } from "@/context/WalletContext";
import StatCard from "@/components/ui/StatCard";
import { api } from "@/lib/api/client";
import { formatNumber } from "@/lib/tron/formatters";

export default function StatsSection() {
  const { lottery } = useWallet();
  const [ticketsThisRound, setTicketsThisRound] = useState(0);

  useEffect(() => {
    api
      .currentRound()
      .then((r) => setTicketsThisRound(r.tickets_count))
      .catch(() => setTicketsThisRound(0));
  }, []);

  return (
    <section className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            light
            gold
            label="Today's jackpot"
            value={formatNumber(lottery.jackpot)}
            unit="FUDSX"
            icon={<Trophy className="h-3.5 w-3.5" />}
          />
          <StatCard
            light
            label="Tickets this round"
            value={formatNumber(ticketsThisRound)}
            icon={<Ticket className="h-3.5 w-3.5" />}
          />
          <StatCard
            light
            label="Current round"
            value={`#${lottery.currentRound}`}
            icon={<Hash className="h-3.5 w-3.5" />}
          />
        </div>
      </div>
    </section>
  );
}
