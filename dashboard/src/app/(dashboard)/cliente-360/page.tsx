import * as React from "react";
import Link from "next/link";
import {
  Search,
  ShieldCheck,
  Calendar,
  Plane,
  AlertTriangle,
  Coins,
  Award,
  ArrowRight,
  ArrowLeft,
  UserX,
  Info,
  Clock,
  Sparkles,
  Compass,
  AlertCircle,
  TrendingUp,
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
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  getCustomerById,
  getTopCustomersByVar,
  getTimelineByCustomerId,
  getClvShapById,
} from "@/lib/data/reader";
import { formatShapFactor } from "@/lib/data/shap-translations";
import { ShapWaterfall } from "@/components/charts/shap-waterfall";
import { CustomerSearchCombobox } from "@/components/customers/customer-search-combobox";
import type { ShapFactorTranslated } from "@/types/analytics";
import { TermHelp } from "@/components/help/term-help";

export const metadata = {
  title: "03 · Cliente 360 & SHAP | PROJETO AURA 2.0",
  description: "Inspeção individual, explicabilidade local SHAP e guardrail temporal",
};

interface PageProps {
  searchParams: Promise<{ id?: string }>;
}

export default async function Cliente360Page({ searchParams }: PageProps) {
  const resolvedParams = await searchParams;
  const rawId = resolvedParams.id?.trim();
  const requestedId = rawId ? rawId.toUpperCase() : undefined;

  // Top 5 Clientes Prioritários para atalhos do Combobox (cache O(1))
  const top5VarShortcuts = await getTopCustomersByVar(5);
  const fallbackCustomer = top5VarShortcuts[0];

  // Caso 1: ID requisitado na URL, mas não existe na base analítica (P0-3)
  if (requestedId) {
    const customerMatch = await getCustomerById(requestedId);

    if (!customerMatch) {
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

          {/* Combobox de Busca Rápida Funcional */}
          <Card className="shadow-2xs border-border-subtle">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold text-azul-navy flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Search className="h-4 w-4 text-azul-action" />
                  Pesquisa de Clientes no Cockpit
                </span>
                <span className="text-xs text-text-muted font-normal">
                  50.000 clientes na base
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CustomerSearchCombobox topCustomers={top5VarShortcuts} />
            </CardContent>
          </Card>

          {/* Estado Explícito de Cliente Não Localizado (P0-3) */}
          <Card className="border-border-subtle shadow-xs">
            <CardContent className="p-12 text-center">
              <div className="flex flex-col items-center justify-center gap-4 max-w-lg mx-auto">
                <div className="p-4 bg-muted/70 text-text-secondary rounded-full border border-border-subtle">
                  <UserX className="h-10 w-10 text-azul-navy" />
                </div>
                <div className="space-y-2">
                  <Badge
                    variant="outline"
                    className="text-xs font-mono text-text-muted border-border-subtle"
                  >
                    Identificador Não Encontrado
                  </Badge>
                  <h2 className="text-xl font-bold text-azul-navy">
                    Cliente &quot;{requestedId}&quot; não localizado na base
                  </h2>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    O identificador <strong className="font-mono text-azul-navy">{requestedId}</strong> não corresponde a nenhum dos 50.000 clientes da coorte calibrada ativa. Por segurança regulatória e privacidade LGPD, nenhum dado de terceiro é exibido.
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="text-xs gap-1.5 cursor-pointer text-azul-navy"
                  >
                    <Link href="/clientes">
                      <ArrowLeft className="h-3.5 w-3.5" />
                      <span>Voltar para a Base de Clientes</span>
                    </Link>
                  </Button>
                  {fallbackCustomer && (
                    <Button
                      asChild
                      variant="primary"
                      size="sm"
                      className="text-xs gap-1.5 cursor-pointer"
                    >
                      <Link href={`/cliente-360?id=${fallbackCustomer.customer_id}`}>
                        <span>Ver Top 1 Risco ({fallbackCustomer.customer_id})</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }
  }

  // Caso 2: Cliente encontrado ou acesso sem parâmetro id (Top 1 VaR por padrão)
  const currentCustomer = requestedId
    ? (await getCustomerById(requestedId))!
    : fallbackCustomer;

  const customerId = currentCustomer.customer_id;

  // Busca timeline com guardrail <= 2025-08-31 via Map indexado O(1)
  const timeline = await getTimelineByCustomerId(customerId);

  // Busca SHAP do cliente via Map indexado O(1)
  const shapRecord = await getClvShapById(customerId);
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

  // Formatação de valores
  const varFormatted = currentCustomer.valor_em_risco.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const clvFormatted = currentCustomer.clv_12m_previsto.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  // Oportunidades & Alavancas CRM (P2-10)
  const hasExpiringPoints = currentCustomer.pontos_expirando_30d > 0;
  const hasGoalProgress = currentCustomer.meta_proximo_nivel_pct > 0;
  const hasUnusedBenefit = Boolean(currentCustomer.beneficio_nao_utilizado);
  const hasFavoriteRoute = Boolean(currentCustomer.rota_favorita);
  const hasFriction = Boolean(currentCustomer.atritos_dominantes);
  const hasAnyOpportunity =
    hasExpiringPoints ||
    hasGoalProgress ||
    hasUnusedBenefit ||
    hasFavoriteRoute ||
    hasFriction;

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

      {/* Seletor Rápido de Clientes via Combobox Funcional (P1-3) */}
      <Card className="shadow-2xs border-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold text-azul-navy flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Search className="h-4 w-4 text-azul-action" />
              Seleção Rápida e Busca no Cockpit 360°
            </span>
            <span className="text-xs text-text-muted font-normal">
              50.000 clientes calibrados
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <CustomerSearchCombobox
            currentCustomerId={currentCustomer.customer_id}
            topCustomers={top5VarShortcuts}
          />
        </CardContent>
      </Card>

      {/* Nota Contextual quando acessado sem ?id (P0-3) */}
      {!requestedId && (
        <div className="flex items-center gap-2.5 p-3 rounded-lg border border-azul-action/25 bg-azul-action/5 text-xs text-azul-navy shadow-2xs">
          <Info className="h-4 w-4 text-azul-action shrink-0" />
          <span>
            <strong>Exibindo cliente com maior Valor em Risco por padrão</strong> (
            <span className="font-mono font-bold">{currentCustomer.customer_id}</span> •
            VaR: <span className="font-mono font-bold text-magenta-text">R$ {varFormatted}</span>
            ). Para inspecionar outro perfil, digite o ID no campo de busca acima.
          </span>
        </div>
      )}

      {/* Cartão Principal do Cliente 360 */}
      <Card className="border-t-4 border-t-azul-action shadow-xs">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-2xl font-extrabold text-azul-navy">
                {currentCustomer.customer_id}
              </span>
              <TierBadge tier={currentCustomer.tier} />
              {/* Badge Top 1 VaR Dinâmico (P3-7) */}
              {currentCustomer.customer_id === fallbackCustomer?.customer_id && (
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
              <span className="font-mono text-xl font-extrabold text-magenta-text">
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

          {/* Bloco Oportunidades de Retenção & Alavancas CRM (P2-10) */}
          <div className="rounded-lg border border-border-subtle bg-surface p-4 shadow-2xs space-y-3">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <h3 className="text-sm font-bold text-azul-navy flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-azul-action" />
                <span>Oportunidades de Retenção &amp; Alavancas CRM</span>
              </h3>
              <Badge variant="outline" className="text-[10px] font-sans">
                Insights Acionáveis
              </Badge>
            </div>

            {!hasAnyOpportunity ? (
              <div className="py-4 text-center text-xs text-text-muted">
                Nenhuma pendência crítica ou benefício desativado para este cliente no momento.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                {/* Alerta de Pontos Expirando */}
                {hasExpiringPoints && (
                  <div className="rounded-md border border-magenta-cta/30 bg-magenta-cta/5 p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-magenta-text font-bold">
                      <Clock className="h-3.5 w-3.5" />
                      <span>Pontos Expirando (30 dias)</span>
                    </div>
                    <p className="font-mono text-base font-extrabold text-magenta-text">
                      {currentCustomer.pontos_expirando_30d.toLocaleString("pt-BR")}{" "}
                      <span className="text-xs font-normal font-sans">pts</span>
                    </p>
                    <p className="text-[11px] text-text-secondary leading-tight">
                      Recomenda-se oferta imediata de resgate ou upgrade para evitar atrito de perda de saldo.
                    </p>
                  </div>
                )}

                {/* Progresso de Nível de Categoria */}
                {hasGoalProgress && (
                  <div className="rounded-md border border-azul-action/30 bg-azul-action/5 p-3 space-y-1.5">
                    <div className="flex items-center justify-between text-azul-navy font-bold">
                      <span className="flex items-center gap-1.5">
                        <TrendingUp className="h-3.5 w-3.5 text-azul-action" />
                        <span>Meta Próximo Nível</span>
                      </span>
                      <span className="font-mono text-azul-action">
                        {(currentCustomer.meta_proximo_nivel_pct * 100).toFixed(0)}%
                      </span>
                    </div>
                    {/* Barra de Progresso */}
                    <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-azul-action rounded-full transition-all"
                        style={{
                          width: `${Math.min(
                            100,
                            currentCustomer.meta_proximo_nivel_pct * 100
                          )}%`,
                        }}
                      />
                    </div>
                    <p className="text-[11px] text-text-secondary leading-tight">
                      Saldo atual de {currentCustomer.saldo_pontos.toLocaleString("pt-BR")} pontos. Faltam poucos trechos para avançar de tier.
                    </p>
                  </div>
                )}

                {/* Benefício Não Utilizado */}
                {hasUnusedBenefit && (
                  <div className="rounded-md border border-border-subtle bg-muted/30 p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-azul-navy font-bold">
                      <Award className="h-3.5 w-3.5 text-amber-500" />
                      <span>Benefício Não Utilizado</span>
                    </div>
                    <p className="font-semibold text-text-primary">
                      {currentCustomer.beneficio_nao_utilizado}
                    </p>
                    <p className="text-[11px] text-text-secondary leading-tight">
                      Alavanca de ativação: incentivar o uso do benefício para fortalecer percepção de valor.
                    </p>
                  </div>
                )}

                {/* Rota Preferencial */}
                {hasFavoriteRoute && (
                  <div className="rounded-md border border-border-subtle bg-muted/30 p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-azul-navy font-bold">
                      <Compass className="h-3.5 w-3.5 text-azul-action" />
                      <span>Rota Preferencial</span>
                    </div>
                    <p className="font-mono font-bold text-azul-navy">
                      {currentCustomer.rota_favorita}
                    </p>
                    <p className="text-[11px] text-text-secondary leading-tight">
                      Canal ótimo para campanhas personalizadas de assento Espaço Azul e antecipação de voo.
                    </p>
                  </div>
                )}

                {/* Atrito Dominante */}
                {hasFriction && (
                  <div className="rounded-md border border-border-subtle bg-muted/30 p-3 space-y-1">
                    <div className="flex items-center gap-1.5 text-azul-navy font-bold">
                      <AlertCircle className="h-3.5 w-3.5 text-magenta-text" />
                      <span>Atrito Dominante</span>
                    </div>
                    <p className="font-semibold text-text-primary">
                      {currentCustomer.atritos_dominantes}
                    </p>
                    <p className="text-[11px] text-text-secondary leading-tight">
                      Atenção especial no atendimento para neutralizar atritos passados nesta dimensão.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Gráfico Waterfall SHAP */}
          <div className="rounded-lg border border-border-subtle bg-surface p-4 shadow-2xs">
            <ShapWaterfall
              factors={shapFactors}
              baseValue={791.09}
              predictedValue={currentCustomer.clv_12m_previsto}
            />
          </div>

          {/* Linha do Tempo com Guardrail Temporal Estrito Reformulado (P2-9) */}
          <div className="space-y-3 pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border-subtle pb-2">
              <h3 className="text-sm font-bold text-azul-navy flex items-center gap-2">
                <Calendar className="h-4 w-4 text-azul-action" />
                Linha do Tempo de Relacionamento (Histórico Auditado)
              </h3>
              {/* Badge Neutro Informativo com Tooltip de Conformidade (P2-9) */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="inline-flex items-center gap-1.5 text-xs text-text-secondary bg-muted/60 border border-border-subtle px-2.5 py-1 rounded-md cursor-help hover:bg-muted/90 transition-colors">
                    <ShieldCheck className="h-3.5 w-3.5 text-azul-action shrink-0" />
                    <span className="font-medium">
                      Guardrail Temporal: Eventos até 31/08/2025
                    </span>
                    <Info className="h-3 w-3 text-text-muted" />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs text-xs">
                  Data de corte amostral estrito (31/08/2025) para conformidade algorítmica: garante a separação rigorosa entre treino e teste para prevenção de vazamento de dados futuros (anti-data leakage).
                </TooltipContent>
              </Tooltip>
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
                        return <AlertTriangle className="h-3.5 w-3.5 text-magenta-text" />;
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
