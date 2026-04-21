import type { Metadata } from "next";
import { Geist, Geist_Mono, Syne } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { FeedbackButton } from "@/components/feedback-button";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "SupoClip",
  description: "Turn long videos into viral-ready shorts.",
  icons: {
    icon: "/icon.svg",
  },
};

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="dark" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} ${syne.variable} antialiased bg-zinc-950 text-zinc-100 overflow-hidden`}>
        <div className="flex h-screen w-full">
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0 relative">
            <Topbar />
            <main className="flex-1 overflow-y-auto custom-scrollbar relative">
              {children}
            </main>
          </div>
        </div>
        <FeedbackButton />
        <Toaster />
      </body>
    </html>
  );
}
