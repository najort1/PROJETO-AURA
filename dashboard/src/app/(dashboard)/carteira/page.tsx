import * as React from "react";
import {
  TrendingDown,
  DollarSign,
  Users,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  PieChart,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getPortfolioSummary, getPortfolioCharts } from "@/lib/data/reader";
import { LorenzCurve } from "@/components/charts/lorenz-curve";
import { ClvHistogram } from "@/components/charts/clv-histogram";
import { PersonaVarBar } from "@/components/charts/persona-var-bar";
import { TermHelp } from "@/components/help/term-help";

export const metadata = {
  title: "01 · Visão da Carteira & VaR | PROJETO AURA 2.0",
  description: "Exposição de capital, concentração de valor e Curva de Lorenz",
};

export default async function CarteiraPage() {
  const [summary, charts] = await Promise.all([
    getPortfolioSummary(),
    getPortfolioCharts(),
  ]);

  const varTotalFormatted = summary.var_total.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  const clvTotalFormatted = summary.clv_total.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  const varExpositionPct = ((summary.var_total / summary.clv_total) * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Header da Tela */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-azul-action">
              Módulo 01
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="outline" className="text-[11px] font-mono">
              Base {summary.total_customers.toLocaleString("pt-BR")} Membros
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5">
            Visão Geral da Carteira e Valor em Risco (VaR)
          </h1>
          <p className="text-sm text-text-secondary">
            Métricas canônicas de risco financeiro, projeção de CLV e assimetria de valor agregado.
          </p>
        </div>
      </div>

      {/* 5 KPI Cards Canônicos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="border-l-4 border-l-magenta-cta shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-text-secondary flex items-center justify-between">
              <span>Valor em Risco (VaR Total)</span>
              <TermHelp term="var" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-azul-navy">
              R$ {varTotalFormatted}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-text-secondary font-medium flex items-center gap-1">
              <TrendingDown className="h-3.5 w-3.5 text-magenta-cta" />
              {varExpositionPct}% do CLV Total
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-azul-action shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-text-secondary flex items-center justify-between">
              <span>CLV 12M Total Previsto</span>
              <TermHelp term="clv" />
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-azul-navy">
              R$ {clvTotalFormatted}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-text-secondary font-medium flex items-center gap-1">
              <DollarSign className="h-3.5 w-3.5 text-azul-action" />
              Média: R$ {summary.media_clv.toFixed(2)} / cliente
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-azul-deep shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Tamanho da Carteira
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-azul-navy">
              {summary.total_customers.toLocaleString("pt-BR")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-text-secondary font-medium flex items-center gap-1">
              <Users className="h-3.5 w-3.5 text-azul-deep" />
              Coorte Calibrada v3
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-azul-primary shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Segmento Alto Valor
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-azul-navy">
              {(summary.alto_valor_pct * 100).toFixed(2)}%
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-text-secondary font-medium flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5 text-azul-primary" />
              {summary.alto_valor_count.toLocaleString("pt-BR")} prioritários (P90)
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Custo Médio da Ação
            </CardDescription>
            <CardTitle className="text-2xl font-bold text-azul-navy">
              R$ {summary.custo_medio_acao.toFixed(2)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="warning" className="text-[10px] px-1.5 py-0 font-medium">
              [PREMISSA DE NEGÓCIO]
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Visualizações Centrais: Histograma e Curva de Lorenz */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Curva de Concentração (Lorenz / Pareto) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold flex items-center justify-between">
              <div className="flex items-center gap-2">
                <PieChart className="h-4 w-4 text-azul-action" />
                <span>Curva de Concentração (Lorenz / Pareto) & Gini ({summary.gini.toFixed(2)})</span>
              </div>
              <TermHelp term="clv" />
            </CardTitle>
            <CardDescription>
              Top 20% dos clientes detém {summary.pareto_80_20_clv_pct.toFixed(1)}% de todo o CLV da companhia.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LorenzCurve
              points={charts.lorenz_curve}
              gini={summary.gini}
              paretoPct={summary.pareto_80_20_clv_pct}
            />
          </CardContent>
        </Card>

        {/* Histograma de Densidade do CLV */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-azul-primary" />
                <span>Distribuição de Densidade do CLV 12M Previsto</span>
              </div>
              <TermHelp term="clv" />
            </CardTitle>
            <CardDescription>
              Frequência de clientes por faixa de receita com destaque automático para a cauda longa (Top 5%).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ClvHistogram
              bins={charts.histogram}
              media={summary.media_clv}
              mediana={summary.mediana_clv}
            />
          </CardContent>
        </Card>
      </div>

      {/* Gráfico de Barras Horizontais: VaR e CLV por Persona */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-magenta-cta" />
              <span>Valor em Risco e CLV por Persona Comportamental</span>
            </div>
            <TermHelp term="personas" />
          </CardTitle>
          <CardDescription>
            Exposição de capital e volume financeiro distribuído nos 6 grupos do modelo de segmentação.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PersonaVarBar items={charts.persona_var} />
        </CardContent>
      </Card>
    </div>
  );
}
