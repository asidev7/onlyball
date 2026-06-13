"use client";

import { useEffect, useState } from "react";
import {
  Ticket,
  CheckCircle2,
  AlertCircle,
  Wallet as WalletIcon,
} from "lucide-react";
import { useWallet } from "@/context/WalletContext";
import { useLotteryStore } from "@/store/lotteryStore";
import { useAffiliate } from "@/lib/hooks/useAffiliate";
import BallPicker from "@/components/lottery/BallPicker";
import NumberBall from "@/components/ui/NumberBall";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Modal from "@/components/ui/Modal";
import TicketCard, { type TicketCardData } from "@/components/lottery/TicketCard";
import {
  TICKET_PRICE_FUDSX,
  TICKET_PRICE_USDT,
} from "@/lib/constants/config";

export default function PlayPage() {
  const {
    isConnected,
    fudsxBalance,
    lottery,
    buyTicket,
    isLoading,
  } = useWallet();
  const { selected, referralCode, setReferral, clear, isComplete } =
    useLotteryStore();
  const { inboundRef } = useAffiliate();

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [status, setStatus] = useState<"idle" | "ok" | "err">("idle");
  const [err, setErr] = useState("");
  const [myTickets, setMyTickets] = useState<TicketCardData[]>([]);

  // Pre-fill the referral field from an inbound ?ref= link.
  useEffect(() => {
    if (inboundRef && !referralCode) setReferral(inboundRef);
  }, [inboundRef, referralCode, setReferral]);

  const balanceNum = Number(fudsxBalance.replace(/,/g, "")) || 0;
  const enoughBalance = balanceNum >= TICKET_PRICE_FUDSX;
  const ready = isConnected && isComplete() && enoughBalance;

  async function confirm() {
    setStatus("idle");
    setErr("");
    try {
      const hash = await buyTicket(selected, referralCode);
      setMyTickets((prev) => [
        {
          label: `Ticket #${prev.length + 1}`,
          numbers: [...selected],
          txHash: hash,
          status: "pending",
        },
        ...prev,
      ]);
      setStatus("ok");
      clear();
      setConfirmOpen(false);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Transaction failed.");
      setStatus("err");
    }
  }

  return (
    <div className="bg-[#0D0D0D]">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        {/* Balance + round bar */}
        <div className="mb-8 flex flex-col gap-3 rounded-[12px] border border-white/10 bg-[#1A1A1A] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <WalletIcon className="h-4 w-4 text-[#FF2D37]" />
            <span className="font-body text-sm text-[#9ca3af]">Your balance</span>
            <span className="font-display text-2xl text-[#FFD700]">
              {fudsxBalance}
              <span className="ml-1 font-body text-xs text-[#6B7280]">FUDSX</span>
            </span>
          </div>
          <span className="font-head text-sm font-semibold text-white">
            Round #{lottery.currentRound}
          </span>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
          {/* Picker */}
          <Card>
            <BallPicker />
          </Card>

          {/* Ticket summary */}
          <Card>
            <h2 className="font-head text-base font-semibold text-white">
              Your ticket
            </h2>

            <div className="mt-4">
              <p className="font-body text-xs uppercase tracking-wide text-[#6B7280]">
                Selected numbers
              </p>
              <div className="mt-2 flex min-h-[3rem] flex-wrap gap-2">
                {selected.length === 0 ? (
                  <span className="font-body text-sm text-[#6B7280]">
                    Pick 6 numbers to continue.
                  </span>
                ) : (
                  selected.map((n) => (
                    <NumberBall key={n} n={n} size="sm" variant="selected" />
                  ))
                )}
              </div>
            </div>

            <div className="mt-5 flex items-center justify-between border-y border-white/10 py-3">
              <span className="font-body text-sm text-[#9ca3af]">Price</span>
              <span className="font-display text-2xl text-white">
                {TICKET_PRICE_FUDSX}{" "}
                <span className="font-body text-xs text-[#6B7280]">
                  FUDSX (≈ {TICKET_PRICE_USDT} USDT)
                </span>
              </span>
            </div>

            <div className="mt-4">
              <label className="font-body text-xs uppercase tracking-wide text-[#6B7280]">
                Referral code (optional)
              </label>
              <input
                value={referralCode}
                onChange={(e) => setReferral(e.target.value.toUpperCase())}
                placeholder="A7F2C9B1"
                className="mt-2 w-full rounded-[12px] border border-white/10 bg-[#0D0D0D] px-3 py-2.5 font-body text-sm text-white outline-none focus:border-[#E31C25]"
              />
            </div>

            <Button
              className="mt-5 w-full"
              size="lg"
              icon={<Ticket className="h-5 w-5" />}
              disabled={!ready}
              onClick={() => setConfirmOpen(true)}
            >
              {!isConnected
                ? "Connect wallet to play"
                : !isComplete()
                ? "Pick 6 numbers"
                : !enoughBalance
                ? "Not enough FUDSX"
                : "Confirm my ticket"}
            </Button>

            {status === "ok" && (
              <div className="mt-3 flex items-center gap-2 rounded-[12px] border border-[#22C55E]/40 bg-[#22C55E]/10 px-3 py-2.5">
                <CheckCircle2 className="h-4 w-4 text-[#22C55E]" />
                <span className="font-body text-xs text-[#22C55E]">
                  Ticket purchased — good luck!
                </span>
              </div>
            )}
            {status === "err" && (
              <div className="mt-3 flex items-center gap-2 rounded-[12px] border border-[#E31C25]/40 bg-[#E31C25]/10 px-3 py-2.5">
                <AlertCircle className="h-4 w-4 text-[#FF2D37]" />
                <span className="font-body text-xs text-[#FF2D37]">{err}</span>
              </div>
            )}
          </Card>
        </div>

        {/* My tickets this round */}
        <div className="mt-10">
          <h2 className="font-head text-lg font-semibold text-white">
            My tickets this round
          </h2>
          <div className="mt-4 space-y-3">
            {myTickets.length === 0 ? (
              <p className="rounded-[12px] border border-dashed border-white/10 px-4 py-6 text-center font-body text-sm text-[#6B7280]">
                No tickets yet for round #{lottery.currentRound}.
              </p>
            ) : (
              myTickets.map((t, i) => <TicketCard key={i} {...t} />)
            )}
          </div>
        </div>
      </div>

      {/* Confirmation modal */}
      <Modal
        open={confirmOpen}
        onClose={() => !isLoading && setConfirmOpen(false)}
        title="Confirm your ticket"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setConfirmOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button onClick={confirm} loading={isLoading}>
              Confirm &amp; pay
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {selected.map((n) => (
              <NumberBall key={n} n={n} size="sm" variant="selected" />
            ))}
          </div>
          <div className="space-y-1.5 font-body text-sm text-[#9ca3af]">
            <Row label="Ticket price" value={`${TICKET_PRICE_FUDSX} FUDSX`} />
            <Row label="≈ in USDT" value={`${TICKET_PRICE_USDT} USDT`} />
            {referralCode && <Row label="Referral" value={referralCode} />}
            <Row label="Round" value={`#${lottery.currentRound}`} />
          </div>
          <p className="rounded-[12px] border border-white/10 bg-[#0D0D0D] px-3 py-2.5 font-body text-xs text-[#6B7280]">
            This approves {TICKET_PRICE_FUDSX} FUDSX and calls{" "}
            <code className="text-white/80">buyTicket</code> on the OnlyBall
            contract. You&apos;ll sign in your wallet.
          </p>
        </div>
      </Modal>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span>{label}</span>
      <span className="font-semibold text-white">{value}</span>
    </div>
  );
}
