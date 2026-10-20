"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  UserCheck,
  Bot,
  AlertOctagon,
  Calculator,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Search,
  Sparkles,
  Plane,
  TableProperties,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  description: string;
}

export interface NavigationGroup {
  id: string;
  title: string;
  items: NavigationItem[];
}

export const navigationGroups: NavigationGroup[] = [
  {
    id: "estrategico",
    title: "Estratégico",
    items: [
      {
        name: "Visão da Carteira",
        href: "/carteira",
        icon: LayoutDashboard,
        description: "VaR, CLV e Gini",
      },
      {
        name: "Personas",
        href: "/personas",
        icon: Users,
        badge: "6 Grupos",
        description: "Segmentação & Playbook",
      },
      {
        name: "Mapa de Atritos",
        href: "/atritos",
        icon: AlertOctagon,
        badge: "7 Aspectos",
        description: "Sentimento Semestral",
      },
    ],
  },
  {
    id: "operacional",
    title: "Operacional",
    items: [
      {
        name: "Base de Clientes",
        href: "/clientes",
        icon: TableProperties,
        description: "Tabela Completa & Filtros",
      },
      {
        name: "Cliente 360",
        href: "/cliente-360",
        icon: UserCheck,
        description: "SHAP & Linha do Tempo",
      },
      {
        name: "Concierge IA",
        href: "/concierge",
        icon: Sparkles,
        description: "Copilot & Tools em Tempo Real",
      },
    ],
  },
  {
    id: "decisao_governanca",
    title: "Decisão & Governança",
    items: [
      {
        name: "Agente & Retenção",
        href: "/agente",
        icon: Bot,
        badge: "HITL",
        description: "Cockpit NBA & HITL",
      },
      {
        name: "Simulador Financeiro",
        href: "/simulador",
        icon: Calculator,
        badge: "ROI",
        description: "Fórmula ΔReceita Líquida",
      },
      {
        name: "IA Responsável",
        href: "/ia-responsavel",
        icon: ShieldCheck,
        badge: "Regra 4/5",
        description: "Art. 20 LGPD & Auditoria",
      },
    ],
  },
];

export const navigationItems = navigationGroups.flatMap((group) => group.items);

const STORAGE_KEY = "aura_sidebar_collapsed";

interface SidebarProps {
  onOpenCommand?: () => void;
  onNavigate?: () => void;
  className?: string;
  isMobile?: boolean;
}

export function Sidebar({
  onOpenCommand,
  onNavigate,
  className,
  isMobile = false,
}: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  // Persistência do estado collapsed em localStorage (P3-1)
  React.useEffect(() => {
    if (isMobile) return;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved !== null) {
        setCollapsed(saved === "true");
      }
    } catch {
      // Ignorar indisponibilidade de localStorage
    }
  }, [isMobile]);

  const handleToggleCollapse = React.useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        // Ignorar
      }
      return next;
    });
  }, []);

  const isActuallyCollapsed = collapsed && !isMobile;

  return (
    <aside
      className={cn(
        "relative flex flex-col h-full self-stretch border-r border-slate-800 bg-[#07243D] text-slate-200 transition-all duration-300 select-none shadow-xl z-30",
        isActuallyCollapsed ? "w-20" : "w-64",
        className
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 shrink-0 items-center justify-between border-b border-slate-800/80 px-4">
        <Link
          href="/carteira"
          onClick={() => onNavigate?.()}
          className="flex items-center gap-2.5 overflow-hidden"
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-azul-action text-white shadow-md">
            <Plane className="h-5 w-5 transform -rotate-45" />
          </div>
          {!isActuallyCollapsed && (
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5 leading-none">
                <span className="font-bold tracking-tight text-white text-base">AZUL</span>
                <span className="font-light text-azul-primary text-base">FIDELIDADE</span>
              </div>
              <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase mt-0.5">
                AURA 2.0 • COCKPIT
              </span>
            </div>
          )}
        </Link>
        {/* Botão de colapso oculto no modo mobile (P3-2) */}
        {!isMobile && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleToggleCollapse}
            className="h-7 w-7 text-slate-400 hover:text-white hover:bg-slate-800/60 cursor-pointer"
            title={isActuallyCollapsed ? "Expandir Menu" : "Recolher Menu"}
            aria-label={isActuallyCollapsed ? "Expandir Menu" : "Recolher Menu"}
          >
            {isActuallyCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>

      {/* Quick Search / Command Palette Trigger */}
      <div className="p-3 shrink-0">
        <button
          onClick={onOpenCommand}
          className={cn(
            "flex w-full items-center gap-2 rounded-lg border border-slate-700/60 bg-slate-900/60 px-3 py-2 text-xs text-slate-400 shadow-inner transition-colors hover:border-azul-action hover:text-slate-200 cursor-pointer",
            isActuallyCollapsed && "justify-center px-0"
          )}
          title="Busca rápida (Ctrl+K)"
          aria-label="Busca rápida de rotas e clientes"
        >
          <Search className="h-4 w-4 shrink-0 text-azul-action" />
          {!isActuallyCollapsed && (
            <>
              <span className="flex-1 text-left truncate">Buscar clientes, telas...</span>
              <kbd className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-300">
                ⌘K
              </kbd>
            </>
          )}
        </button>
      </div>

      {/* Navigation List — Organizada em 3 grupos semânticos (P2-2) */}
      <nav className="flex-1 min-h-0 space-y-4 overflow-y-auto px-2 py-2">
        {navigationGroups.map((group) => (
          <div key={group.id} className="space-y-1">
            {!isActuallyCollapsed ? (
              <div className="px-3 pt-1 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                {group.title}
              </div>
            ) : (
              <div className="my-1.5 border-t border-slate-800/70" />
            )}

            {group.items.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/" && pathname.startsWith(item.href));
              const Icon = item.icon;

              const linkContent = (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => onNavigate?.()}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                    isActive
                      ? "bg-azul-action text-white shadow-md shadow-azul-action/20 font-semibold"
                      : "text-slate-300 hover:bg-slate-800/80 hover:text-white",
                    isActuallyCollapsed && "justify-center px-0"
                  )}
                >
                  {isActive && (
                    <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-md bg-lime-campaign" />
                  )}
                  <Icon
                    className={cn(
                      "h-5 w-5 shrink-0 transition-transform group-hover:scale-105",
                      isActive
                        ? "text-white"
                        : "text-slate-400 group-hover:text-azul-primary"
                    )}
                  />
                  {!isActuallyCollapsed && (
                    <div className="flex flex-1 items-center justify-between overflow-hidden">
                      <div className="flex flex-col truncate">
                        <span className="truncate leading-tight">{item.name}</span>
                        <span
                          className={cn(
                            "text-[10px] truncate",
                            isActive ? "text-slate-100/90" : "text-slate-400"
                          )}
                        >
                          {item.description}
                        </span>
                      </div>
                      {item.badge && (
                        <span
                          className={cn(
                            "ml-2 rounded-full px-1.5 py-0.5 text-[10px] font-bold tracking-tight shrink-0",
                            isActive
                              ? "bg-white/20 text-white"
                              : "bg-slate-800 text-slate-300"
                          )}
                        >
                          {item.badge}
                        </span>
                      )}
                    </div>
                  )}
                </Link>
              );

              // Itens recolhidos utilizam Radix Tooltip (P3-1)
              if (isActuallyCollapsed) {
                return (
                  <Tooltip key={item.href}>
                    <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                    <TooltipContent
                      side="right"
                      className="flex items-center gap-2 border-slate-700 bg-slate-900 text-slate-100 shadow-xl"
                    >
                      <span className="font-medium">{item.name}</span>
                      {item.badge && (
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-bold text-slate-300">
                          {item.badge}
                        </span>
                      )}
                    </TooltipContent>
                  </Tooltip>
                );
              }

              return linkContent;
            })}
          </div>
        ))}
      </nav>

      {/* Footer Profile & Status */}
      <div className="border-t border-slate-800/80 p-3 bg-slate-950/40 shrink-0">
        {!isActuallyCollapsed ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                DuckDB / Parquet Ativo
              </span>
              <span className="font-mono text-slate-300">Base Calibrada</span>
            </div>
            <div className="rounded border border-slate-800 bg-slate-900/80 p-2 text-[10px] text-slate-400 leading-tight">
              <span className="font-semibold text-slate-300">PROJETO AURA 2.0</span>
              <p className="mt-0.5 text-slate-400">Arquitetura Next.js 15 • Conforme Art. 20 LGPD</p>
            </div>
          </div>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex justify-center cursor-help py-1">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse motion-reduce:animate-none" />
              </div>
            </TooltipTrigger>
            <TooltipContent
              side="right"
              className="border-slate-700 bg-slate-900 text-slate-200 text-xs"
            >
              DuckDB / Parquet Ativo
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </aside>
  );
}
