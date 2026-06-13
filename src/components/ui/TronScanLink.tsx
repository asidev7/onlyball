import { ExternalLink } from "lucide-react";
import clsx from "clsx";
import { TRONSCAN_BASE } from "@/lib/constants/config";

type Kind = "address" | "transaction" | "contract" | "token";

const paths: Record<Kind, string> = {
  address: "/address/",
  transaction: "/transaction/",
  contract: "/contract/",
  token: "/token20/",
};

export default function TronScanLink({
  value,
  kind = "address",
  label,
  className,
}: {
  value: string;
  kind?: Kind;
  label?: string;
  className?: string;
}) {
  return (
    <a
      href={`${TRONSCAN_BASE}${paths[kind]}${value}`}
      target="_blank"
      rel="noopener noreferrer"
      className={clsx(
        "inline-flex items-center gap-1.5 font-body text-xs text-[#FF2D37] transition-colors hover:text-white",
        className
      )}
    >
      {label || "TronScan"}
      <ExternalLink className="h-3.5 w-3.5" />
    </a>
  );
}
