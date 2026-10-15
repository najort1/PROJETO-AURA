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
import { Badge } from "@/components/ui/badge";

export const navigationItems = [
  {
    name: "Visão da Carteira",
    href: "/carteira",
    icon: LayoutDashboard,
    badge: "R$ 8,31M",
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
    name: "Cliente 360",
    href: "/cliente-360",
    icon: UserCheck,
    badge: "50k Base",
    description: "SHAP & Linha do Tempo",
  },
  {
    name: "Base de Clientes",
    href: "/clientes",
    icon: TableProperties,
    badge: "50k Base",
    description: "Tabela Completa & Filtros",
  },
  {
    name: "Concierge IA (Chat)",
    href: "/concierge",
    icon: Sparkles,
    badge: "Ao Vivo",
    description: "Copilot & Tools em Tempo Real",
  },
  {
    name: "Agente & Retenção",
    href: "/agente",
    icon: Bot,
    badge: "Kanban",
    description: "Cockpit NBA & HITL",
  },
  {
    name: "Mapa de Atritos",
    href: "/atritos",
    icon: AlertOctagon,
    badge: "7 Aspectos",
    description: "Sentimento Semestral",
  },
  {
    name: "Simulador Financeiro",
    href: "/simulador",
    icon: Calculator,
    badge: "ROI Real",
    description: "Fórmula ΔReceita Líquida",
  },
  {
    name: "IA Responsável",
    href: "/ia-responsavel",
    icon: ShieldCheck,
    badge: "Regra 4/5",
    description: "Art. 20 LGPD & Auditoria",
  },
];

interface SidebarProps {
  onOpenCommand?: () => void;
  onNavigate?: () => void;
  className?: string;
}

export function Sidebar({ onOpenCommand, onNavigate, className }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-[#07243D] text-slate-200 transition-all duration-300 select-none shadow-xl z-30",
        collapsed ? "w-20" : "w-64",
        className
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between border-b border-slate-800/80 px-4">
        <Link
          href="/carteira"
          onClick={() => onNavigate?.()}
          className="flex items-center gap-2.5 overflow-hidden"
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-azul-action text-white shadow-md">
            <Plane className="h-5 w-5 transform -rotate-45" />
          </div>
          {!collapsed && (
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
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="h-7 w-7 text-slate-400 hover:text-white hover:bg-slate-800/60"
          title={collapsed ? "Expandir Menu" : "Recolher Menu"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Quick Search / Command Palette Trigger */}
      <div className="p-3">
        <button
          onClick={onOpenCommand}
          className={cn(
            "flex w-full items-center gap-2 rounded-lg border border-slate-700/60 bg-slate-900/60 px-3 py-2 text-xs text-slate-400 shadow-inner transition-colors hover:border-azul-action hover:text-slate-200 cursor-pointer",
            collapsed && "justify-center px-0"
          )}
          title="Busca rápida (Ctrl+K)"
        >
          <Search className="h-4 w-4 shrink-0 text-azul-primary" />
          {!collapsed && (
            <>
              <span className="flex-1 text-left">Buscar clientes, telas...</span>
              <kbd className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-300">
                ⌘K
              </kbd>
            </>
          )}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-2">
        {navigationItems.map((item, index) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => onNavigate?.()}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-azul-action text-white shadow-md shadow-azul-action/20 font-semibold"
                  : "text-slate-300 hover:bg-slate-800/80 hover:text-white",
                collapsed && "justify-center px-0"
              )}
              title={collapsed ? `${item.name} (${item.badge})` : undefined}
            >
              {isActive && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-md bg-lime-campaign" />
              )}
              <Icon
                className={cn(
                  "h-5 w-5 shrink-0 transition-transform group-hover:scale-105",
                  isActive ? "text-white" : "text-slate-400 group-hover:text-azul-primary"
                )}
              />
              {!collapsed && (
                <div className="flex flex-1 items-center justify-between overflow-hidden">
                  <div className="flex flex-col truncate">
                    <span className="truncate leading-tight">{item.name}</span>
                    <span
                      className={cn(
                        "text-[10px] truncate",
                        isActive ? "text-slate-100/80" : "text-slate-400"
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
                          : "bg-slate-800 text-slate-400"
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Profile & Status */}
      <div className="border-t border-slate-800/80 p-3 bg-slate-950/40">
        {!collapsed ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                DuckDB / Parquet Ativo
              </span>
              <span className="font-mono text-slate-300">50k Calibrados</span>
            </div>
            <div className="rounded border border-slate-800 bg-slate-900/80 p-2 text-[10px] text-slate-400 leading-tight">
              <span className="font-semibold text-slate-300">PROJETO AURA 2.0</span>
              <p className="mt-0.5 text-slate-400">Arquitetura Next.js 15 • Conforme Art. 20 LGPD</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title="DuckDB / Parquet 50k Ativo">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
          </div>
        )}
      </div>
    </aside>
  );
}
