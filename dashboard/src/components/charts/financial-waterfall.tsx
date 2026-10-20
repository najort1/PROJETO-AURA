"use client";

import * as React from "react";
import { formatCurrencyBRL } from "@/lib/format";

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
  const formatBRL = formatCurrencyBRL;

  // Dimensões SVG coordenadas
  const svgWidth = 520;
  const svgHeight = 230;
  const topMargin = 32;
  const bottomMargin = 40;
  const chartHeight = svgHeight - topMargin - bottomMargin; // 158

  // Escala dinâmica calibrada para comportar grandezas positivas e negativas
  const maxPos = Math.max(receitaSalva, receitaLiquida > 0 ? receitaLiquida : 0, 1000);
  const maxNeg = Math.max(custoTotal, receitaLiquida < 0 ? Math.abs(receitaLiquida) : 0, 1000);

  // Posição vertical do eixo zero (com clamping para garantir headroom mínimo de 36px)
  const rawZeroY = topMargin + (maxPos / (maxPos + maxNeg)) * chartHeight;
  const zeroY = Math.min(Math.max(rawZeroY, topMargin + 36), topMargin + chartHeight - 36);

  const posAvailable = zeroY - topMargin;
  const negAvailable = topMargin + chartHeight - zeroY;

  // Barra 1: Investimento / Custo (projeção para BAIXO a partir do zero em magenta)
  const custoHeight = Math.max(4, (custoTotal / maxNeg) * negAvailable);
  const custoY = zeroY;

  // Barra 2: Receita Bruta Salva (projeção para CIMA a partir do zero em azul-action)
  const receitaHeight = Math.max(4, (receitaSalva / maxPos) * posAvailable);
  const receitaY = zeroY - receitaHeight;

  // Barra 3: Δ Retorno Líquido (polaridade condicional sem Math.abs mascarando prejuízo)
  const isLiquidoPositivo = receitaLiquida >= 0;
  const liquidoHeight = Math.max(
    4,
    isLiquidoPositivo
      ? (receitaLiquida / maxPos) * posAvailable
      : (Math.abs(receitaLiquida) / maxNeg) * negAvailable
  );
  const liquidoY = isLiquidoPositivo ? zeroY - liquidoHeight : zeroY;

  const barWidth = 72;
  const col1X = 60;
  const col2X = 205;
  const col3X = 350;

  return (
    <div className="w-full space-y-3 font-sans">
      <div className="flex items-center justify-between text-xs border-b border-border-subtle pb-2">
        <span className="font-bold text-azul-navy uppercase tracking-wider text-[11px]">
          Decomposição do Retorno Econômico Líquido (Waterfall)
        </span>
        <span className="font-mono text-xs font-semibold text-text-secondary">
          ROI:{" "}
          <span
            className={
              roiPct >= 0
                ? "text-emerald-600 font-bold"
                : "text-magenta-text font-bold"
            }
          >
            {roiPct.toFixed(1)}%
          </span>
        </span>
      </div>

      {/* Gráfico Waterfall SVG Customizado Real com Eixo Zero Explícito */}
      <div className="w-full overflow-x-auto bg-surface rounded-lg p-2 border border-border-subtle shadow-xs">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto min-w-[460px] select-none"
          role="img"
          aria-label={`Waterfall financeiro: Investimento de ${formatBRL(custoTotal)}, Receita salva de ${formatBRL(receitaSalva)} e Retorno líquido de ${formatBRL(receitaLiquida)}`}
        >
          <title>Waterfall Financeiro de Retenção</title>
          <desc>
            Gráfico de cascata com eixo zero horizontal. Investimento de {formatBRL(custoTotal)} projetado para baixo, receita salva de {formatBRL(receitaSalva)} projetada para cima e retorno líquido de {formatBRL(receitaLiquida)}.
          </desc>

          {/* Gridline de Referência Superior */}
          <line
            x1="30"
            y1={topMargin}
            x2="460"
            y2={topMargin}
            stroke="#E2E8F0"
            strokeWidth="1"
            strokeDasharray="2 3"
          />

          {/* Eixo Zero Horizontal Explícito */}
          <line
            x1="30"
            y1={zeroY}
            x2="465"
            y2={zeroY}
            stroke="#64748B"
            strokeWidth="1.5"
          />
          <text
            x="472"
            y={zeroY + 3.5}
            fill="#64748B"
            fontSize="10"
            fontFamily="monospace"
            fontWeight="bold"
          >
            R$ 0,00
          </text>

          {/* BARRA 1: Investimento / Custo (Projeta para BAIXO em Magenta) */}
          <g>
            <rect
              x={col1X}
              y={custoY}
              width={barWidth}
              height={custoHeight}
              rx="4"
              className="fill-[#B81D7D] transition-all duration-300"
            />
            {/* Valor monetário (abaixo da barra projetada para baixo) */}
            <text
              x={col1X + barWidth / 2}
              y={custoY + custoHeight + 14}
              textAnchor="middle"
              className="fill-[#B81D7D] font-mono text-[11px] font-bold"
            >
              -{formatBRL(custoTotal)}
            </text>
            <text
              x={col1X + barWidth / 2}
              y={svgHeight - 8}
              textAnchor="middle"
              className="fill-slate-600 text-[10px] font-semibold"
            >
              1. Custo Campanha
            </text>
          </g>

          {/* BARRA 2: Receita Bruta Salva (Projeta para CIMA em Azul-Action) */}
          <g>
            <rect
              x={col2X}
              y={receitaY}
              width={barWidth}
              height={receitaHeight}
              rx="4"
              className="fill-[#0070BA] transition-all duration-300"
            />
            {/* Valor monetário (acima da barra projetada para cima) */}
            <text
              x={col2X + barWidth / 2}
              y={receitaY - 8}
              textAnchor="middle"
              className="fill-[#0070BA] font-mono text-[11px] font-bold"
            >
              +{formatBRL(receitaSalva)}
            </text>
            <text
              x={col2X + barWidth / 2}
              y={svgHeight - 8}
              textAnchor="middle"
              className="fill-slate-600 text-[10px] font-semibold"
            >
              2. Receita Salva
            </text>
          </g>

          {/* BARRA 3: Delta Retorno Líquido (Polaridade Condicional Honesta) */}
          <g>
            <rect
              x={col3X}
              y={liquidoY}
              width={barWidth}
              height={liquidoHeight}
              rx="4"
              className={`transition-all duration-300 ${
                isLiquidoPositivo ? "fill-emerald-600" : "fill-[#B81D7D]"
              }`}
            />
            {/* Valor monetário posicionado conforme polaridade */}
            <text
              x={col3X + barWidth / 2}
              y={isLiquidoPositivo ? liquidoY - 8 : liquidoY + liquidoHeight + 14}
              textAnchor="middle"
              className={`font-mono text-[11px] font-extrabold ${
                isLiquidoPositivo ? "fill-emerald-700" : "fill-[#B81D7D]"
              }`}
            >
              {isLiquidoPositivo ? "+" : ""}
              {formatBRL(receitaLiquida)}
            </text>
            <text
              x={col3X + barWidth / 2}
              y={svgHeight - 8}
              textAnchor="middle"
              className="fill-slate-600 text-[10px] font-semibold"
            >
              3. Δ Retorno Líquido
            </text>
          </g>
        </svg>
      </div>

      {/* Legenda Informativa */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-[11px] text-text-secondary">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="size-2.5 rounded-full bg-[#B81D7D]" aria-hidden="true" />
            <span>Saída (Custo)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="size-2.5 rounded-full bg-[#0070BA]" aria-hidden="true" />
            <span>Entrada (Preservada)</span>
          </span>
          <span className="flex items-center gap-1">
            <span
              className={`size-2.5 rounded-full ${
                receitaLiquida >= 0 ? "bg-emerald-600" : "bg-[#B81D7D]"
              }`}
              aria-hidden="true"
            />
            <span>Resultado Líquido</span>
          </span>
        </div>
        <span className="font-mono text-[10px] text-text-muted">
          Eixo zero horizontal calibrado
        </span>
      </div>
    </div>
  );
}
