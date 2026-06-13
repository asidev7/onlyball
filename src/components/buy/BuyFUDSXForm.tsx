"use client";

import { useState } from "react";
import { ArrowDown, Repeat, CheckCircle2, AlertCircle } from "lucide-react";
import { useWallet } from "@/context/WalletContext";
import { FUDSX_PER_USDT } from "@/lib/constants/config";
import Button from "@/components/ui/Button";
import TronScanLink from "@/components/ui/TronScanLink";

export default function BuyFUDSXForm({ light = false }: { light?: boolean }) {
  const { buyFUDSX, isConnected, usdtBalance, fudsxBalance } = useWallet();
  const [usdt, setUsdt] = useState("20");
  const [status, setStatus] = useState<"idle" | "loading" | "ok" | "err">("idle");
  const [hash, setHash] = useState("");
  const [err, setErr] = useState("");

  const usdtNum = Number(usdt) || 0;
  const fudsxOut = usdtNum * FUDSX_PER_USDT;
  const balanceNum = Number(usdtBalance.replace(/,/g, "")) || 0;
  const valid = usdtNum > 0 && usdtNum <= balanceNum;

  async function submit() {
    setStatus("loading");
    setErr("");
    try {
      const tx = await buyFUDSX(usdt);
      setHash(tx);
      setStatus("ok");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Purchase failed.");
      setStatus("err");
    }
  }

  const label = light ? "text-[#6B7280]" : "text-white/60";
  const inputBg = light
    ? "border-black/10 bg-white text-[#0D0D0D]"
    : "border-white/10 bg-[#0D0D0D] text-white";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center gap-2 rounded-[12px] border border-[#E31C25]/30 bg-[#E31C25]/10 px-4 py-2.5">
        <Repeat className="h-4 w-4 text-[#FF2D37]" />
        <span className="font-head text-sm font-semibold">
          1 USDT = {FUDSX_PER_USDT} FUDSX
        </span>
      </div>

      <div className={`rounded-[12px] border p-4 ${inputBg}`}>
        <div className="mb-1 flex justify-between">
          <span className={`font-body text-xs ${label}`}>You send</span>
          <span className={`font-body text-xs ${label}`}>
            Balance: {usdtBalance} USDT
          </span>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min="0"
            value={usdt}
            onChange={(e) => setUsdt(e.target.value)}
            className="w-full bg-transparent font-display text-3xl outline-none"
          />
          <span className="font-head text-sm font-semibold text-[#6B7280]">
            USDT
          </span>
        </div>
      </div>

      <div className="flex justify-center">
        <ArrowDown className="h-5 w-5 text-[#E31C25]" />
      </div>

      <div className={`rounded-[12px] border p-4 ${inputBg}`}>
        <div className="mb-1 flex justify-between">
          <span className={`font-body text-xs ${label}`}>You receive</span>
          <span className={`font-body text-xs ${label}`}>
            Balance: {fudsxBalance} FUDSX
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-display text-3xl text-[#FFD700]">
            {fudsxOut.toLocaleString("en-US")}
          </span>
          <span className="font-head text-sm font-semibold text-[#6B7280]">
            FUDSX
          </span>
        </div>
      </div>

      <Button
        className="w-full"
        size="lg"
        disabled={!isConnected || !valid}
        loading={status === "loading"}
        onClick={submit}
      >
        {isConnected ? "Buy now" : "Connect wallet to buy"}
      </Button>

      {status === "ok" && (
        <div className="flex items-center gap-2 rounded-[12px] border border-[#22C55E]/40 bg-[#22C55E]/10 px-3 py-2.5">
          <CheckCircle2 className="h-4 w-4 text-[#22C55E]" />
          <span className="font-body text-xs text-[#22C55E]">Purchase submitted.</span>
          <TronScanLink value={hash} kind="transaction" label="View" />
        </div>
      )}
      {status === "err" && (
        <div className="flex items-center gap-2 rounded-[12px] border border-[#E31C25]/40 bg-[#E31C25]/10 px-3 py-2.5">
          <AlertCircle className="h-4 w-4 text-[#FF2D37]" />
          <span className="font-body text-xs text-[#FF2D37]">{err}</span>
        </div>
      )}
    </div>
  );
}
