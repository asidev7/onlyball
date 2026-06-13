"use client";

import { useWallet } from "@/context/WalletContext";
import { WALLET_OPTIONS, type WalletType } from "@/lib/tron/walletAdapters";
import Modal from "@/components/ui/Modal";
import WalletIcon from "@/components/wallet/WalletIcon";

export default function WalletSelector({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { connect, isConnecting, error } = useWallet();

  async function handle(type: WalletType) {
    await connect(type);
    if (typeof window !== "undefined" && window.tronWeb?.defaultAddress?.base58) {
      onClose();
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Choose your wallet">
      <div className="space-y-2">
        {WALLET_OPTIONS.map((w) => (
          <button
            key={w.type}
            disabled={isConnecting}
            onClick={() => handle(w.type)}
            className="flex w-full items-center justify-between rounded-[12px] border border-white/10 bg-[#0D0D0D] px-4 py-3 text-left transition-colors hover:border-[#E31C25] disabled:opacity-50"
          >
            <span className="flex items-center gap-3">
              <WalletIcon type={w.type} />
              <span>
                <span className="block font-head text-sm font-semibold text-white">
                  {w.name}
                </span>
                <span className="block font-body text-xs text-[#6B7280]">
                  {w.description}
                </span>
              </span>
            </span>
          </button>
        ))}

        {error && (
          <p className="rounded-lg border border-[#E31C25]/40 bg-[#E31C25]/10 px-3 py-2 font-body text-xs text-[#FF2D37]">
            {error}
          </p>
        )}

        <p className="pt-1 text-center font-body text-xs text-[#6B7280]">
          New to TRON?{" "}
          <a
            href="https://www.tronlink.org/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#FF2D37] hover:underline"
          >
            Get TronLink →
          </a>
        </p>
      </div>
    </Modal>
  );
}

