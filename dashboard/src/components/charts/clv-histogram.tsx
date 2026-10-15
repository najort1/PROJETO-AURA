"use client";

import * as React from "react";
import type { HistogramBin } from "@/types/analytics";

interface ClvHistogramProps {
  bins: HistogramBin[];
  media: number;
  mediana: number;
}

export function ClvHistogram({ bins, media, mediana }: ClvHistogramProps) {
  const [hoveredBin, setHoveredBin] = React.useState<HistogramBin | null>(null);

  if (!bins || bins.length === 0) {
    return <div className="h-64 flex items-center justify-center text-xs text-text-muted">Carregando histograma...</div>;
  }

  const maxCount = Math.max(...bins.map((b) => b.count), 1);
  const totalCustomers = bins.reduce((acc, b) => acc + b.count, 0);

  return (
    <div className="w-full space-y-3">
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
      <div className="relative h-56 w-full flex items-end gap-1.5 pt-6 pb-6 border-b border-border-subtle">
        {bins.map((bin, idx) => {
          const heightPct = Math.max((bin.count / maxCount) * 100, 3);
          const isMagenta = bin.is_p95;

          return (
            <div
              key={idx}
              className="relative flex-1 h-full flex flex-col justify-end items-center group cursor-pointer"
              onMouseEnter={() => setHoveredBin(bin)}
              onMouseLeave={() => setHoveredBin(null)}
            >
              <div
                className={`w-full rounded-t-sm transition-all duration-200 ${
                  isMagenta
                    ? "bg-magenta-cta hover:bg-magenta-cta/80 group-hover:scale-y-105"
                    : "bg-azul-action hover:bg-azul-action/80 group-hover:scale-y-105"
                }`}
                style={{ height: `${heightPct}%` }}
              />
            </div>
          );
        })}

        {/* Hover Tooltip Float */}
        {hoveredBin && (
          <div className="absolute top-0 left-1/2 -translate-x-1/2 z-20 rounded-md bg-azul-navy px-3 py-1.5 text-xs text-white shadow-xl pointer-events-none">
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

      {/* X Axis Labels */}
      <div className="flex justify-between text-[10px] text-text-muted font-mono px-1">
        <span>R$ 0</span>
        <span>R$ 2.000</span>
        <span>R$ 4.000</span>
        <span>R$ 6.000+</span>
      </div>
    </div>
  );
}
