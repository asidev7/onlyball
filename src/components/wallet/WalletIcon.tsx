import type { WalletType } from "@/lib/tron/walletAdapters";

// Brand-coloured wallet tiles with a recognisable glyph for each provider.
const BRAND: Record<WalletType, string> = {
  tronlink: "#1D62F0",
  trustwallet: "#3375BB",
  tokenpocket: "#2980FE",
  bitkeep: "#00CFBE",
};

export default function WalletIcon({
  type,
  className = "h-9 w-9",
}: {
  type: WalletType;
  className?: string;
}) {
  return (
    <span
      className={`flex items-center justify-center rounded-lg ${className}`}
      style={{ backgroundColor: BRAND[type] }}
      aria-hidden
    >
      <Glyph type={type} />
    </span>
  );
}

function Glyph({ type }: { type: WalletType }) {
  const common = {
    width: 20,
    height: 20,
    viewBox: "0 0 24 24",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
  };

  switch (type) {
    case "tronlink":
      // TRON-style triangle.
      return (
        <svg {...common}>
          <path
            d="M4 5.5 19.5 8.2 11 20 4 5.5Z"
            fill="#fff"
            fillOpacity="0.95"
          />
          <path
            d="M4 5.5 11 20 19.5 8.2M4 5.5 19.5 8.2M11 11.3 11 20M11 11.3 4 5.5M11 11.3 19.5 8.2"
            stroke={BRAND.tronlink}
            strokeWidth="1.1"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "trustwallet":
      // Shield.
      return (
        <svg {...common}>
          <path
            d="M12 3.2 19 6v5.2c0 4.4-2.9 7.6-7 9.6-4.1-2-7-5.2-7-9.6V6l7-2.8Z"
            fill="#fff"
          />
        </svg>
      );
    case "tokenpocket":
      // Pocket / layered card.
      return (
        <svg {...common}>
          <rect x="4" y="6" width="16" height="12" rx="3" fill="#fff" />
          <path d="M4 11h16" stroke={BRAND.tokenpocket} strokeWidth="1.6" />
          <circle cx="15.5" cy="14.5" r="1.6" fill={BRAND.tokenpocket} />
        </svg>
      );
    case "bitkeep":
      // Bitget-style chevrons.
      return (
        <svg {...common}>
          <path
            d="M8 4 14 9 10.5 12 14 15 8 20"
            stroke="#fff"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>
      );
    default:
      return null;
  }
}
