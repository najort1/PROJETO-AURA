"use client";

import * as React from "react";
import { HelpCircle } from "lucide-react";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import type { ShapFactorTranslated } from "@/types/analytics";

interface ShapWaterfallProps {
  factors: ShapFactorTranslated[];
  baseValue?: number;
  predictedValue?: number;
  metricLabel?: string;
}

interface WaterfallItem {
  label: string;
  shapValue: number;
  observedValue?: number | string;
  isResidual?: boolean;
  tooltipText: string;
}

export function ShapWaterfall({
  factors,
  baseValue = 791.09,
  predictedValue,
  metricLabel = "Impacto no CLV (BRL)",
}: ShapWaterfallProps) {
  if (!factors || factors.length === 0) {
    return (
      <div className="h-60 flex items-center justify-center text-xs text-text-muted">
        Nenhum fator SHAP disponível.
      </div>
    );
  }

  // Soma dos Top fatores
  const topFactorsSum = factors.reduce((acc, f) => acc + f.shap_value, 0);

  // Barra residual calculada: predictedValue - (baseValue + topFactorsSum)
  const residual =
    predictedValue !== undefined
      ? predictedValue - (baseValue + topFactorsSum)
      : null;

  const items: WaterfallItem[] = factors.map((factor) => {
    const isPos = factor.shap_value >= 0;
    return {
      label: factor.human_label,
      shapValue: factor.shap_value,
      observedValue: factor.feature_value,
      isResidual: false,
      tooltipText: `Fator: ${factor.human_label} | Impacto líquido: ${
        isPos ? "+" : ""
      }R$ ${factor.shap_value.toFixed(2)} no CLV previsto${
        factor.feature_value !== undefined
          ? ` (Valor observado: ${String(factor.feature_value)})`
          : ""
      }`,
    };
  });

  if (residual !== null) {
    const isResPos = residual >= 0;
    items.push({
      label: "Outros Fatores do Modelo (Resíduo)",
      shapValue: residual,
      observedValue: undefined,
      isResidual: true,
      tooltipText: `Soma residual das demais variáveis do modelo LightGBM para fechamento exato da predição: ${
        isResPos ? "+" : ""
      }R$ ${residual.toFixed(2)}`,
    });
  }

  const maxAbsValue = Math.max(
    ...items.map((item) => Math.abs(item.shapValue)),
    1
  );

  return (
    <div className="w-full space-y-4">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between text-xs border-b border-border-subtle pb-2">
        <span className="font-bold text-azul-navy uppercase tracking-wider text-[11px]">
          Explicabilidade Local SHAP ({metricLabel})
        </span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 font-medium text-text-secondary">
            <span className="h-2.5 w-2.5 rounded-full bg-azul-action" /> Eleva Valor (+)
          </span>
          <span className="flex items-center gap-1 font-medium text-text-secondary">
            <span className="h-2.5 w-2.5 rounded-full bg-magenta-cta" /> Reduz Valor (-)
          </span>
        </div>
      </div>

      {/* Waterfall Rows */}
      <div className="space-y-3 font-sans">
        {items.map((item, index) => {
          const isPositive = item.shapValue >= 0;
          const widthPct = Math.min((Math.abs(item.shapValue) / maxAbsValue) * 45, 45);

          return (
            <div key={index} className="flex flex-col gap-1 text-xs group">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span
                    className={`font-medium ${
                      item.isResidual
                        ? "text-text-secondary italic"
                        : "text-text-primary"
                    }`}
                  >
                    {item.label}
                  </span>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        aria-label={`Detalhes do fator ${item.label}`}
                        className="text-text-muted hover:text-azul-action transition-colors cursor-help p-0.5 rounded focus:outline-none"
                      >
                        <HelpCircle className="h-3 w-3" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-xs text-xs">
                      {item.tooltipText}
                    </TooltipContent>
                  </Tooltip>
                </div>

                <span className="font-mono font-bold">
                  <span
                    className={
                      isPositive ? "text-azul-action" : "text-magenta-text"
                    }
                  >
                    {isPositive ? "+" : ""}
                    {item.shapValue.toFixed(2)}
                  </span>
                  {item.observedValue !== undefined && (
                    <span className="text-text-muted ml-1.5 font-normal">
                      (valor: {String(item.observedValue)})
                    </span>
                  )}
                </span>
              </div>

              {/* Bidirectional Bar Centered */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <div
                    tabIndex={0}
                    role="img"
                    aria-label={item.tooltipText}
                    className="relative h-4 w-full bg-muted/40 rounded-full flex items-center overflow-hidden cursor-help focus:outline-none focus:ring-1 focus:ring-azul-action/40"
                  >
                    {/* Center line */}
                    <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-border-dark z-10" />

                    {isPositive ? (
                      <div
                        className={`absolute left-1/2 h-full rounded-r-full transition-all duration-300 ${
                          item.isResidual
                            ? "bg-azul-action/80"
                            : "bg-azul-action"
                        }`}
                        style={{ width: `${widthPct}%` }}
                      />
                    ) : (
                      <div
                        className={`absolute h-full rounded-l-full transition-all duration-300 ${
                          item.isResidual
                            ? "bg-magenta-cta/80"
                            : "bg-magenta-cta"
                        }`}
                        style={{
                          right: "50%",
                          width: `${widthPct}%`,
                        }}
                      />
                    )}
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs text-xs">
                  {item.tooltipText}
                </TooltipContent>
              </Tooltip>
            </div>
          );
        })}
      </div>

      {/* Base & Prediction Footnote */}
      <div className="rounded-md bg-muted/60 p-3 text-[11px] text-text-secondary font-mono space-y-1.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span>
            Valor Base Global E[f(x)]: <strong>R$ {baseValue.toFixed(2)}</strong>
          </span>
          {predictedValue !== undefined && (
            <span className="font-bold text-azul-navy">
              Predição Final f(x): R$ {predictedValue.toFixed(2)}
            </span>
          )}
        </div>
        {predictedValue !== undefined && residual !== null && (
          <div className="text-[10px] text-text-muted border-t border-border-subtle/60 pt-1.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <span>
              Fechamento Aritmético: R$ {baseValue.toFixed(2)} + Fatores Top:{" "}
              {topFactorsSum >= 0 ? "+" : ""}
              {topFactorsSum.toFixed(2)} + Resíduo: {residual >= 0 ? "+" : ""}
              {residual.toFixed(2)} ={" "}
              <strong className="text-azul-navy">
                R$ {predictedValue.toFixed(2)}
              </strong>
            </span>
            <span className="text-emerald-700 font-semibold font-sans">
              Balanço 100% Calibrado
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
