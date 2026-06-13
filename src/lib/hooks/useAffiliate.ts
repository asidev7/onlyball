"use client";

// Affiliate data for the connected wallet (code, link, stored inbound ref).
import { useEffect, useState } from "react";
import { useWallet } from "@/context/WalletContext";
import {
  deriveCodeFromAddress,
  getReferralLink,
  getStoredReferral,
} from "@/lib/affiliate/referral";

export interface AffiliateData {
  myCode: string;
  myLink: string;
  inboundRef: string; // referral code captured from the URL
}

export function useAffiliate(): AffiliateData {
  const { address } = useWallet();
  const [inboundRef, setInboundRef] = useState("");

  useEffect(() => {
    setInboundRef(getStoredReferral());
  }, []);

  const myCode = address ? deriveCodeFromAddress(address) : "";
  const myLink = myCode ? getReferralLink(myCode) : "";

  return { myCode, myLink, inboundRef };
}
