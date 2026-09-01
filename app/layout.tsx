import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BriefBond — Creator Campaign Escrow",
  description:
    "Lock a creator campaign brief and GEN payout, verify the public post with GenLayer validators, and enforce the settlement.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
  other: {
    "codex-preview": "development",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
