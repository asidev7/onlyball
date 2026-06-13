"use client";

import { useState, type ReactNode } from "react";
import { Wallet } from "lucide-react";
import { useWallet } from "@/context/WalletContext";
import Button from "@/components/ui/Button";
import WalletSelector from "@/components/wallet/WalletSelector";

// Wraps connected-only dashboard content; prompts to connect otherwise.
export default function ConnectGate({ children }: { children: ReactNode }) {
  const { isConnected } = useWallet();
  const [open, setOpen] = useState(false);

  if (isConnected) return <>{children}</>;

  return (
    <div className="flex flex-col items-center justify-center rounded-[12px] border border-dashed border-white/15 bg-[#1A1A1A] px-6 py-20 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-[12px] bg-[#E31C25]/15 text-[#FF2D37]">
        <Wallet className="h-7 w-7" />
      </span>
      <h2 className="mt-4 font-head text-xl font-semibold text-white">
        Connect your wallet
      </h2>
      <p className="mt-2 max-w-sm font-body text-sm text-[#9ca3af]">
        Connect a TRON wallet to view your dashboard, tickets, referrals and
        rewards.
      </p>
      <Button
        className="mt-6"
        icon={<Wallet className="h-4 w-4" />}
        onClick={() => setOpen(true)}
      >
        Connect Wallet
      </Button>
      <WalletSelector open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
