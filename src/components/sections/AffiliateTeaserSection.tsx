"use client";

import Link from "next/link";
import { Gift, ArrowRight } from "lucide-react";
import { REFERRAL_REWARD_FUDSX } from "@/lib/constants/config";

export default function AffiliateTeaserSection() {
  return (
    <section className="bg-[#E31C25]">
      <div className="mx-auto flex max-w-5xl flex-col items-center gap-6 px-4 py-16 text-center sm:px-6">
        <span className="flex h-14 w-14 items-center justify-center rounded-[12px] bg-white/15 text-white">
          <Gift className="h-7 w-7" />
        </span>
        <h2 className="font-head text-3xl font-semibold text-white sm:text-4xl">
          Invite friends. Earn FUDSX.
        </h2>
        <p className="max-w-xl font-body text-sm text-white/90 sm:text-base">
          Every friend who plays with your referral link earns you{" "}
          <span className="font-semibold">
            +{REFERRAL_REWARD_FUDSX} FUDSX
          </span>{" "}
          — paid instantly and automatically by the smart contract.
        </p>
        <Link
          href="/dashboard/affiliate"
          className="inline-flex items-center gap-2 rounded-[12px] bg-white px-6 py-3 font-head text-sm font-semibold text-[#E31C25] transition-colors hover:bg-[#0D0D0D] hover:text-white"
        >
          Get my referral link
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </section>
  );
}
