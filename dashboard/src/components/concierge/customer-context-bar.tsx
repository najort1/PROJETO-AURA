"use client";

import * as React from "react";
import { Zap, Search, Plane, BookOpen, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PRESET_CUSTOMERS, type PresetCustomer } from "@/types/concierge";

interface CustomerContextBarProps {
  selectedCustomerId: string;
  onSelectCustomer: (customerId: string) => void;
  onQuickAction: (prompt: string, actionType?: "chat" | "evaluate") => void;
  isLoading: boolean;
  isOnline?: boolean;
  customers?: PresetCustomer[];
}

export function CustomerContextBar({
  selectedCustomerId,
  onSelectCustomer,
  onQuickAction,
  isLoading,
  isOnline = true,
  customers = PRESET_CUSTOMERS,
}: CustomerContextBarProps) {
  const isActionDisabled = isLoading || !isOnline;

  return (
    <div className="rounded-xl border border-border-subtle bg-surface p-2.5 sm:p-3 space-y-2.5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap min-w-0 flex-1 sm:flex-initial">
          <label
            htmlFor="customer-context-select"
            className="text-xs font-bold text-azul-navy uppercase tracking-wider shrink-0"
          >
            Cliente Ativo:
          </label>
          <select
            id="customer-context-select"
            value={selectedCustomerId}
            onChange={(e) => onSelectCustomer(e.target.value)}
            disabled={isLoading}
            aria-label="Selecionar cliente para contexto ativo no chat"
            className="text-xs font-mono font-semibold bg-muted/50 border border-border-subtle rounded-lg px-2.5 py-1 text-azul-navy focus:outline-none focus:ring-1 focus:ring-azul-action cursor-pointer disabled:opacity-60 min-w-0 max-w-full truncate w-full sm:w-auto"
          >
            <option value="">Nenhum (Contexto Geral)</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() =>
              onQuickAction(
                selectedCustomerId
                  ? `Avalie completamente o cliente ${selectedCustomerId}, consulte o perfil 360, atritos e tome as ações necessárias de retenção.`
                  : "Execute uma varredura analítica e avalie os clientes em maior risco de evasão na carteira.",
                "evaluate"
              )
            }
            disabled={isActionDisabled}
            title={!isOnline ? "Motor local desconectado — Ação indisponível" : undefined}
            className="text-xs font-semibold h-7 bg-azul-action/10 text-azul-action border-azul-action/30 hover:bg-azul-action/20 cursor-pointer disabled:opacity-40"
            aria-label={`Executar ciclo autônomo completo para ${selectedCustomerId || "carteira geral"}`}
          >
            <Zap className="size-3 mr-1 text-azul-action fill-azul-action" aria-hidden="true" />
            Ciclo Autônomo ({selectedCustomerId || "Geral"})
          </Button>
        </div>
      </div>

      {/* Chips de Ações Rápidas */}
      <div className="flex flex-wrap items-center gap-1.5 pt-1.5 border-t border-border-subtle/60 text-xs">
        <span className="text-[11px] font-semibold text-text-secondary mr-1 shrink-0">
          Sugestões:
        </span>

        <button
          type="button"
          onClick={() =>
            onQuickAction(
              selectedCustomerId
                ? `Consulte a visão 360 do cliente ${selectedCustomerId} e me diga o tier, CLV, risco de churn e os fatores SHAP dominantes.`
                : "Consulte a visão 360 dos clientes em risco na carteira e me informe o tier predominante, CLV e fatores SHAP dominantes."
            )
          }
          disabled={isActionDisabled}
          title={!isOnline ? "Motor local desconectado" : undefined}
          aria-label={
            selectedCustomerId
              ? `Consultar visão 360 e fatores SHAP do cliente ${selectedCustomerId}`
              : "Consultar visão 360 e fatores SHAP gerais da carteira"
          }
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary hover:text-azul-navy text-[11px] font-medium transition-colors border border-border-subtle/50 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Search className="size-2.5 text-azul-action" aria-hidden="true" />
          <span>Visão 360° & SHAP</span>
        </button>

        <button
          type="button"
          onClick={() =>
            onQuickAction(
              selectedCustomerId
                ? `Quais foram os atritos e atrasos de voo recentes enfrentados pelo cliente ${selectedCustomerId}?`
                : "Quais foram os principais atritos operacionais e atrasos de voo recentes registrados na carteira?"
            )
          }
          disabled={isActionDisabled}
          title={!isOnline ? "Motor local desconectado" : undefined}
          aria-label={
            selectedCustomerId
              ? `Consultar histórico de atritos e atrasos do cliente ${selectedCustomerId}`
              : "Consultar principais atritos e atrasos de voos da carteira"
          }
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary hover:text-azul-navy text-[11px] font-medium transition-colors border border-border-subtle/50 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Plane className="size-2.5 text-azul-action" aria-hidden="true" />
          <span>Histórico de Atritos</span>
        </button>

        <button
          type="button"
          onClick={() =>
            onQuickAction(
              `Consulte no regulamento oficial quais são as regras de Resgate Especial e teto de pontos para clientes Diamante e Safira.`
            )
          }
          disabled={isActionDisabled}
          title={!isOnline ? "Motor local desconectado" : undefined}
          aria-label="Consultar regras do regulamento oficial"
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary hover:text-azul-navy text-[11px] font-medium transition-colors border border-border-subtle/50 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <BookOpen className="size-2.5 text-azul-action" aria-hidden="true" />
          <span>Regulamento (RAG)</span>
        </button>

        <button
          type="button"
          onClick={() =>
            onQuickAction(
              `Liste os 5 clientes de maior valor com atrito recente e risco de perda na carteira.`
            )
          }
          disabled={isActionDisabled}
          title={!isOnline ? "Motor local desconectado" : undefined}
          aria-label="Listar 5 clientes em maior risco na carteira"
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary hover:text-azul-navy text-[11px] font-medium transition-colors border border-border-subtle/50 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ShieldAlert className="size-2.5 text-amber-600" aria-hidden="true" />
          <span>Varredura de Risco</span>
        </button>
      </div>
    </div>
  );
}
