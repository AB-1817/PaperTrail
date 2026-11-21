import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Fraunces } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

// Fraunces = open-source substitute for Editorial New (high-contrast light serif)
const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  weight: ["100", "200", "300", "400"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "PaperTrail — Research Intelligence Platform",
  description:
    "Discover, organize and synthesize academic research with verifiable evidence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`}>
      <body className="bg-canvas text-ink antialiased">{children}</body>
    </html>
  );
}
