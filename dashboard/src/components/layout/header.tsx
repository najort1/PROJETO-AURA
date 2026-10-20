"use client";

import * as React from "react";
import Link from "next/link";
import {
  Bell,
  Search,
  ShieldCheck,
  ChevronDown,
  Menu,
  Check,
  HelpCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useHelpSettings } from "@/contexts/help-settings-context";
import {
  OperatorProfile,
  OPERATOR_PROFILES,
  useOperator,
} from "@/components/layout/operator-context";

export type { OperatorProfile };
export { OPERATOR_PROFILES };

interface HeaderProps {
  onOpenCommand?: () => void;
  onMobileToggle?: () => void;
  currentProfile?: OperatorProfile;
  onProfileChange?: (profile: OperatorProfile) => void;
}

interface PendingRecommendationItem {
  customer_id: string;
  action_name: string;
  confidence: number;
}

export function Header({
  onOpenCommand,
  onMobileToggle,
  currentProfile: propProfile,
  onProfileChange: propOnProfileChange,
}: HeaderProps) {
  const operator = useOperator();
  const selectedProfile = propProfile || operator.currentProfile;

  const [profileDropdownOpen, setProfileDropdownOpen] = React.useState(false);
  const [notificationsOpen, setNotificationsOpen] = React.useState(false);
  const [pendingCount, setPendingCount] = React.useState(0);
  const [pendingItems, setPendingItems] = React.useState<PendingRecommendationItem[]>([]);

  const { showTooltips, toggleTooltips } = useHelpSettings();

  // Consulta do endpoint real de recomendações pendentes de revisão humana (P2-3)
  React.useEffect(() => {
    let active = true;

    async function loadHitlPending() {
      try {
        const res = await fetch("/api/agent/recommendations?human_review=true&page_size=5");
        if (!res.ok) throw new Error("Falha ao buscar recomendações HITL");
        const json = await res.json();
        if (active) {
          const total = typeof json.total === "number" ? json.total : (json.data?.length ?? 0);
          setPendingCount(total);
          setPendingItems(
            (json.data || []).map((item: any) => ({
              customer_id: item.customer_id,
              action_name: item.action_name,
              confidence: item.confidence,
            }))
          );
        }
      } catch (err) {
        if (active) {
          setPendingCount(0);
          setPendingItems([]);
        }
      }
    }

    loadHitlPending();
    return () => {
      active = false;
    };
  }, []);

  const handleSelectProfile = (profile: OperatorProfile) => {
    operator.setProfile(profile);
    if (propOnProfileChange) {
      propOnProfileChange(profile);
    }
    setProfileDropdownOpen(false);
  };

  return (
    <header className="sticky top-0 z-20 flex flex-col border-b border-border-subtle bg-surface shadow-xs shrink-0">
      {/* Faixa Dourada / Acento Institucional Azul */}
      <div className="h-1 w-full bg-gradient-to-r from-azul-navy via-azul-action to-lime-campaign" />

      <div className="flex h-14 items-center justify-between px-3 sm:px-6">
        {/* Left: Mobile trigger & Context title */}
        <div className="flex items-center gap-2 sm:gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-text-primary"
            onClick={onMobileToggle}
            aria-label="Abrir menu lateral"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <div className="hidden sm:flex items-center gap-2">
            <span className="font-bold text-azul-navy tracking-tight text-sm">
              PROJETO AURA 2.0
            </span>
            <span className="text-border-dark">/</span>
            <span className="text-xs text-text-secondary font-medium">
              Cockpit de Inteligência & Retenção
            </span>
          </div>
        </div>

        {/* Center / Right: Quick Search + Operator Profile + Actions */}
        <div className="flex items-center gap-1.5 sm:gap-3">
          {/* Quick search button */}
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenCommand}
            className="h-8 gap-2 border-border-subtle bg-muted/40 text-xs text-text-secondary hover:bg-muted hover:text-azul-navy cursor-pointer"
            aria-label="Abrir busca rápida e comandos"
          >
            <Search className="h-3.5 w-3.5 text-azul-action" />
            <span className="hidden sm:inline">Comandos & Busca</span>
            <kbd className="hidden sm:inline-block rounded border border-border-dark bg-surface px-1.5 py-0.2 font-mono text-[10px] text-text-muted">
              ⌘K
            </kbd>
          </Button>

          {/* Dicionário Canônico ON / OFF Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={toggleTooltips}
            title={
              showTooltips
                ? "Desativar explicações do dicionário de termos"
                : "Ativar explicações do dicionário de termos"
            }
            className={cn(
              "h-8 gap-1.5 border-border-subtle text-xs transition-colors cursor-pointer",
              showTooltips
                ? "bg-accent/60 text-azul-action border-azul-action/40 hover:bg-accent"
                : "bg-muted/30 text-text-muted hover:text-text-primary hover:bg-muted"
            )}
          >
            <HelpCircle
              className={cn("h-3.5 w-3.5", showTooltips ? "text-azul-action" : "text-text-muted")}
            />
            <span className="hidden sm:inline font-medium">
              Dicionário {showTooltips ? "ON" : "OFF"}
            </span>
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full shrink-0",
                showTooltips ? "bg-emerald-500" : "bg-text-muted"
              )}
            />
          </Button>

          {/* Notification Indicator com Popover de Pendências HITL (P2-3) */}
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                setNotificationsOpen(!notificationsOpen);
                setProfileDropdownOpen(false);
              }}
              className={cn(
                "relative h-8 w-8 text-text-secondary hover:text-azul-navy hover:bg-muted cursor-pointer",
                notificationsOpen && "bg-muted text-azul-navy"
              )}
              title={
                pendingCount > 0
                  ? `${pendingCount} pendência(s) de revisão humana (HITL)`
                  : "Notificações operacionais (Nenhuma pendência)"
              }
              aria-label={
                pendingCount > 0
                  ? `Notificações: ${pendingCount} casos aguardando revisão humana`
                  : "Notificações: nenhuma pendência"
              }
            >
              <Bell className="h-4 w-4" />
              {pendingCount > 0 && (
                <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-magenta-text ring-2 ring-surface" />
              )}
            </Button>

            {notificationsOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setNotificationsOpen(false)}
                />
                <div className="absolute right-0 top-full mt-1.5 z-50 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-border-subtle bg-surface p-3 shadow-xl animate-in fade-in zoom-in-95">
                  <div className="flex items-center justify-between border-b border-border-subtle pb-2 mb-2">
                    <div className="flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4 text-azul-action" />
                      <span className="text-xs font-bold text-azul-navy">
                        Revisão Humana (HITL)
                      </span>
                    </div>
                    {pendingCount > 0 ? (
                      <span className="rounded-full bg-magenta-text/10 text-magenta-text font-bold text-[10px] px-2 py-0.5">
                        {pendingCount} pendente{pendingCount > 1 ? "s" : ""}
                      </span>
                    ) : (
                      <span className="rounded-full bg-emerald-50 text-emerald-700 font-semibold text-[10px] px-2 py-0.5">
                        Conforme
                      </span>
                    )}
                  </div>

                  {pendingCount > 0 ? (
                    <div className="space-y-2 mb-2">
                      <p className="text-[11px] text-text-secondary leading-snug">
                        Casos recomendados pela IA que exigem aprovação nominal do operador:
                      </p>
                      <div className="divide-y divide-border-subtle/60 rounded-lg border border-border-subtle bg-muted/20">
                        {pendingItems.map((item) => (
                          <Link
                            key={item.customer_id}
                            href={`/agente?customer_id=${encodeURIComponent(item.customer_id)}&filter=hitl`}
                            onClick={() => setNotificationsOpen(false)}
                            className="flex items-center justify-between p-2 text-xs hover:bg-muted/60 transition-colors"
                          >
                            <div className="flex flex-col truncate">
                              <span className="font-mono font-bold text-azul-navy">
                                {item.customer_id}
                              </span>
                              <span className="text-[10px] text-text-secondary truncate">
                                {item.action_name}
                              </span>
                            </div>
                            <span className="text-[10px] font-mono text-azul-action font-semibold ml-2 shrink-0">
                              Revisar →
                            </span>
                          </Link>
                        ))}
                      </div>
                      <Link
                        href="/agente?filter=hitl"
                        onClick={() => setNotificationsOpen(false)}
                        className="block text-center rounded-md bg-accent/70 hover:bg-accent p-1.5 text-xs font-semibold text-azul-action transition-colors"
                      >
                        Ver todas no Kanban do Agente ({pendingCount}) →
                      </Link>
                    </div>
                  ) : (
                    <div className="py-4 text-center space-y-1.5">
                      <div className="mx-auto flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                        <Check className="h-4 w-4" />
                      </div>
                      <p className="text-xs font-semibold text-azul-navy">
                        Nenhuma pendência HITL
                      </p>
                      <p className="text-[11px] text-text-muted max-w-[220px] mx-auto">
                        Todas as recomendações do cockpit foram revisadas ou homologadas pelo operador.
                      </p>
                    </div>
                  )}

                  <div className="border-t border-border-subtle pt-2 text-[10px] text-text-muted flex items-center justify-between">
                    <span>Audit Trail: Ativo</span>
                    <span className="font-mono text-emerald-600">decisions.jsonl</span>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Profile Selector Dropdown (P2-4: Compacto no mobile <640px) */}
          <div className="relative">
            <button
              onClick={() => {
                setProfileDropdownOpen(!profileDropdownOpen);
                setNotificationsOpen(false);
              }}
              className="flex items-center gap-1.5 sm:gap-2 rounded-lg border border-border-subtle bg-surface p-1 sm:p-1.5 text-left text-xs transition-colors hover:bg-muted/50 cursor-pointer shrink-0"
              aria-label={`Perfil do Operador: ${selectedProfile.name} (${selectedProfile.role})`}
              title={`${selectedProfile.name} • ${selectedProfile.role}`}
            >
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-white font-bold text-xs shadow-xs",
                  selectedProfile.avatarColor
                )}
              >
                {selectedProfile.name.charAt(0)}
              </div>
              <div className="hidden md:flex flex-col text-left leading-tight">
                <span className="font-semibold text-azul-navy">{selectedProfile.name}</span>
                <span className="text-[10px] text-text-muted truncate max-w-[130px]">
                  {selectedProfile.role}
                </span>
              </div>
              <ChevronDown className="h-3.5 w-3.5 text-text-muted shrink-0" />
            </button>

            {profileDropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setProfileDropdownOpen(false)}
                />
                <div className="absolute right-0 top-full mt-1.5 z-50 w-72 max-w-[calc(100vw-2rem)] rounded-lg border border-border-subtle bg-surface p-2 shadow-xl animate-in fade-in zoom-in-95">
                  <div className="px-2 py-1.5 border-b border-border-subtle mb-1">
                    <p className="text-xs font-bold text-azul-navy">Perfil do Operador (RBAC)</p>
                    <p className="text-[10px] text-text-secondary">
                      Alterna o contexto de autorização e assinatura HITL
                    </p>
                  </div>

                  <div className="space-y-1">
                    {OPERATOR_PROFILES.map((profile: OperatorProfile) => (
                      <button
                        key={profile.id}
                        onClick={() => handleSelectProfile(profile)}
                        className={cn(
                          "flex w-full items-center justify-between rounded-md px-2.5 py-2 text-left text-xs transition-colors cursor-pointer",
                          selectedProfile.id === profile.id
                            ? "bg-accent text-azul-navy font-semibold"
                            : "hover:bg-muted text-text-primary"
                        )}
                      >
                        <div className="flex items-center gap-2.5 overflow-hidden">
                          <div
                            className={cn(
                              "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-white font-bold text-[11px]",
                              profile.avatarColor
                            )}
                          >
                            {profile.name.charAt(0)}
                          </div>
                          <div className="flex flex-col truncate">
                            <span className="truncate">{profile.name}</span>
                            <span className="text-[10px] text-text-muted truncate">
                              {profile.role}
                            </span>
                          </div>
                        </div>
                        {selectedProfile.id === profile.id && (
                          <Check className="h-4 w-4 shrink-0 text-azul-action" />
                        )}
                      </button>
                    ))}
                  </div>

                  <div className="mt-2 border-t border-border-subtle pt-2 px-2 text-[10px] text-text-muted flex items-center justify-between">
                    <span>Audit Trail: Ativo</span>
                    <span className="font-mono text-emerald-600">decisions.jsonl</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
