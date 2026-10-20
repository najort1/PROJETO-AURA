"use client";

import * as React from "react";
import type { HistogramBin } from "@/types/analytics";

interface ClvHistogramProps {
  bins: HistogramBin[];
  media: number;
  mediana: number;
}

export function ClvHistogram({ bins, media, mediana }: ClvHistogramProps) {
  const [hoveredIndex, setHoveredIndex] = React.useState<number | null>(null);

  if (!bins || bins.length === 0) {
    return <div className="h-64 flex items-center justify-center text-xs text-text-muted">Carregando histograma...</div>;
  }

  const maxCount = Math.max(...bins.map((b) => b.count), 1);
  const totalCustomers = bins.reduce((acc, b) => acc + b.count, 0);
  const hoveredBin = hoveredIndex !== null ? bins[hoveredIndex] : null;

  // Derivação dos rótulos do eixo X a partir das faixas reais retornadas (P2-15)
  const xLabels = React.useMemo(() => {
    if (!bins || bins.length === 0) return [];
    const stepCount = Math.min(4, bins.length);
    const divisor = stepCount > 1 ? stepCount - 1 : 1;
    const step = Math.floor((bins.length - 1) / divisor);
    const indices: number[] = [];
    for (let i = 0; i < stepCount - 1; i++) {
      indices.push(i * step);
    }
    indices.push(bins.length - 1);

    return indices.map((idx) => {
      const b = bins[idx];
      const isLast = idx === bins.length - 1;
      const text = isLast
        ? `R$ ${b.bin_start.toLocaleString("pt-BR")}+`
        : `R$ ${b.bin_start.toLocaleString("pt-BR")}`;
      return { idx, text };
    });
  }, [bins]);

  return (
    <div
      className="w-full space-y-3"
      role="region"
      aria-label="Histograma de Distribuição de Densidade do CLV 12M Previsto"
    >
      {/* Legend & Summary */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 font-medium text-text-secondary">
            <span className="h-3 w-3 rounded-xs bg-azul-action" /> Faixas Padrão (&lt; P95)
          </span>
          <span className="flex items-center gap-1.5 font-medium text-text-secondary">
            <span className="h-3 w-3 rounded-xs bg-magenta-cta" /> Cauda Longa Top 5% (&ge; P95)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded bg-muted px-2 py-0.5 font-mono text-[11px] text-azul-navy">
            Média: R$ {media.toFixed(2)}
          </span>
          <span className="rounded bg-muted px-2 py-0.5 font-mono text-[11px] text-azul-navy">
            Mediana: R$ {mediana.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Bar Chart Bars Container */}
      <div
        className="relative h-56 w-full flex items-end gap-1.5 pt-6 pb-6 border-b border-border-subtle"
        role="group"
        aria-label={`Histograma com ${bins.length} faixas de CLV. Média de R$ ${media.toFixed(2)} e mediana de R$ ${mediana.toFixed(2)}`}
      >
        {bins.map((bin, idx) => {
          const heightPct = Math.max((bin.count / maxCount) * 100, 3);
          const isMagenta = bin.is_p95;

          return (
            <div
              key={idx}
              tabIndex={0}
              role="button"
              aria-label={`Faixa ${bin.label}: ${bin.count.toLocaleString("pt-BR")} membros (${((bin.count / totalCustomers) * 100).toFixed(1)}%)${bin.is_p95 ? " - Segmento Cauda Longa Top 5%" : ""}`}
              className="relative flex-1 h-full flex flex-col justify-end items-center group cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-azul-action focus-visible:ring-offset-1 rounded-t-sm motion-reduce:transition-none"
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
              onFocus={() => setHoveredIndex(idx)}
              onBlur={() => setHoveredIndex(null)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setHoveredIndex(idx);
                }
              }}
            >
              <div
                className={`w-full rounded-t-sm transition-all duration-200 motion-reduce:transition-none ${
                  isMagenta
                    ? "bg-magenta-cta hover:bg-magenta-cta/80 group-hover:scale-y-105 group-focus-visible:scale-y-105"
                    : "bg-azul-action hover:bg-azul-action/80 group-hover:scale-y-105 group-focus-visible:scale-y-105"
                }`}
                style={{ height: `${heightPct}%` }}
              />
            </div>
          );
        })}

        {/* Hover/Focus Tooltip Float Posicionado Dinamicamente (P2-15) */}
        {hoveredBin && hoveredIndex !== null && (
          <div
            className="absolute top-0 z-20 rounded-md bg-azul-navy px-3 py-1.5 text-xs text-white shadow-xl pointer-events-none whitespace-nowrap transition-all duration-150 motion-reduce:transition-none border border-slate-700"
            style={{
              left: `${Math.max(10, Math.min(90, ((hoveredIndex + 0.5) / bins.length) * 100))}%`,
              transform: "translateX(-50%)",
            }}
          >
            <p className="font-bold">{hoveredBin.label}</p>
            <p className="text-slate-300">
              {hoveredBin.count.toLocaleString("pt-BR")} membros (
              {((hoveredBin.count / totalCustomers) * 100).toFixed(1)}%)
            </p>
            {hoveredBin.is_p95 && (
              <p className="text-magenta-cta font-bold text-[10px] uppercase">
                ★ Segmento Cauda Longa (Top 5% P95)
              </p>
            )}
          </div>
        )}
      </div>

      {/* X Axis Labels derivados dos bins reais (P2-15) */}
      <div className="flex justify-between text-[10px] text-text-muted font-mono px-1">
        {xLabels.map((item) => (
          <span key={item.idx}>{item.text}</span>
        ))}
      </div>
    </div>
  );
}
