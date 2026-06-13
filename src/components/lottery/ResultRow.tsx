import NumberBall from "@/components/ui/NumberBall";
import TronScanLink from "@/components/ui/TronScanLink";
import { formatDate, formatNumber, shortenAddress } from "@/lib/tron/formatters";
import type { DrawResult } from "@/lib/lottery/draw";

export default function ResultRow({ result }: { result: DrawResult }) {
  return (
    <tr className="border-b border-white/5 last:border-0 hover:bg-white/5">
      <td className="px-4 py-3 font-display text-lg text-white">
        #{result.round}
      </td>
      <td className="px-4 py-3 font-body text-xs text-[#9ca3af]">
        {formatDate(new Date(result.date).getTime())}
      </td>
      <td className="px-4 py-3">
        <div className="flex gap-1">
          {result.numbers.map((n, i) => (
            <NumberBall key={i} n={n} size="sm" variant="selected" />
          ))}
        </div>
      </td>
      <td className="px-4 py-3 text-right font-display text-lg text-[#FFD700]">
        {formatNumber(result.jackpot)}
      </td>
      <td className="px-4 py-3 text-right">
        {result.winner ? (
          result.txHash ? (
            <TronScanLink
              value={result.txHash}
              kind="transaction"
              label={shortenAddress(result.winner)}
            />
          ) : (
            <span className="font-body text-xs text-[#22C55E]">
              {shortenAddress(result.winner)}
            </span>
          )
        ) : (
          <span className="font-body text-xs text-[#6B7280]">Rollover</span>
        )}
      </td>
    </tr>
  );
}
