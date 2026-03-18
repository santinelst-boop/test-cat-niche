import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "Enciclopedia Raselor de Pisici",
    template: "%s | Enciclopedia Pisicilor"
  },
  description: "Ghid complet despre cele mai populare rase de pisici. Descoperă caracteristicile, temperamentul și îngrijirea fiecărei rase.",
  keywords: ["pisici", "rase pisici", "Bengal", "Siameză", "Maine Coon", "îngrijire pisici"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ro">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
