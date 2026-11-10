import type { Metadata } from "next";
import "@/styles/globals.css";
import { AppQueryProvider } from "@/providers/query-provider";

export const metadata: Metadata = {
  title: "AI-Native Social Media Agent Team v2",
  description:
    "Enterprise AI Operations Command Center for Autonomous Multi-Agent Social Media Marketing with Hash-Chain Governance",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-navy-950 text-slate-100 min-h-screen">
        <AppQueryProvider>{children}</AppQueryProvider>
      </body>
    </html>
  );
}

