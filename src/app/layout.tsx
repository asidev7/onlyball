import type { Metadata } from "next";
import { Bebas_Neue, Sora, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { WalletProvider } from "@/context/WalletContext";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { APP_NAME, APP_TAGLINE, APP_URL } from "@/lib/constants/config";

const bebas = Bebas_Neue({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-bebas",
  display: "swap",
});

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(APP_URL),
  title: {
    default: `${APP_NAME} — ${APP_TAGLINE}`,
    template: `%s · ${APP_NAME}`,
  },
  description:
    "OnlyBall is the daily decentralized lottery on TRON, powered by the FUDSX token. Pick 6 numbers, play in FUDSX, and win every day. Transparent, on-chain draws at midnight UTC.",
  keywords: [
    "OnlyBall",
    "TRON lottery",
    "FUDSX",
    "crypto lottery",
    "TRC20",
    "daily draw",
    "decentralized lottery",
  ],
  openGraph: {
    title: `${APP_NAME} — ${APP_TAGLINE}`,
    description:
      "The daily decentralized lottery on TRON, powered by FUDSX. On-chain draws every midnight UTC.",
    url: APP_URL,
    siteName: APP_NAME,
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: `${APP_NAME} — ${APP_TAGLINE}`,
    description:
      "Pick 6 numbers, play in FUDSX, win daily. On-chain draws on TRON.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${bebas.variable} ${sora.variable} ${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-[#0D0D0D] text-white">
        <WalletProvider>
          <Header />
          <main className="flex flex-1 flex-col">{children}</main>
          <Footer />
        </WalletProvider>
      </body>
    </html>
  );
}
