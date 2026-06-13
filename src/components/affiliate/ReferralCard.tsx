"use client";

import { Link2, Send, Share2 } from "lucide-react";
import { useWallet } from "@/context/WalletContext";
import { useAffiliate } from "@/lib/hooks/useAffiliate";
import CopyButton from "@/components/ui/CopyButton";
import { REFERRAL_REWARD_FUDSX } from "@/lib/constants/config";

export default function ReferralCard() {
  const { address } = useWallet();
  const { myCode, myLink } = useAffiliate();

  const shareText = `Play OnlyBall — the daily TRON lottery. Use my link and we both win FUDSX:`;
  const telegram = `https://t.me/share/url?url=${encodeURIComponent(
    myLink
  )}&text=${encodeURIComponent(shareText)}`;
  const twitter = `https://twitter.com/intent/tweet?text=${encodeURIComponent(
    shareText
  )}&url=${encodeURIComponent(myLink)}`;

  if (!address) return null;

  return (
    <div className="rounded-[12px] border border-white/10 bg-[#1A1A1A] p-6">
      <div className="flex items-center gap-2">
        <Link2 className="h-4 w-4 text-[#FF2D37]" />
        <h2 className="font-head text-base font-semibold text-white">
          My referral
        </h2>
      </div>

      <div className="mt-4 space-y-3">
        <Field label="Code">
          <span className="font-mono text-lg text-[#FFD700]">{myCode}</span>
          <CopyButton value={myCode} label="Copy" />
        </Field>
        <Field label="Link">
          <span className="truncate font-mono text-sm text-white/90">
            {myLink}
          </span>
          <CopyButton value={myLink} label="Copy" />
        </Field>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <a
          href={telegram}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-[12px] border border-white/10 bg-[#0D0D0D] px-4 py-2 font-head text-sm font-semibold text-white transition-colors hover:border-[#E31C25]"
        >
          <Send className="h-4 w-4" /> Share on Telegram
        </a>
        <a
          href={twitter}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-[12px] border border-white/10 bg-[#0D0D0D] px-4 py-2 font-head text-sm font-semibold text-white transition-colors hover:border-[#E31C25]"
        >
          <Share2 className="h-4 w-4" /> Share on X
        </a>
      </div>

      <p className="mt-4 font-body text-xs text-[#6B7280]">
        Earn +{REFERRAL_REWARD_FUDSX} FUDSX each time a friend buys a ticket with
        your link.
      </p>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[12px] border border-white/10 bg-[#0D0D0D] px-4 py-3">
      <div className="min-w-0">
        <p className="font-body text-xs uppercase tracking-wide text-[#6B7280]">
          {label}
        </p>
        <div className="mt-0.5 flex items-center gap-2 truncate">{children}</div>
      </div>
    </div>
  );
}
