"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import dynamic from "next/dynamic";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { BannerSynthetic } from "@/components/branding/banner-synthetic";
import { HelpSettingsProvider } from "@/contexts/help-settings-context";
import { TooltipProvider } from "@/components/ui/tooltip";
import { OperatorProvider } from "@/components/layout/operator-context";
import { useKeySequence } from "@/hooks/use-key-sequence";

const CommandMenu = dynamic(
  () => import("@/components/search/command-menu").then((mod) => mod.CommandMenu),
  { ssr: false }
);

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [commandOpen, setCommandOpen] = React.useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false);

  // Hook global de atalhos de sequência G X (P0-1)
  useKeySequence();

  return (
    <OperatorProvider>
      <HelpSettingsProvider>
        <TooltipProvider delayDuration={150} skipDelayDuration={300}>
          <div className="flex flex-1 h-full min-h-0 overflow-hidden bg-canvas">
            {/* Desktop Sidebar */}
            <Sidebar
              onOpenCommand={() => setCommandOpen(true)}
              className="hidden md:flex h-full shrink-0"
            />

            {/* Mobile Sidebar Drawer com Radix Dialog (focus trap + Escape) (P3-2) */}
            <DialogPrimitive.Root open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
              <DialogPrimitive.Portal>
                <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs md:hidden" />
                <DialogPrimitive.Content
                  className="fixed inset-y-0 left-0 z-50 flex h-full w-64 flex-col border-r border-slate-800 bg-[#07243D] shadow-2xl focus:outline-none md:hidden animate-in slide-in-from-left duration-200"
                  aria-describedby={undefined}
                >
                  <DialogPrimitive.Title className="sr-only">
                    Menu Principal de Navegação
                  </DialogPrimitive.Title>
                  <Sidebar
                    onOpenCommand={() => {
                      setMobileSidebarOpen(false);
                      setCommandOpen(true);
                    }}
                    onNavigate={() => setMobileSidebarOpen(false)}
                    isMobile
                    className="flex h-full w-full border-r-0 shadow-none"
                  />
                </DialogPrimitive.Content>
              </DialogPrimitive.Portal>
            </DialogPrimitive.Root>

            {/* Main Workspace com contenção vertical estrita (B7) */}
            <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
              <div className="shrink-0">
                <BannerSynthetic />
              </div>
              <Header
                onOpenCommand={() => setCommandOpen(true)}
                onMobileToggle={() => setMobileSidebarOpen(!mobileSidebarOpen)}
              />

              <main className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-6 lg:p-8">
                <div className="mx-auto max-w-7xl">
                  {children}
                </div>
              </main>
            </div>

            {/* Global Command Palette */}
            {/* Suspense boundary para o dynamic import com ssr:false:
                evita o bailout de SSR "Bail out to client-side rendering: next/dynamic"
                surfacing como 500 em requests não-hidratados (C3) */}
            <React.Suspense fallback={null}>
              <CommandMenu open={commandOpen} onOpenChange={setCommandOpen} />
            </React.Suspense>
          </div>
        </TooltipProvider>
      </HelpSettingsProvider>
    </OperatorProvider>
  );
}
