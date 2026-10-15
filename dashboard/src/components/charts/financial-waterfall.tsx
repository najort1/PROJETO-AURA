"use client";

import * as React from "react";

interface FinancialWaterfallProps {
  custoTotal: number;
  receitaSalva: number;
  receitaLiquida: number;
  roiPct: number;
}

export function FinancialWaterfall({
  custoTotal,
  receitaSalva,
  receitaLiquida,
  roiPct,
}: FinancialWaterfallProps) {
  const maxValue = Math.max(custoTotal, receitaSalva, Math.abs(receitaLiquida), 1);

  return (
    <div className="w-full space-y-4 font-sans">
      <div className="flex items-center justify-between text-xs border-b border-border-subtle pb-2">
        <span className="font-bold text-azul-navy uppercase tracking-wider text-[11px]">
          Decomposição do Retorno Econômico Líquido
        </span>
        <span className="font-mono text-xs font-semibold text-text-secondary">
          ROI: <span className={roiPct >= 0 ? "text-emerald-600" : "text-magenta-cta"}>{roiPct.toFixed(1)}%</span>
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        {/* Custo Total */}
        <div className="flex flex-col items-center gap-2">
          <span className="text-xs font-semibold text-text-secondary">Investimento / Custo</span>
          <div className="h-36 w-full flex items-end justify-center">
            <div
              className="w-16 rounded-t-md bg-magenta-cta transition-all duration-300 shadow-sm"
              style={{ height: `${Math.max((custoTotal / maxValue) * 100, 10)}%` }}
            />
          </div>
          <span className="font-mono text-xs font-bold text-magenta-cta">
            -R$ {custoTotal.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>

        {/* Receita Salva */}
        <div className="flex flex-col items-center gap-2">
          <span className="text-xs font-semibold text-text-secondary">Receita Bruta Salva</span>
          <div className="h-36 w-full flex items-end justify-center">
            <div
              className="w-16 rounded-t-md bg-azul-action transition-all duration-300 shadow-sm"
              style={{ height: `${Math.max((receitaSalva / maxValue) * 100, 10)}%` }}
            />
          </div>
          <span className="font-mono text-xs font-bold text-azul-action">
            +R$ {receitaSalva.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>

        {/* ΔReceita Líquida */}
        <div className="flex flex-col items-center gap-2">
          <span className="text-xs font-semibold text-text-secondary">ΔReceita Líquida</span>
          <div className="h-36 w-full flex items-end justify-center">
            <div
              className={`w-16 rounded-t-md transition-all duration-300 shadow-sm ${
                receitaLiquida >= 0 ? "bg-emerald-600" : "bg-magenta-cta/80"
              }`}
              style={{ height: `${Math.max((Math.abs(receitaLiquida) / maxValue) * 100, 10)}%` }}
            />
          </div>
          <span
            className={`font-mono text-xs font-extrabold ${
              receitaLiquida >= 0 ? "text-emerald-700" : "text-magenta-cta"
            }`}
          >
            {receitaLiquida >= 0 ? "+" : ""}
            R$ {receitaLiquida.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      </div>
    </div>
  );
}
