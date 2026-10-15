"use client";

import * as React from "react";
import {
  Bell,
  Search,
  User,
  ShieldCheck,
  ChevronDown,
  Menu,
  Sparkles,
  Database,
  Building2,
  Check,
  HelpCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useHelpSettings } from "@/contexts/help-settings-context";

export interface OperatorProfile {
  id: string;
  name: string;
  role: string;
  avatarColor: string;
}

export const OPERATOR_PROFILES: OperatorProfile[] = [
  {
    id: "operador_crm",
    name: "Carolina Silva",
    role: "Analista de Retenção CRM (HITL)",
    avatarColor: "bg-azul-action",
  },
  {
    id: "lideranca_fidelidade",
    name: "Rodrigo Mendes",
    role: "Diretoria de Fidelidade & Parcerias",
    avatarColor: "bg-azul-deep",
  },
  {
    id: "gerente_contas",
    name: "Mariana Alencar",
    role: "Gerente de Contas Diamante Unique",
    avatarColor: "bg-magenta-cta",
  },
  {
    id: "auditor_lgpd",
    name: "Fernando Bastos",
    role: "Auditor de Ética Algorítmica & LGPD",
    avatarColor: "bg-emerald-600",
  },
];

interface HeaderProps {
  onOpenCommand?: () => void;
  onMobileToggle?: () => void;
  currentProfile?: OperatorProfile;
  onProfileChange?: (profile: OperatorProfile) => void;
}

export function Header({
  onOpenCommand,
  onMobileToggle,
  currentProfile = OPERATOR_PROFILES[0],
  onProfileChange,
}: HeaderProps) {
  const [profileDropdownOpen, setProfileDropdownOpen] = React.useState(false);
  const [selectedProfile, setSelectedProfile] = React.useState<OperatorProfile>(currentProfile);
  const { showTooltips, toggleTooltips } = useHelpSettings();

  const handleSelectProfile = (profile: OperatorProfile) => {
    setSelectedProfile(profile);
    if (onProfileChange) {
      onProfileChange(profile);
    }
    setProfileDropdownOpen(false);
  };

  return (
    <header className="sticky top-0 z-20 flex flex-col border-b border-border-subtle bg-surface shadow-xs">
      {/* Faixa Dourada / Acento Institucional Azul */}
      <div className="h-1 w-full bg-gradient-to-r from-azul-navy via-azul-action to-lime-campaign" />

      <div className="flex h-14 items-center justify-between px-4 sm:px-6">
        {/* Left: Mobile trigger & Context title */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-text-primary"
            onClick={onMobileToggle}
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

          <Badge variant="outline" className="hidden lg:inline-flex items-center gap-1 text-[11px] font-mono bg-muted/60 text-azul-navy">
            <Database className="h-3 w-3 text-azul-action" />
            50.000 Registros Parquet
          </Badge>
        </div>

        {/* Center / Right: Quick Search + Operator Profile + Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Quick search button */}
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenCommand}
            className="h-8 gap-2 border-border-subtle bg-muted/40 text-xs text-text-secondary hover:bg-muted hover:text-azul-navy cursor-pointer"
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
            title={showTooltips ? "Desativar explicações do dicionário de termos" : "Ativar explicações do dicionário de termos"}
            className={cn(
              "h-8 gap-1.5 border-border-subtle text-xs transition-colors cursor-pointer",
              showTooltips
                ? "bg-accent/60 text-azul-action border-azul-action/40 hover:bg-accent"
                : "bg-muted/30 text-text-muted hover:text-text-primary hover:bg-muted"
            )}
          >
            <HelpCircle className={cn("h-3.5 w-3.5", showTooltips ? "text-azul-action" : "text-text-muted")} />
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

          {/* Notification Indicator */}
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-text-secondary hover:text-azul-navy hover:bg-muted"
              title="Notificações operacionais"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-magenta-cta" />
            </Button>
          </div>

          {/* Profile Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              className="flex items-center gap-2 rounded-lg border border-border-subtle bg-surface p-1.5 text-left text-xs transition-colors hover:bg-muted/50 cursor-pointer"
            >
              <div
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-full text-white font-bold text-xs shadow-xs",
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
              <ChevronDown className="h-3.5 w-3.5 text-text-muted" />
            </button>

            {profileDropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setProfileDropdownOpen(false)}
                />
                <div className="absolute right-0 top-full mt-1.5 z-50 w-72 rounded-lg border border-border-subtle bg-surface p-2 shadow-xl animate-in fade-in zoom-in-95">
                  <div className="px-2 py-1.5 border-b border-border-subtle mb-1">
                    <p className="text-xs font-bold text-azul-navy">Perfil do Operador (RBAC)</p>
                    <p className="text-[10px] text-text-secondary">
                      Alterna o contexto de autorização e assinatura HITL
                    </p>
                  </div>

                  <div className="space-y-1">
                    {OPERATOR_PROFILES.map((profile) => (
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
