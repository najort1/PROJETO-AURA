import * as React from "react";
import Link from "next/link";
import { Users, BookOpen, AlertTriangle, ArrowRight, BarChart3, ArrowUpDown } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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

      {/* Grid de Cards das 6 Personas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {personas.map((persona) => (
          <Card key={persona.persona} className="overflow-hidden border border-border-subtle shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
            <div>
              {/* Header com token de cor oficial */}
              <div
                className="px-5 py-3 text-white flex items-center justify-between shadow-xs"
                style={{ backgroundColor: persona.cor }}
              >
                <div className="font-bold text-sm tracking-tight">{persona.nome_display}</div>
                <span className="rounded-full bg-white/20 px-2 py-0.5 text-xs font-bold font-mono">
                  {(persona.share_pct * 100).toFixed(2)}%
                </span>
              </div>

              <CardContent className="p-5 space-y-4">
                {/* 2x2 Mini-Grid de Métricas Financeiras */}
                <div className="grid grid-cols-2 gap-2.5 text-xs font-mono">
                  <div className="rounded-md bg-muted/60 p-2.5">
                    <span className="text-text-muted block text-[10px] font-sans">Membros ($N$)</span>
                    <span className="text-sm font-bold text-azul-navy">
                      {persona.clientes_count.toLocaleString("pt-BR")}
                    </span>
                  </div>
                  <div className="rounded-md bg-muted/60 p-2.5">
                    <span className="text-text-muted text-[10px] font-sans flex items-center justify-between">
                      <span>CLV 12M Médio</span>
                      <TermHelp term="clv" />
                    </span>
                    <span className="text-sm font-bold text-azul-action">
                      R$ {persona.clv_medio.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="rounded-md bg-muted/60 p-2.5">
                    <span className="text-text-muted text-[10px] font-sans flex items-center justify-between">
                      <span>Churn Médio</span>
                      <TermHelp term="churn" />
                    </span>
                    <span className="text-sm font-bold text-text-primary">
                      {(persona.churn_medio * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="rounded-md bg-muted/60 p-2.5">
                    <span className="text-text-muted text-[10px] font-sans flex items-center justify-between">
                      <span>VaR Total</span>
                      <TermHelp term="var" />
                    </span>
                    <span className="text-sm font-bold text-magenta-cta">
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

            {/* Footer do Card com Ação Rápida */}
            <div className="p-4 pt-0 border-t border-border-subtle mt-2 flex items-center justify-between">
              <Link
                href={`/cliente-360?persona=${persona.persona}`}
                className="text-xs text-azul-action hover:text-azul-deep font-semibold flex items-center gap-1"
              >
                Ver clientes desta persona
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </Card>
        ))}
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
                  <th className="p-3">
                    <span className="inline-flex items-center gap-1">
                      Persona
                      <TermHelp term="personas" />
                    </span>
                  </th>
                  <th className="p-3">Clientes ($N$)</th>
                  <th className="p-3">Share (%)</th>
                  <th className="p-3">
                    <span className="inline-flex items-center gap-1">
                      CLV Médio
                      <TermHelp term="clv" />
                    </span>
                  </th>
                  <th className="p-3">
                    <span className="inline-flex items-center gap-1">
                      Churn Médio
                      <TermHelp term="churn" />
                    </span>
                  </th>
                  <th className="p-3">
                    <span className="inline-flex items-center gap-1">
                      VaR Total
                      <TermHelp term="var" />
                    </span>
                  </th>
                  <th className="p-3">Ticket Médio</th>
                  <th className="p-3">Ação Playbook</th>
                  <th className="p-3">Atrito Dominante</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {personas.map((p) => (
                  <tr key={p.persona} className="hover:bg-muted/40 transition-colors">
                    <td className="p-3 font-semibold text-azul-navy flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: p.cor }}
                      />
                      {p.nome_display}
                    </td>
                    <td className="p-3 font-mono">{p.clientes_count.toLocaleString("pt-BR")}</td>
                    <td className="p-3 font-mono font-bold">{(p.share_pct * 100).toFixed(2)}%</td>
                    <td className="p-3 font-mono text-azul-action font-semibold">
                      R$ {p.clv_medio.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="p-3 font-mono">{(p.churn_medio * 100).toFixed(1)}%</td>
                    <td className="p-3 font-mono font-bold text-magenta-cta">
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
