import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="pt-BR" className="h-full overflow-hidden">
      <body className="h-full min-h-screen flex flex-col overflow-hidden bg-canvas text-text-primary antialiased">
        {children}
      </body>
    </html>
  );
}
