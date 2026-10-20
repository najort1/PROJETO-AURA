import * as React from "react";
import { AlertOctagon, Info, Layers, Calendar, Flame } from "lucide-react";
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

interface AggregatedAspect {
  key: string;
  name: string;
  weight: number;
  mentions: number;
  negativeCount: number;
  negativeRate: number;
}

export default async function AtritosPage() {
  const frictionMap = await getFrictionMap();

  // Semestres únicos ordenados decrescentemente (mais recente primeiro - P3-10)
  const semesters = Array.from(new Set(frictionMap.map((f) => f.semester))).sort().reverse();

  // Dicionário aspecto -> semestre -> negative_rate
  const matrix: Record<string, Record<string, number>> = {};
  // Mapa de agregação dinâmica dos registros (P1-6)
  const aspectsMap: Record<
    string,
    { weight: number; mentions: number; negativeCount: number }
  > = {};

  for (const f of frictionMap) {
    if (!matrix[f.aspect]) {
      matrix[f.aspect] = {};
    }
    matrix[f.aspect][f.semester] = f.negative_rate;

    if (!aspectsMap[f.aspect]) {
      aspectsMap[f.aspect] = {
        weight: Number(f.aspect_weight) || 0,
        mentions: 0,
        negativeCount: 0,
      };
    }
    aspectsMap[f.aspect].mentions += Number(f.mention_count);
    aspectsMap[f.aspect].negativeCount += Number(f.negative_count);
  }

  // Lista agregada de aspectos baseada nos registros reais
  const aspectKeys = Object.keys(aspectLabels);
  const derivedAspects: AggregatedAspect[] = aspectKeys.map((key) => {
    const data = aspectsMap[key] || { weight: 0, mentions: 0, negativeCount: 0 };
    const negativeRate = data.mentions > 0 ? data.negativeCount / data.mentions : 0;
    return {
      key,
      name: aspectLabels[key] || key,
      weight: data.weight,
      mentions: data.mentions,
      negativeCount: data.negativeCount,
      negativeRate,
    };
  });

  const maxNegativeRate = Math.max(...derivedAspects.map((a) => a.negativeRate), 0);
  const totalMentions = derivedAspects.reduce((acc, a) => acc + a.mentions, 0);
  const totalWeight = derivedAspects.reduce((acc, a) => acc + a.weight, 0);

  // Cálculo ponderado real da taxa agregada (P1-6)
  const weightedNegativeRate =
    totalWeight > 0
      ? derivedAspects.reduce((acc, a) => acc + a.weight * a.negativeRate, 0) / totalWeight
      : 0;

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
              7 Aspectos • {semesters.length} Semestres ({frictionMap.length} Registros)
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5">
            Mapa de Atritos e Sentimento por Aspecto
          </h1>
          <p className="text-sm text-text-secondary">
            Categorização de insatisfações de {semesters[semesters.length - 1]} a {semesters[0]} e matriz de pesos ponderados.
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
            {derivedAspects.map((asp) => {
              const isWorst = asp.negativeRate === maxNegativeRate && maxNegativeRate > 0;
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
                    <th className="p-2.5 sticky left-0 bg-muted z-10 whitespace-nowrap">Aspecto</th>
                    <th className="p-2.5 whitespace-nowrap">Peso Ponderado (W)</th>
                    <th className="p-2.5 whitespace-nowrap">Menções</th>
                    <th className="p-2.5 whitespace-nowrap">Negatividade</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {derivedAspects.map((row) => (
                    <tr key={row.key} className="hover:bg-muted/40 font-mono">
                      <td className="p-2.5 font-sans font-medium text-text-primary sticky left-0 bg-surface shadow-xs z-10 whitespace-nowrap">
                        {row.name}
                      </td>
                      <td className="p-2.5 font-bold text-azul-action whitespace-nowrap">
                        {row.weight.toFixed(4)} ({(row.weight * 100).toFixed(2)}%)
                      </td>
                      <td className="p-2.5 whitespace-nowrap">{row.mentions.toLocaleString("pt-BR")}</td>
                      <td className="p-2.5 font-bold text-magenta-text whitespace-nowrap">
                        {(row.negativeRate * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-muted/60 font-bold font-mono border-t-2 border-border-dark">
                    <td className="p-2.5 font-sans sticky left-0 bg-muted/60 shadow-xs z-10 whitespace-nowrap">Total Consolidado</td>
                    <td className="p-2.5 text-azul-navy whitespace-nowrap">{totalWeight.toFixed(4)} (100,00%)</td>
                    <td className="p-2.5 whitespace-nowrap">{totalMentions.toLocaleString("pt-BR")}</td>
                    <td className="p-2.5 text-azul-navy whitespace-nowrap">
                      {(weightedNegativeRate * 100).toFixed(1)}%
                    </td>
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
            Matriz Semestral de Sentimento Negativo ({semesters[semesters.length - 1]} a {semesters[0]})
          </CardTitle>
          <CardDescription>
            {frictionMap.length} medições semestrais dos índices de insatisfação monitorados continuamente no programa.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-center border-collapse">
              <thead>
                <tr className="bg-muted text-azul-navy font-semibold uppercase">
                  <th className="p-2.5 text-left sticky left-0 bg-muted z-10 whitespace-nowrap">Aspecto</th>
                  {semesters.map((s) => (
                    <th key={s} className="p-2.5 whitespace-nowrap">{s}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {Object.keys(aspectLabels).map((key) => (
                  <tr key={key} className="hover:bg-muted/40">
                    <td className="p-2.5 text-left font-semibold text-azul-navy sticky left-0 bg-surface shadow-xs z-10 whitespace-nowrap">
                      {aspectLabels[key] || key}
                    </td>
                    {semesters.map((sem) => {
                      const rate = matrix[key]?.[sem];
                      if (rate === undefined || rate === null) {
                        return (
                          <td key={sem} className="p-2.5 font-mono text-text-muted">
                            -
                          </td>
                        );
                      }
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
