"use client";

import * as React from "react";
import type { LorenzPoint } from "@/types/analytics";

interface LorenzCurveProps {
  points: LorenzPoint[];
  gini: number;
  paretoPct: number;
}

export function LorenzCurve({ points, gini, paretoPct }: LorenzCurveProps) {
  const [hoveredPoint, setHoveredPoint] = React.useState<LorenzPoint | null>(null);

  if (!points || points.length === 0) {
    return <div className="h-64 flex items-center justify-center text-xs text-text-muted">Carregando curva de Lorenz...</div>;
  }

  const width = 500;
  const height = 300;
  const padding = 45;

  const innerWidth = width - padding * 2;
  const innerHeight = height - padding * 2;

  const getX = (p: number) => padding + p * innerWidth;
  const getY = (lp: number) => height - padding - lp * innerHeight;

  // Path da curva de Lorenz
  const lorenzPath = points.reduce((acc, pt, i) => {
    const x = getX(pt.p);
    const y = getY(pt.l_p);
    return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, "");

  // Área sombreada entre linha de perfeita igualdade e curva de Lorenz (Área do Gini)
  const giniAreaPath = `${lorenzPath} L ${getX(1)} ${getY(1)} L ${getX(0)} ${getY(0)} Z`;

  // Ponto 80/20 (p = 0.8)
  const paretoX = getX(0.8);
  const paretoY = getY(1 - paretoPct / 100);

  return (
    <div className="flex flex-col items-center w-full">
      <div className="relative w-full max-w-lg aspect-[5/3]">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-full overflow-visible select-none"
        >
          {/* Grid lines */}
          {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((tick) => (
            <g key={tick}>
              <line
                x1={getX(tick)}
                y1={getY(0)}
                x2={getX(tick)}
                y2={getY(1)}
                stroke="#E2E6E9"
                strokeDasharray="3 3"
                strokeWidth="1"
              />
              <line
                x1={getX(0)}
                y1={getY(tick)}
                x2={getX(1)}
                y2={getY(tick)}
                stroke="#E2E6E9"
                strokeDasharray="3 3"
                strokeWidth="1"
              />
              <text
                x={getX(tick)}
                y={height - padding + 15}
                fontSize="10"
                fill="#5E6F7A"
                textAnchor="middle"
              >
                {Math.round(tick * 100)}%
              </text>
              <text
                x={padding - 8}
                y={getY(tick) + 3}
                fontSize="10"
                fill="#5E6F7A"
                textAnchor="end"
              >
                {Math.round(tick * 100)}%
              </text>
            </g>
          ))}

          {/* Área do Gini Sombreada */}
          <path
            d={giniAreaPath}
            fill="#0874B5"
            fillOpacity="0.12"
          />

          {/* Linha de Perfeita Igualdade (Diagonal 45°) */}
          <line
            x1={getX(0)}
            y1={getY(0)}
            x2={getX(1)}
            y2={getY(1)}
            stroke="#8A99A2"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />

          {/* Curva de Lorenz Real */}
          <path
            d={lorenzPath}
            fill="none"
            stroke="#0874B5"
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Ponto e Destaque 80/20 */}
          <circle
            cx={paretoX}
            cy={paretoY}
            r="6"
            fill="#E832A5"
            stroke="#FFFFFF"
            strokeWidth="2"
            className="animate-pulse"
          />
          <line
            x1={paretoX}
            y1={paretoY}
            x2={paretoX}
            y2={getY(0)}
            stroke="#E832A5"
            strokeWidth="1.5"
            strokeDasharray="2 2"
          />
          <line
            x1={getX(0)}
            y1={paretoY}
            x2={paretoX}
            y2={paretoY}
            stroke="#E832A5"
            strokeWidth="1.5"
            strokeDasharray="2 2"
          />

          {/* Interactive hover overlay */}
          {points.map((pt, i) => (
            <circle
              key={i}
              cx={getX(pt.p)}
              cy={getY(pt.l_p)}
              r="8"
              fill="transparent"
              className="cursor-pointer hover:stroke-azul-navy hover:stroke-2"
              onMouseEnter={() => setHoveredPoint(pt)}
              onMouseLeave={() => setHoveredPoint(null)}
            />
          ))}

          {/* Label de Eixos */}
          <text
            x={width / 2}
            y={height - 5}
            fontSize="11"
            fill="#0B3558"
            fontWeight="600"
            textAnchor="middle"
          >
            Fração Acumulada de Clientes (0 a 100%)
          </text>
          <text
            x={-height / 2}
            y="12"
            transform="rotate(-90)"
            fontSize="11"
            fill="#0B3558"
            fontWeight="600"
            textAnchor="middle"
          >
            Fração Acumulada da Receita CLV (0 a 100%)
          </text>
        </svg>

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <div
            className="absolute z-20 pointer-events-none rounded-md bg-azul-navy px-2.5 py-1.5 text-xs text-white shadow-lg border border-slate-700"
            style={{
              left: `${(getX(hoveredPoint.p) / width) * 100}%`,
              top: `${(getY(hoveredPoint.l_p) / height) * 100 - 15}%`,
              transform: "translate(-50%, -100%)",
            }}
          >
            <p className="font-bold">Clientes: {(hoveredPoint.p * 100).toFixed(1)}%</p>
            <p className="text-azul-primary">CLV Acumulado: {(hoveredPoint.l_p * 100).toFixed(1)}%</p>
          </div>
        )}
      </div>

      {/* Badges de Anotação Canônica */}
      <div className="flex flex-wrap items-center justify-center gap-4 mt-3 text-xs">
        <div className="flex items-center gap-1.5 rounded-full bg-azul-action/10 px-3 py-1 font-semibold text-azul-navy border border-azul-action/20">
          <span className="h-2.5 w-2.5 rounded-full bg-azul-action" />
          Coeficiente de Gini: <span className="font-mono text-azul-action text-sm font-bold">{gini.toFixed(2)}</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-magenta-cta/10 px-3 py-1 font-semibold text-azul-navy border border-magenta-cta/20">
          <span className="h-2.5 w-2.5 rounded-full bg-magenta-cta" />
          Marcador 80/20: Top 20% detém <span className="font-mono text-magenta-cta text-sm font-bold">{paretoPct.toFixed(1)}%</span> do CLV
        </div>
      </div>
    </div>
  );
}
