"use client";

import * as React from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header, OPERATOR_PROFILES, type OperatorProfile } from "@/components/layout/header";
import { CommandMenu } from "@/components/search/command-menu";
import { HelpSettingsProvider } from "@/contexts/help-settings-context";
import { TooltipProvider } from "@/components/ui/tooltip";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [commandOpen, setCommandOpen] = React.useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false);
  const [currentProfile, setCurrentProfile] = React.useState<OperatorProfile>(OPERATOR_PROFILES[0]);

  return (
    <HelpSettingsProvider>
      <TooltipProvider delayDuration={150} skipDelayDuration={300}>
        <div className="flex h-[calc(100vh-33px)] overflow-hidden bg-canvas">
          {/* Desktop Sidebar */}
          <Sidebar
            onOpenCommand={() => setCommandOpen(true)}
            className="hidden md:flex"
          />

          {/* Mobile Sidebar Overlay */}
          {mobileSidebarOpen && (
            <div className="fixed inset-0 z-50 md:hidden flex">
              <div
                className="fixed inset-0 bg-black/50 backdrop-blur-xs"
                onClick={() => setMobileSidebarOpen(false)}
              />
              <Sidebar
                onOpenCommand={() => {
                  setMobileSidebarOpen(false);
                  setCommandOpen(true);
                }}
                onNavigate={() => setMobileSidebarOpen(false)}
                className="relative z-50 flex h-full"
              />
            </div>
          )}

          {/* Main Workspace */}
          <div className="flex flex-1 flex-col overflow-hidden">
            <Header
              onOpenCommand={() => setCommandOpen(true)}
              onMobileToggle={() => setMobileSidebarOpen(!mobileSidebarOpen)}
              currentProfile={currentProfile}
              onProfileChange={setCurrentProfile}
            />

            <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
              <div className="mx-auto max-w-7xl">
                {children}
              </div>
            </main>
          </div>

          {/* Global Command Palette */}
          <CommandMenu open={commandOpen} onOpenChange={setCommandOpen} />
        </div>
      </TooltipProvider>
    </HelpSettingsProvider>
  );
}
