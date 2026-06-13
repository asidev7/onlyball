"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import PageHero from "@/components/layout/PageHero";
import BallDisplay from "@/components/lottery/BallDisplay";
import ResultRow from "@/components/lottery/ResultRow";
import Badge from "@/components/ui/Badge";
import { api, type ApiResult } from "@/lib/api/client";
import type { DrawResult } from "@/lib/lottery/draw";
import { formatDate, formatNumber, shortenAddress } from "@/lib/tron/formatters";

function toDrawResult(r: ApiResult): DrawResult {
  return {
    round: r.index,
    date: r.draws_at,
    numbers: r.winning_numbers ?? [],
    jackpot: Number(r.jackpot_fudsx),
    winner: r.winners[0]?.address ?? null,
    txHash: null,
    totalTickets: r.tickets_count,
  };
}

export default function ResultsPage() {
  const [history, setHistory] = useState<DrawResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .results()
      .then((rows) => setHistory(rows.map(toDrawResult)))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  const latest = history[0];

  return (
    <div className="bg-[#0D0D0D]">
      <PageHero
        title="Results"
        subtitle="Every draw is recorded at midnight UTC. Ticket payments are verifiable on TronScan."
      />

      {loading ? (
        <div className="flex items-center justify-center gap-2 py-24 font-body text-sm text-[#6B7280]">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading results…
        </div>
      ) : !latest ? (
        <div className="mx-auto max-w-6xl px-4 py-24 text-center sm:px-6">
          <p className="font-display text-3xl text-white">No draw yet</p>
          <p className="mt-2 font-body text-sm text-[#6B7280]">
            The first round is still open. Winning numbers appear here once it is
            drawn.
          </p>
        </div>
      ) : (
        <>
          {/* Latest draw */}
          <section className="border-b border-white/10 bg-[#0D0D0D]">
            <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
              <div className="rounded-[12px] border border-[#FFD700]/30 bg-[#1A1A1A] p-6 sm:p-8">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-display text-3xl text-white">
                    Round #{latest.round}
                  </span>
                  <Badge tone="gold">Latest draw</Badge>
                  <span className="font-body text-xs text-[#6B7280]">
                    {formatDate(new Date(latest.date).getTime())} · 00:00 UTC
                  </span>
                </div>

                <p className="mt-6 font-body text-xs uppercase tracking-widest text-[#6B7280]">
                  Winning numbers
                </p>
                <div className="mt-3">
                  <BallDisplay numbers={latest.numbers} size="lg" variant="winning" />
                </div>

                <div className="mt-8 flex flex-wrap items-center gap-x-10 gap-y-4">
                  <div>
                    <p className="font-body text-xs uppercase tracking-wide text-[#6B7280]">
                      Jackpot
                    </p>
                    <p className="font-display text-3xl text-[#FFD700]">
                      {formatNumber(latest.jackpot)}{" "}
                      <span className="font-body text-sm text-[#6B7280]">FUDSX</span>
                    </p>
                  </div>
                  <div>
                    <p className="font-body text-xs uppercase tracking-wide text-[#6B7280]">
                      Winner
                    </p>
                    {latest.winner ? (
                      <p className="font-head text-lg font-semibold text-[#22C55E]">
                        {shortenAddress(latest.winner)}
                      </p>
                    ) : (
                      <p className="font-head text-lg font-semibold text-[#6B7280]">
                        Rollover
                      </p>
                    )}
                  </div>
                  <div>
                    <p className="font-body text-xs uppercase tracking-wide text-[#6B7280]">
                      Tickets
                    </p>
                    <p className="font-display text-3xl text-white">
                      {formatNumber(latest.totalTickets)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Full history */}
          <section className="bg-[#0D0D0D]">
            <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
              <h2 className="mb-6 font-head text-2xl font-semibold text-white">
                Full history
              </h2>
              <div className="overflow-x-auto rounded-[12px] border border-white/10 bg-[#1A1A1A]">
                <table className="w-full min-w-[640px]">
                  <thead>
                    <tr className="border-b border-white/10 text-left font-body text-xs uppercase tracking-wide text-[#6B7280]">
                      <th className="px-4 py-3">Round</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Numbers</th>
                      <th className="px-4 py-3 text-right">Jackpot</th>
                      <th className="px-4 py-3 text-right">Winner</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((r) => (
                      <ResultRow key={r.round} result={r} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
