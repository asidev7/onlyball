import Link from "next/link";

export default function Logo({ size = 28 }: { size?: number }) {
  return (
    <Link href="/" className="flex items-center gap-2">
      <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden>
        <circle cx="16" cy="16" r="15" fill="#E31C25" stroke="#FF2D37" strokeWidth="2" />
        <circle cx="16" cy="16" r="9" fill="#0D0D0D" />
        <circle cx="16" cy="16" r="3" fill="#FFD700" />
      </svg>
      <span className="font-display text-2xl leading-none text-white">
        ONLY<span className="text-[#E31C25]">BALL</span>
      </span>
    </Link>
  );
}
