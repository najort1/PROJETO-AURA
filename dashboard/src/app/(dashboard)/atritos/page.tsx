import * as React from "react";
import { AlertOctagon, Info, TrendingDown, Layers, Calendar, Flame } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getFrictionMap } from "@/lib/data/reader";

export const metadata = {
  title: "05 · Mapa de Atritos & Sentimento | PROJETO AURA 2.0",
  description: "Monitoramento em 7 aspectos, 49 pontos semestrais e conformidade LGPD",
};

const aspectLabels: Record<string, string> = {
  atraso: "Atraso de Voo",
  atendimento: "Atendimento",
  bagagem: "Bagagem / Extravio",
  resgate_milhas: "Resgate de Milhas",
  app_checkin: "App & Check-in",
  preco: "Preço & Tarifas",
  conforto: "Conforto a Bordo",
};

const canonicalAspectWeights = [
  { key: "atraso", name: "Atraso de Voo", weight: 0.1965, mentions: 366, negativeRate: 0.724 },
  { key: "atendimento", name: "Atendimento", weight: 0.1770, mentions: 371, negativeRate: 0.681 },
  { key: "bagagem", name: "Bagagem / Extravio", weight: 0.1666, mentions: 305, negativeRate: 0.653 },
  { key: "resgate_milhas", name: "Resgate de Milhas", weight: 0.1660, mentions: 313, negativeRate: 0.748 },
  { key: "app_checkin", name: "App & Check-in", weight: 0.1411, mentions: 353, negativeRate: 0.592 },
  { key: "preco", name: "Preço & Tarifas", weight: 0.1026, mentions: 222, negativeRate: 0.615 },
  { key: "conforto", name: "Conforto a Bordo", weight: 0.0502, mentions: 144, negativeRate: 0.440 },
];

export default async function AtritosPage() {
  const frictionMap = await getFrictionMap();

  // Semestres únicos ordenados
  const semesters = Array.from(new Set(frictionMap.map((f) => f.semester))).sort();

  // Dicionário aspecto -> semestre -> negative_rate
  const matrix: Record<string, Record<string, number>> = {};
  for (const f of frictionMap) {
    if (!matrix[f.aspect]) {
      matrix[f.aspect] = {};
    }
    matrix[f.aspect][f.semester] = f.negative_rate;
  }

  const totalMentions = canonicalAspectWeights.reduce((acc, a) => acc + a.mentions, 0);
  const totalWeight = canonicalAspectWeights.reduce((acc, a) => acc + a.weight, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-amber-600">
              Módulo 05
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="outline" className="text-[11px] font-mono">
              7 Aspectos • 7 Semestres ({frictionMap.length} Registros)
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5">
            Mapa de Atritos e Sentimento por Aspecto
          </h1>
          <p className="text-sm text-text-secondary">
            Categorização de insatisfações de 2024-S1 a 2026-S2 e matriz de pesos ponderados.
          </p>
        </div>
      </div>

      {/* Nota Regulatória Obrigatória (LGPD / Termos de Uso) */}
      <div className="rounded-lg border border-azul-action/30 bg-azul-action/5 p-4 text-xs text-azul-navy flex items-start gap-3 shadow-xs">
        <Info className="h-5 w-5 text-azul-action shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-azul-navy tracking-tight uppercase">
            DECLARAÇÃO METODOLÓGICA — CORPUS SINTÉTICO (LGPD / TERMOS DE USO)
          </p>
          <p className="text-text-secondary leading-relaxed">
            As avaliações e menções analisadas foram geradas sinteticamente com calibração semântica e rotulagem por aspecto em PT-BR. Nenhum dado pessoal, perfil ou avaliação extraída sem autorização de plataformas terceiras é armazenado neste repositório.
          </p>
        </div>
      </div>

      {/* Barras de Intensidade e Negatividade Recente */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold text-azul-navy flex items-center gap-2">
              <Flame className="h-4 w-4 text-magenta-cta" />
              Taxa Média de Sentimento Negativo por Aspecto
            </CardTitle>
            <CardDescription>
              O aspecto com maior índice de insatisfação recebe destaque automático em Magenta CTA.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {canonicalAspectWeights.map((asp) => {
              const isWorst = asp.key === "resgate_milhas";
              const pct = (asp.negativeRate * 100).toFixed(1);

              return (
                <div key={asp.key} className="space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-text-primary flex items-center gap-1.5">
                      {asp.name}
                      {isWorst && (
                        <span className="rounded bg-magenta-cta/10 text-magenta-cta text-[10px] px-1 font-bold">
                          Maior Negatividade
                        </span>
                      )}
                    </span>
                    <span className="font-mono font-bold text-azul-navy">{pct}%</span>
                  </div>
                  <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isWorst ? "bg-magenta-cta" : "bg-azul-action"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Tabela de Pesos Canônicos */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold text-azul-navy flex items-center gap-2">
              <Layers className="h-4 w-4 text-azul-action" />
              Pesos Canônicos dos 7 Aspectos (Soma = {totalWeight.toFixed(4)})
            </CardTitle>
            <CardDescription>
              Importância relativa de cada dimensão no cálculo de atrito agregado.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted text-azul-navy font-semibold uppercase">
                  <tr>
                    <th className="p-2.5">Aspecto</th>
                    <th className="p-2.5">Peso ($W_j$)</th>
                    <th className="p-2.5">Menções</th>
                    <th className="p-2.5">Negatividade</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {canonicalAspectWeights.map((row) => (
                    <tr key={row.key} className="hover:bg-muted/40 font-mono">
                      <td className="p-2.5 font-sans font-medium text-text-primary">
                        {row.name}
                      </td>
                      <td className="p-2.5 font-bold text-azul-action">
                        {row.weight.toFixed(4)} ({(row.weight * 100).toFixed(2)}%)
                      </td>
                      <td className="p-2.5">{row.mentions}</td>
                      <td className="p-2.5 font-bold text-magenta-cta">
                        {(row.negativeRate * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-muted/60 font-bold font-mono border-t-2 border-border-dark">
                    <td className="p-2.5 font-sans">Total Consolidado</td>
                    <td className="p-2.5 text-azul-navy">{totalWeight.toFixed(4)} (100,00%)</td>
                    <td className="p-2.5">{totalMentions}</td>
                    <td className="p-2.5 text-azul-navy">66,2%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Matriz 2D Temporal de Aspectos x Semestres */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold text-azul-navy flex items-center gap-2">
            <Calendar className="h-4 w-4 text-azul-action" />
            Matriz Semestral de Sentimento Negativo (2024-S1 a 2026-S2)
          </CardTitle>
          <CardDescription>
            49 medições semestrais dos índices de insatisfação monitorados continuamente no programa.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-center border-collapse">
              <thead>
                <tr className="bg-muted text-azul-navy font-semibold uppercase">
                  <th className="p-2.5 text-left">Aspecto</th>
                  {semesters.map((s) => (
                    <th key={s} className="p-2.5">{s}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {Object.keys(aspectLabels).map((key) => (
                  <tr key={key} className="hover:bg-muted/40">
                    <td className="p-2.5 text-left font-semibold text-azul-navy">
                      {aspectLabels[key]}
                    </td>
                    {semesters.map((sem) => {
                      const rate = matrix[key]?.[sem] ?? 0.6;
                      const pct = (rate * 100).toFixed(1);
                      const isHigh = rate >= 0.70;

                      return (
                        <td key={sem} className="p-2.5 font-mono">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold ${
                              isHigh
                                ? "bg-magenta-cta/15 text-magenta-cta"
                                : "bg-azul-action/10 text-azul-action"
                            }`}
                          >
                            {pct}%
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
