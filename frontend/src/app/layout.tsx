import type { Metadata, Viewport } from "next";
import { Gabarito } from "next/font/google";

import { AppShell } from "@/components/shell/AppShell";
import { Providers } from "@/store/providers";

import "./globals.css";

const gabarito = Gabarito({
  subsets: ["latin", "latin-ext"],
  variable: "--font-gabarito",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Stumble",
  description: "Speak French. The words you can't find become the words you review.",
  applicationName: "Stumble",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "Stumble" },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#ffd84a",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${gabarito.variable} h-full`}>
      <body className="min-h-dvh">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
