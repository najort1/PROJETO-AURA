"use client";

import * as React from "react";
import type { ShapFactorTranslated } from "@/types/analytics";

interface ShapWaterfallProps {
  factors: ShapFactorTranslated[];
  baseValue?: number;
  predictedValue?: number;
  metricLabel?: string;
}

export function ShapWaterfall({
  factors,
  baseValue = 791.09,
  predictedValue,
  metricLabel = "Impacto no CLV (BRL)",
}: ShapWaterfallProps) {
  if (!factors || factors.length === 0) {
    return <div className="h-60 flex items-center justify-center text-xs text-text-muted">Nenhum fator SHAP disponível.</div>;
  }

  const maxAbsValue = Math.max(...factors.map((f) => Math.abs(f.shap_value)), 1);

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
        {factors.map((factor, index) => {
          const isPositive = factor.shap_value >= 0;
          const widthPct = Math.min((Math.abs(factor.shap_value) / maxAbsValue) * 45, 45);

          return (
            <div key={index} className="flex flex-col gap-1 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-medium text-text-primary">
                  {factor.human_label}
                </span>
                <span className="font-mono font-bold">
                  <span className={isPositive ? "text-azul-action" : "text-magenta-cta"}>
                    {isPositive ? "+" : ""}
                    {factor.shap_value.toFixed(2)}
                  </span>
                  {factor.feature_value !== undefined && (
                    <span className="text-text-muted ml-1.5 font-normal">
                      (valor: {String(factor.feature_value)})
                    </span>
                  )}
                </span>
              </div>

              {/* Bidirectional Bar Centered */}
              <div className="relative h-4 w-full bg-muted/40 rounded-full flex items-center overflow-hidden">
                {/* Center line */}
                <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-border-dark z-10" />

                {isPositive ? (
                  <div
                    className="absolute left-1/2 h-full rounded-r-full bg-azul-action transition-all duration-300"
                    style={{ width: `${widthPct}%` }}
                  />
                ) : (
                  <div
                    className="absolute h-full rounded-l-full bg-magenta-cta transition-all duration-300"
                    style={{
                      right: "50%",
                      width: `${widthPct}%`,
                    }}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Base & Prediction Footnote */}
      <div className="rounded-md bg-muted/60 p-2.5 text-[11px] text-text-secondary flex items-center justify-between font-mono">
        <span>Valor Base Global E[f(x)]: R$ {baseValue.toFixed(2)}</span>
        {predictedValue !== undefined && (
          <span className="font-bold text-azul-navy">
            Predição Final f(x): R$ {predictedValue.toFixed(2)}
          </span>
        )}
      </div>
    </div>
  );
}
