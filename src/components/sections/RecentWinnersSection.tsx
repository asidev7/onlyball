"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import BallDisplay from "@/components/lottery/BallDisplay";
import Badge from "@/components/ui/Badge";
import { api } from "@/lib/api/client";
import { formatDate, formatNumber, shortenAddress } from "@/lib/tron/formatters";

interface RecentRow {
  round: number;
  date: string;
  numbers: number[];
  jackpot: number;
  winner: string | null;
}

export default function RecentWinnersSection() {
  const [recent, setRecent] = useState<RecentRow[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api
      .results()
      .then((rows) =>
        setRecent(
          rows.slice(0, 3).map((r) => ({
            round: r.index,
            date: r.draws_at,
            numbers: r.winning_numbers ?? [],
            jackpot: Number(r.jackpot_fudsx),
            winner: r.winners[0]?.address ?? null,
          }))
        )
      )
      .catch(() => setRecent([]))
      .finally(() => setLoaded(true));
  }, []);

  return (
    <section className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="font-head text-3xl font-semibold text-[#0D0D0D] sm:text-4xl">
              Latest results
            </h2>
            <p className="mt-2 font-body text-sm text-[#6B7280]">
              Draws are recorded every midnight UTC.
            </p>
          </div>
          <Link
            href="/results"
            className="hidden items-center gap-1.5 font-head text-sm font-semibold text-[#E31C25] hover:text-[#9B0E14] sm:flex"
          >
            All results <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {loaded && recent.length === 0 ? (
          <div className="mt-8 rounded-[12px] border border-black/10 bg-white p-8 text-center">
            <p className="font-display text-2xl text-[#0D0D0D]">
              First draw coming soon
            </p>
            <p className="mt-2 font-body text-sm text-[#6B7280]">
              Buy a ticket to be in the very first OnlyBall round.
            </p>
          </div>
        ) : (
          <div className="mt-8 space-y-3">
            {recent.map((r) => (
              <div
                key={r.round}
                className="flex flex-col gap-4 rounded-[12px] border border-black/10 bg-white p-5 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6">
                  <div className="min-w-[110px]">
                    <p className="font-display text-2xl text-[#0D0D0D]">
                      Round #{r.round}
                    </p>
                    <p className="font-body text-xs text-[#6B7280]">
                      {formatDate(new Date(r.date).getTime())}
                    </p>
                  </div>
                  <BallDisplay
                    numbers={r.numbers}
                    size="sm"
                    variant="winning"
                    animate={false}
                  />
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="font-display text-xl text-[#0D0D0D]">
                      {formatNumber(r.jackpot)}{" "}
                      <span className="font-body text-xs text-[#6B7280]">
                        FUDSX
                      </span>
                    </p>
                    {r.winner ? (
                      <span className="font-body text-xs text-[#22C55E]">
                        {shortenAddress(r.winner)}
                      </span>
                    ) : (
                      <Badge tone="neutral">Rollover</Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6 sm:hidden">
          <Link
            href="/results"
            className="flex items-center justify-center gap-1.5 font-head text-sm font-semibold text-[#E31C25]"
          >
            All results <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
