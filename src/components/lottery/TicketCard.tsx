import NumberBall from "@/components/ui/NumberBall";
import TronScanLink from "@/components/ui/TronScanLink";
import Badge from "@/components/ui/Badge";

export interface TicketCardData {
  label: string; // e.g. "Ticket #1" or "Round #43"
  numbers: number[];
  txHash?: string | null;
  status?: "pending" | "win" | "loss";
  winningNumbers?: number[];
}

export default function TicketCard({
  label,
  numbers,
  txHash,
  status,
  winningNumbers,
}: TicketCardData) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-white/10 bg-[#1A1A1A] px-4 py-3">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-head text-sm font-semibold text-white">{label}</span>
        <div className="flex gap-1.5">
          {numbers.map((n, i) => (
            <NumberBall
              key={i}
              n={n}
              size="sm"
              variant={
                winningNumbers?.includes(n) ? "gold" : "selected"
              }
            />
          ))}
        </div>
      </div>
      <div className="flex items-center gap-3">
        {status === "win" && <Badge tone="win">✓ Winner</Badge>}
        {status === "loss" && <Badge tone="loss">No win</Badge>}
        {status === "pending" && <Badge tone="gold">Pending draw</Badge>}
        {txHash && <TronScanLink value={txHash} kind="transaction" label="Tx" />}
      </div>
    </div>
  );
}
