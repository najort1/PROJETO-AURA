import type { Metadata } from "next";
import "./globals.css";
import { BannerSynthetic } from "@/components/branding/banner-synthetic";

export const metadata: Metadata = {
  title: "PROJETO AURA 2.0 | Da Milha ao Cuidado - Azul Fidelidade",
  description:
    "Cockpit Analítico de Retenção e Inteligência de Fidelidade — Next.js 15, React 19, Tailwind CSS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-canvas text-text-primary antialiased">
        <BannerSynthetic />
        {children}
      </body>
    </html>
  );
}
