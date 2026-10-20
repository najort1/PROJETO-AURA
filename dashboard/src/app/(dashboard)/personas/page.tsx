import * as React from "react";
import Link from "next/link";
import { Users, BookOpen, AlertTriangle, ArrowRight, BarChart3 } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getPersonasSummary } from "@/lib/data/reader";
import { TermHelp } from "@/components/help/term-help";

export const metadata = {
  title: "02 · Personas e Playbook | PROJETO AURA 2.0",
  description: "6 Arquétipos comportamentais calibrados sobre a base de 50.000 clientes",
};

export default async function PersonasPage() {
  const personas = await getPersonasSummary();

  const totalClients = personas.reduce((acc, p) => acc + p.clientes_count, 0);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-azul-deep">
              Módulo 02
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="outline" className="text-[11px] font-mono">
              6 Arquétipos • {totalClients.toLocaleString("pt-BR")} Clientes
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5 flex items-center gap-2">
            <span>Personas e Segmentação Comportamental</span>
            <TermHelp term="personas" />
          </h1>
          <p className="text-sm text-text-secondary">
            Clusterização analítica, matriz de valor e playbook de intervenção pró-ativa.
          </p>
        </div>
      </div>

      {/* Barra de Legenda e Ajuda Canônica Unificada (P3-9) */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-lg bg-surface border border-border-subtle shadow-xs text-xs text-text-secondary">
        <div className="flex items-center gap-2">
          <span className="font-bold text-azul-navy uppercase tracking-wider text-[11px]">
            Métricas dos Cards:
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-5">
          <div className="flex items-center gap-1.5">
            <span className="font-medium text-azul-navy">CLV 12M Médio</span>
            <TermHelp term="clv" />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-medium text-azul-navy">Churn Médio</span>
            <TermHelp term="churn" />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-medium text-magenta-text font-semibold">VaR Total</span>
            <TermHelp term="var" />
          </div>
        </div>
      </div>

      {/* Grid de Cards das 6 Personas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {personas.map((persona) => {
          const isEventualAscendente = persona.persona === "eventual_ascendente";

          return (
            <Card key={persona.persona} className="overflow-hidden border border-border-subtle shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
              <div>
                {/* Header com token de cor oficial e contraste WCAG AA (P2-16) */}
                <div
                  className={`px-5 py-3 flex items-center justify-between shadow-xs ${
                    isEventualAscendente ? "text-[#07243D]" : "text-white"
                  }`}
                  style={{ backgroundColor: persona.cor }}
                >
                  <div className="font-bold text-sm tracking-tight">{persona.nome_display}</div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-bold font-mono ${
                      isEventualAscendente
                        ? "bg-[#07243D]/15 text-[#07243D]"
                        : "bg-white/20 text-white"
                    }`}
                  >
                    {(persona.share_pct * 100).toFixed(2)}%
                  </span>
                </div>

                <CardContent className="p-5 space-y-4">
                  {/* 2x2 Mini-Grid de Métricas Financeiras */}
                  <div className="grid grid-cols-2 gap-2.5 text-xs font-mono">
                    <div className="rounded-md bg-muted/60 p-2.5">
                      <span className="text-text-muted block text-[10px] font-sans">Membros na Base (N)</span>
                      <span className="text-sm font-bold text-azul-navy">
                        {persona.clientes_count.toLocaleString("pt-BR")}
                      </span>
                    </div>
                    <div className="rounded-md bg-muted/60 p-2.5">
                      <span className="text-text-muted block text-[10px] font-sans">CLV 12M Médio</span>
                      <span className="text-sm font-bold text-azul-action">
                        R$ {persona.clv_medio.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="rounded-md bg-muted/60 p-2.5">
                      <span className="text-text-muted block text-[10px] font-sans">Churn Médio</span>
                      <span className="text-sm font-bold text-text-primary">
                        {(persona.churn_medio * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="rounded-md bg-muted/60 p-2.5">
                      <span className="text-text-muted block text-[10px] font-sans">VaR Total</span>
                      <span className="text-sm font-bold text-magenta-text">
                        R$ {persona.valor_em_risco_total.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}
                      </span>
                    </div>
                  </div>

                  {/* Atritos e Playbook */}
                  <div className="space-y-2 text-xs border-t border-border-subtle pt-3">
                    <div>
                      <span className="font-semibold text-text-primary flex items-center gap-1.5">
                        <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
                        Atrito Crítico Dominante:
                      </span>
                      <p className="text-text-secondary mt-0.5 pl-5 font-sans leading-tight">
                        {persona.atritos_dominantes}
                      </p>
                    </div>
                    <div>
                      <span className="font-semibold text-text-primary flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5 text-azul-action shrink-0" />
                        Ação Playbook Recomendada:
                      </span>
                      <p className="font-mono text-[11px] text-azul-action mt-0.5 pl-5 font-semibold">
                        {persona.acao_recomendada}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </div>

              {/* Footer do Card com Ação Rápida (P0-4) */}
              <div className="p-4 pt-0 border-t border-border-subtle mt-2 flex items-center justify-between">
                <Link
                  href={`/clientes?persona=${encodeURIComponent(persona.persona)}`}
                  className="text-xs text-azul-action hover:text-azul-deep font-semibold flex items-center gap-1"
                >
                  Ver clientes desta persona
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Tabela Comparativa Analítica Completa */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold text-azul-navy flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-azul-action" />
            Tabela Comparativa Analítica das 6 Personas (Base 50k)
          </CardTitle>
          <CardDescription>
            Visão consolidada de tickets, taxas de evasão e volume de capital sob risco.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted text-azul-navy font-semibold uppercase">
                <tr>
                  <th className="p-3 sticky left-0 bg-muted z-10 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1">
                      Persona
                      <TermHelp term="personas" />
                    </span>
                  </th>
                  <th className="p-3 whitespace-nowrap">Total de Clientes (N)</th>
                  <th className="p-3 whitespace-nowrap">Share (%)</th>
                  <th className="p-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1">
                      CLV Médio
                      <TermHelp term="clv" />
                    </span>
                  </th>
                  <th className="p-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1">
                      Churn Médio
                      <TermHelp term="churn" />
                    </span>
                  </th>
                  <th className="p-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1">
                      VaR Total
                      <TermHelp term="var" />
                    </span>
                  </th>
                  <th className="p-3 whitespace-nowrap">Ticket Médio</th>
                  <th className="p-3 whitespace-nowrap">Ação Playbook</th>
                  <th className="p-3 whitespace-nowrap">Atrito Dominante</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {personas.map((p) => (
                  <tr key={p.persona} className="hover:bg-muted/40 transition-colors">
                    <td className="p-3 font-semibold text-azul-navy sticky left-0 bg-surface shadow-xs z-10 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: p.cor }}
                        />
                        <span>{p.nome_display}</span>
                      </div>
                    </td>
                    <td className="p-3 font-mono">{p.clientes_count.toLocaleString("pt-BR")}</td>
                    <td className="p-3 font-mono font-bold">{(p.share_pct * 100).toFixed(2)}%</td>
                    <td className="p-3 font-mono text-azul-action font-semibold">
                      R$ {p.clv_medio.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-3 font-mono">{(p.churn_medio * 100).toFixed(1)}%</td>
                    <td className="p-3 font-mono font-bold text-magenta-text">
                      R$ {p.valor_em_risco_total.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}
                    </td>
                    <td className="p-3 font-mono">R$ {p.ticket_medio.toFixed(2)}</td>
                    <td className="p-3 font-mono text-azul-action text-[11px] font-semibold">{p.acao_recomendada}</td>
                    <td className="p-3 text-text-secondary">{p.atritos_dominantes}</td>
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
