"use client";

import * as React from "react";
import type { PersonaVarBarItem } from "@/types/analytics";

interface PersonaVarBarProps {
  items: PersonaVarBarItem[];
}

export function PersonaVarBar({ items }: PersonaVarBarProps) {
  const [hoveredItem, setHoveredItem] = React.useState<PersonaVarBarItem | null>(null);

  if (!items || items.length === 0) {
    return <div className="h-64 flex items-center justify-center text-xs text-text-muted">Carregando barras de personas...</div>;
  }

  const maxVar = Math.max(...items.map((i) => i.var_total), 1);

  return (
    <div
      className="w-full space-y-3"
      role="region"
      aria-label="Gráfico de Barras: Valor em Risco e CLV por Persona Comportamental"
    >
      <div className="flex items-center justify-between text-xs text-text-muted">
        <span>Persona (Ordenado por VaR Total)</span>
        <span>VaR Total (BRL)</span>
      </div>

      <div className="space-y-2.5" role="list">
        {items.map((item) => {
          const widthPct = Math.max((item.var_total / maxVar) * 100, 4);

          return (
            <div
              key={item.persona}
              role="listitem"
              tabIndex={0}
              aria-label={`${item.nome_display}: VaR Total de R$ ${item.var_total.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}, ${item.clientes_count.toLocaleString("pt-BR")} membros, Churn Médio ${(item.churn_medio * 100).toFixed(1)}%`}
              className="group relative cursor-pointer p-1 -m-1 rounded-md transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-azul-action focus-visible:ring-offset-1 motion-reduce:transition-none"
              onMouseEnter={() => setHoveredItem(item)}
              onMouseLeave={() => setHoveredItem(null)}
              onFocus={() => setHoveredItem(item)}
              onBlur={() => setHoveredItem(null)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setHoveredItem(item);
                }
              }}
            >
              <div className="flex items-center justify-between text-xs font-medium mb-1">
                <span className="text-azul-navy flex items-center gap-1.5 font-semibold">
                  <span
                    className="h-2.5 w-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: item.cor }}
                  />
                  {item.nome_display}
                </span>
                <span className="font-mono font-bold text-azul-navy">
                  R$ {item.var_total.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>

              <div className="h-4 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300 group-hover:brightness-110 motion-reduce:transition-none"
                  style={{
                    width: `${widthPct}%`,
                    backgroundColor: item.cor,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Área Reservada com min-h fixo para eliminar CLS (P1-8) */}
      <div className="min-h-[88px] rounded-lg border border-border-subtle bg-surface p-3 shadow-xs text-xs flex flex-col justify-center transition-colors">
        {hoveredItem ? (
          <div className="space-y-1 w-full animate-in fade-in duration-150">
            <div className="flex items-center justify-between border-b border-border-subtle pb-1">
              <span className="font-bold text-azul-navy flex items-center gap-1.5">
                <span
                  className="h-2 w-2 rounded-full shrink-0"
                  style={{ backgroundColor: hoveredItem.cor }}
                />
                {hoveredItem.nome_display}
              </span>
              <span className="font-mono text-xs text-text-muted">
                {hoveredItem.clientes_count.toLocaleString("pt-BR")} membros
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-[11px]">
              <div>
                <span className="text-text-muted block font-sans">VaR Total:</span>
                <span className="font-bold text-magenta-text">
                  R$ {hoveredItem.var_total.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}
                </span>
              </div>
              <div>
                <span className="text-text-muted block font-sans">CLV Total:</span>
                <span className="font-bold text-azul-action">
                  R$ {hoveredItem.clv_total.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}
                </span>
              </div>
              <div>
                <span className="text-text-muted block font-sans">Churn Médio:</span>
                <span className="font-bold text-text-primary">
                  {(hoveredItem.churn_medio * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center text-text-muted text-xs font-medium py-2">
            Passe o cursor ou navegue com Tab sobre uma barra para detalhar métricas
          </div>
        )}
      </div>
    </div>
  );
}
