"use client";

import { useState } from "react";
import { Wallet, LogOut } from "lucide-react";
import { useWallet } from "@/context/WalletContext";
import Button from "@/components/ui/Button";
import WalletSelector from "@/components/wallet/WalletSelector";
import WalletBadge from "@/components/wallet/WalletBadge";

export default function WalletButton() {
  const { isConnected, disconnect } = useWallet();
  const [open, setOpen] = useState(false);

  if (isConnected) {
    return (
      <div className="flex items-center gap-2">
        <WalletBadge />
        <Button
          variant="outline"
          size="sm"
          onClick={disconnect}
          icon={<LogOut className="h-3.5 w-3.5" />}
        >
          <span className="hidden sm:inline">Disconnect</span>
        </Button>
      </div>
    );
  }

  return (
    <>
      <Button onClick={() => setOpen(true)} icon={<Wallet className="h-4 w-4" />}>
        Connect Wallet
      </Button>
      <WalletSelector open={open} onClose={() => setOpen(false)} />
    </>
  );
}
