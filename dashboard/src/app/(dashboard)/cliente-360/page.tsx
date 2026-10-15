import * as React from "react";
import Link from "next/link";
import {
  UserCheck,
  Search,
  ShieldAlert,
  Calendar,
  BarChart2,
  Plane,
  AlertTriangle,
  Coins,
  Award,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  DollarSign,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TierBadge } from "@/components/branding/tier-badge";
import {
  getCustomersScores,
  getCustomerTimeline,
  getClvShap,
} from "@/lib/data/reader";
import { formatShapFactor } from "@/lib/data/shap-translations";
import { ShapWaterfall } from "@/components/charts/shap-waterfall";
import type { ShapFactorTranslated } from "@/types/analytics";
import { TermHelp } from "@/components/help/term-help";

export const metadata = {
  title: "03 · Cliente 360 & SHAP | PROJETO AURA 2.0",
  description: "Inspeção individual, explicabilidade local SHAP e guardrail temporal",
};

interface PageProps {
  searchParams: Promise<{ id?: string; persona?: string }>;
}

export default async function Cliente360Page({ searchParams }: PageProps) {
  const resolvedParams = await searchParams;
  const requestedId = resolvedParams.id?.trim().toUpperCase();

  const [allCustomers, allShap] = await Promise.all([
    getCustomersScores(),
    getClvShap(),
  ]);

  // Ordena por maior VaR por padrão
  const sortedByVar = [...allCustomers].sort(
    (a, b) => b.valor_em_risco - a.valor_em_risco
  );

  // Cliente selecionado (padrão C038454 - Top 1 VaR)
  const currentCustomer =
    (requestedId && allCustomers.find((c) => c.customer_id === requestedId)) ||
    sortedByVar[0];

  const customerId = currentCustomer?.customer_id || "C038454";

  // Busca timeline com guardrail <= 2025-08-31
  const timeline = await getCustomerTimeline(customerId);

  // Busca SHAP do cliente
  const shapRecord = allShap.find((s) => s.customer_id === customerId);
  const shapFactors: ShapFactorTranslated[] = [];

  if (shapRecord) {
    if (shapRecord.top1_feature) {
      shapFactors.push(
        formatShapFactor(
          shapRecord.top1_feature,
          shapRecord.top1_shap,
          shapRecord.top1_value
        )
      );
    }
    if (shapRecord.top2_feature) {
      shapFactors.push(
        formatShapFactor(
          shapRecord.top2_feature,
          shapRecord.top2_shap,
          shapRecord.top2_value
        )
      );
    }
    if (shapRecord.top3_feature) {
      shapFactors.push(
        formatShapFactor(
          shapRecord.top3_feature,
          shapRecord.top3_shap,
          shapRecord.top3_value
        )
      );
    }
  }

  // Top 10 Clientes Prioritários para Seleção Rápida
  const top10Var = sortedByVar.slice(0, 10);

  // Formatação de valores
  const varFormatted = currentCustomer.valor_em_risco.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const clvFormatted = currentCustomer.clv_12m_previsto.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-azul-primary">
              Módulo 03
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="outline" className="text-[11px] font-mono">
              Auditoria Granular 50k
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5 flex items-center gap-2">
            <span>Cliente 360 e Explicabilidade SHAP</span>
            <TermHelp term="shap" />
          </h1>
          <p className="text-sm text-text-secondary">
            Decomposição de fatores preditivos LightGBM e linha do tempo com guardrail anti-vazamento.
          </p>
        </div>
      </div>

      {/* Seletor Rápido de Clientes em Risco Crítico */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold text-azul-navy flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Search className="h-4 w-4 text-azul-action" />
              Seleção Rápida de Clientes Prioritários (Top Valor em Risco)
            </span>
            <span className="text-xs text-text-muted font-normal">
              Mostrando os 10 maiores riscos da carteira
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {top10Var.map((c, idx) => (
              <Link
                key={c.customer_id}
                href={`/cliente-360?id=${c.customer_id}`}
                className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-mono transition-all ${
                  c.customer_id === customerId
                    ? "border-azul-action bg-azul-action text-white font-bold shadow-xs"
                    : "border-border-subtle bg-muted/40 hover:bg-muted text-azul-navy"
                }`}
              >
                <span>{c.customer_id}</span>
                <span className={c.customer_id === customerId ? "text-lime-campaign" : "text-magenta-cta"}>
                  R$ {c.valor_em_risco.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}
                </span>
                {idx === 0 && <span className="text-[10px] bg-magenta-cta text-white px-1 rounded">Top 1</span>}
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cartão Principal do Cliente 360 */}
      <Card className="border-t-4 border-t-azul-action shadow-xs">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-2xl font-extrabold text-azul-navy">
                {currentCustomer.customer_id}
              </span>
              <TierBadge tier={currentCustomer.tier} />
              {currentCustomer.customer_id === "C038454" && (
                <Badge variant="destructive" className="font-bold">
                  Top 1 VaR da Carteira
                </Badge>
              )}
              {currentCustomer.alto_valor && (
                <Badge variant="primary">Segmento Alto Valor (P90)</Badge>
              )}
            </div>
            <p className="text-xs text-text-secondary">
              Persona: <strong className="text-azul-navy">{currentCustomer.persona}</strong> • Recência: <span className="font-mono">{currentCustomer.recencia_dias} dias</span> • Voos (12M): <span className="font-mono">{currentCustomer.frequencia_voos}</span>
            </p>
          </div>

          <div className="flex items-center gap-4 bg-muted/30 p-2.5 rounded-lg border border-border-subtle">
            <div className="text-right">
              <span className="text-[10px] text-text-muted uppercase font-sans font-semibold flex items-center justify-end gap-1">
                <span>Valor em Risco (VaR)</span>
                <TermHelp term="var" />
              </span>
              <span className="font-mono text-xl font-extrabold text-magenta-cta">
                R$ {varFormatted}
              </span>
            </div>
            <div className="h-8 w-px bg-border-subtle" />
            <div className="text-right">
              <span className="text-[10px] text-text-muted uppercase font-sans font-semibold flex items-center justify-end gap-1">
                <span>Prob. Churn</span>
                <TermHelp term="churn" />
              </span>
              <span className="font-mono text-xl font-extrabold text-azul-navy">
                {(currentCustomer.churn_prob * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-6 space-y-6">
          {/* Mini-Cards de Métricas Individuais */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div className="rounded-lg border border-border-subtle bg-muted/40 p-3">
              <span className="text-text-muted font-sans text-[11px] flex items-center justify-between">
                <span>CLV 12M Previsto</span>
                <TermHelp term="clv" />
              </span>
              <span className="text-base font-bold text-azul-action">R$ {clvFormatted}</span>
            </div>
            <div className="rounded-lg border border-border-subtle bg-muted/40 p-3">
              <span className="text-text-muted font-sans text-[11px] flex items-center justify-between">
                <span>Score Alto Valor (ScoreAV)</span>
                <TermHelp term="score_av" />
              </span>
              <span className="text-base font-bold text-azul-navy">{currentCustomer.score_av.toFixed(3)}</span>
            </div>
            <div className="rounded-lg border border-border-subtle bg-muted/40 p-3">
              <span className="text-text-muted block font-sans text-[11px]">Gasto Total (12M)</span>
              <span className="text-base font-bold text-text-primary">
                R$ {currentCustomer.gastos_12m_brl.toFixed(2)}
              </span>
            </div>
            <div className="rounded-lg border border-border-subtle bg-muted/40 p-3">
              <span className="text-text-muted block font-sans text-[11px]">Pontos Qualificáveis</span>
              <span className="text-base font-bold text-text-primary">
                {currentCustomer.pontos_qualificaveis_12m.toLocaleString("pt-BR")}
              </span>
            </div>
          </div>

          {/* Gráfico Waterfall SHAP */}
          <div className="rounded-lg border border-border-subtle bg-surface p-4 shadow-2xs">
            <ShapWaterfall
              factors={shapFactors}
              baseValue={791.09}
              predictedValue={currentCustomer.clv_12m_previsto}
            />
          </div>

          {/* Linha do Tempo com Guardrail Temporal Estrito */}
          <div className="space-y-3 pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border-subtle pb-2">
              <h3 className="text-sm font-bold text-azul-navy flex items-center gap-2">
                <Calendar className="h-4 w-4 text-azul-action" />
                Linha do Tempo de Relacionamento (Histórico Auditado)
              </h3>
              <div className="flex items-center gap-1.5 text-xs text-amber-800 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
                <span>Guardrail Ativo: Eventos estritamente &le; 2025-08-31</span>
              </div>
            </div>

            {timeline.length === 0 ? (
              <div className="h-28 flex items-center justify-center text-xs text-text-muted border border-dashed rounded-md">
                Nenhum evento registrado até 2025-08-31 para este cliente.
              </div>
            ) : (
              <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border-subtle">
                {timeline.map((event, idx) => {
                  const getIcon = () => {
                    switch (event.tipo) {
                      case "voo":
                        return <Plane className="h-3.5 w-3.5 text-azul-action" />;
                      case "atrito":
                        return <AlertTriangle className="h-3.5 w-3.5 text-magenta-cta" />;
                      case "resgate":
                        return <Coins className="h-3.5 w-3.5 text-amber-500" />;
                      case "tier":
                        return <Award className="h-3.5 w-3.5 text-azul-deep" />;
                      default:
                        return <Calendar className="h-3.5 w-3.5 text-text-muted" />;
                    }
                  };

                  return (
                    <div key={idx} className="relative group text-xs">
                      {/* Timeline Dot */}
                      <div className="absolute -left-6 top-1 h-4 w-4 rounded-full bg-surface border-2 border-azul-action flex items-center justify-center shadow-xs">
                        <div className="h-1.5 w-1.5 rounded-full bg-azul-action" />
                      </div>

                      <div className="rounded-lg border border-border-subtle bg-muted/20 p-3 hover:bg-muted/40 transition-colors">
                        <div className="flex items-center justify-between font-mono text-[11px] text-text-muted mb-1">
                          <span className="flex items-center gap-1.5 font-sans font-bold text-azul-navy">
                            {getIcon()}
                            {event.titulo}
                          </span>
                          <span>{event.data}</span>
                        </div>
                        <p className="text-text-secondary text-xs">{event.detalhe}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
