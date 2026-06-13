import type { ReactNode } from "react";

// Compact page header used on inner content pages.
export default function PageHero({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children?: ReactNode;
}) {
  return (
    <section className="hero-bg border-b border-white/10">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <h1 className="font-head text-3xl font-semibold text-white sm:text-4xl">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-2 max-w-2xl font-body text-sm text-[#9ca3af]">
            {subtitle}
          </p>
        )}
        {children}
      </div>
    </section>
  );
}
