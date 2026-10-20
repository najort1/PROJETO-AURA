import * as React from "react";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  Scale,
  FileText,
  UserCheck,
  Lock,
  Eye,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getFairnessMetrics } from "@/lib/data/reader";
import { TermHelp } from "@/components/help/term-help";

export const metadata = {
  title: "07 · IA Responsável & LGPD | PROJETO AURA 2.0",
  description: "Auditoria Four-Fifths, transparência algorítmica e salvaguardas do Art. 20 da LGPD",
};

export default async function IaResponsavelPage() {
  const metrics = await getFairnessMetrics();

  // Classificação dos grupos
  const compliantCount = metrics.filter(
    (m) =>
      !m.group_value.toLowerCase().includes("não informado") &&
      m.selection_ratio_vs_max >= 0.8 &&
      m.selection_ratio_vs_max < 1.0
  ).length;

  const referenceCount = metrics.filter(
    (m) => m.selection_ratio_vs_max === 1.0
  ).length;

  const nonCompliant = metrics.filter(
    (m) =>
      !m.group_value.toLowerCase().includes("não informado") &&
      m.selection_ratio_vs_max < 0.8
  );

  const excludedLgpd = metrics.filter((m) =>
    m.group_value.toLowerCase().includes("não informado")
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-600">
              Módulo 07
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="outline" className="text-[11px] font-mono">
              EEOC 29 CFR § 1607.4 • Art. 20 LGPD
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5 flex items-center gap-2">
            <span>IA Responsável, Auditoria de Viés e Governança LGPD</span>
            <TermHelp term="regra_4_5" />
          </h1>
          <p className="text-sm text-text-secondary">
            Auditoria da Regra dos Quatro Quintos (Four-Fifths) e salvaguardas transacionais para decisões automatizadas.
          </p>
        </div>
      </div>

      {/* 3 Cards de Síntese da Regra dos 4/5 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 border-l-4 border-l-emerald-600 shadow-xs">
          <span className="text-xs font-semibold text-text-muted block">Grupos em Conformidade</span>
          <span className="text-2xl font-extrabold text-emerald-700 font-mono">
            {compliantCount + referenceCount} Grupos
          </span>
          <span className="text-xs text-text-secondary mt-1 block">
            Impact Ratio &ge; 0,80 (inclui {referenceCount} grupos de referência)
          </span>
        </Card>

        <Card className="p-4 border-l-4 border-l-magenta-cta shadow-xs">
          <span className="text-xs font-semibold text-text-muted block">Disparidades Adversas (&lt; 0,80)</span>
          <span className="text-2xl font-extrabold text-magenta-cta font-mono">
            {nonCompliant.length} Grupos
          </span>
          <span
            className="text-xs text-text-secondary mt-1 block leading-relaxed"
            title={nonCompliant
              .map((g) => `${g.group_value} (${g.selection_ratio_vs_max.toLocaleString("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 })})`)
              .join(", ")}
          >
            {nonCompliant
              .map((g) => `${g.group_value} (${g.selection_ratio_vs_max.toLocaleString("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 })})`)
              .join(", ")}
          </span>
        </Card>

        <Card className="p-4 border-l-4 border-l-slate-400 shadow-xs">
          <span className="text-xs font-semibold text-text-muted block">Preservação LGPD (Não Informado)</span>
          <span className="text-2xl font-extrabold text-slate-700 font-mono">
            {excludedLgpd.length} Grupos
          </span>
          <span className="text-xs text-text-secondary mt-1 block">
            Mantidos fora do denominador em respeito à autodeterminação
          </span>
        </Card>
      </div>

      {/* Tabela Mestra de Auditoria Four-Fifths */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold text-azul-navy flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Scale className="h-4 w-4 text-azul-action" />
              <span>Tabela Mestra de Disparidade nos Grupos Demográficos (16 Linhas Auditadas)</span>
            </div>
            <TermHelp term="regra_4_5" />
          </CardTitle>
          <CardDescription>
            Taxa de seleção para o segmento de Alto Valor (Top 10% da carteira) versus grupo de referência em cada dimensão sensível.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted text-azul-navy font-semibold uppercase">
                <tr>
                  <th className="p-3 sticky left-0 bg-muted z-10 whitespace-nowrap">Dimensão Protegida</th>
                  <th className="p-3 whitespace-nowrap">Grupo Demográfico</th>
                  <th className="p-3 whitespace-nowrap">Total da Amostra (N)</th>
                  <th className="p-3 whitespace-nowrap">Taxa Alto Valor</th>
                  <th className="p-3 whitespace-nowrap">Razão vs Máximo</th>
                  <th className="p-3 whitespace-nowrap">Churn Médio</th>
                  <th className="p-3 whitespace-nowrap">Status de Conformidade</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {metrics.map((row, idx) => {
                  const isExcluded = row.group_value.toLowerCase().includes("não informado");
                  const isReference = row.selection_ratio_vs_max === 1.0;
                  const isNonCompliant = !isExcluded && row.selection_ratio_vs_max < 0.8;

                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-muted/40 transition-colors ${
                        isNonCompliant ? "bg-magenta-cta/5" : ""
                      }`}
                    >
                      <td
                        className={`p-3 font-semibold text-azul-navy sticky left-0 z-10 whitespace-nowrap shadow-xs ${
                          isNonCompliant ? "bg-[#FAF0F6]" : "bg-surface"
                        }`}
                      >
                        {row.sensitive_attribute === "faixa_etaria"
                          ? "Faixa Etária"
                          : row.sensitive_attribute === "genero"
                          ? "Gênero"
                          : "Região"}
                      </td>
                      <td className="p-3 font-medium text-text-primary">
                        {row.group_value}
                      </td>
                      <td className="p-3 font-mono">{row.group_size.toLocaleString("pt-BR")}</td>
                      <td className="p-3 font-mono font-bold text-azul-navy">
                        {(row.selection_rate * 100).toFixed(2)}%
                      </td>
                      <td className="p-3 font-mono font-bold">
                        <span
                          className={
                            isNonCompliant
                              ? "text-magenta-cta text-sm"
                              : isReference
                              ? "text-azul-action"
                              : "text-emerald-700"
                          }
                        >
                          {row.selection_ratio_vs_max.toFixed(4)}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-text-muted">
                        {(row.avg_predicted_churn * 100).toFixed(2)}%
                      </td>
                      <td className="p-3">
                        {isReference && (
                          <span className="inline-flex items-center gap-1 text-azul-action font-bold">
                            ★ Grupo de Referência
                          </span>
                        )}
                        {isNonCompliant && (
                          <span className="inline-flex items-center gap-1 text-magenta-cta font-bold">
                            <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                            Não Conforme (&lt; 0,80)
                          </span>
                        )}
                        {!isReference && !isNonCompliant && !isExcluded && (
                          <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                            <CheckCircle className="h-3.5 w-3.5 shrink-0" />
                            Conforme
                          </span>
                        )}
                        {isExcluded && (
                          <span className="inline-flex items-center gap-1 text-slate-500 italic">
                            ⚪ Fora de Julgamento (LGPD)
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Salvaguardas do Artigo 20 da LGPD */}
      <div className="space-y-3">
        <h3 className="text-base font-bold text-azul-navy flex items-center gap-2">
          <FileText className="h-4 w-4 text-azul-action" />
          <span>Salvaguardas Mandatórias do Artigo 20 da LGPD (Lei nº 13.709/2018)</span>
          <TermHelp term="art_20_lgpd" />
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-4 space-y-2">
            <div className="flex items-center justify-between text-azul-action font-bold text-sm">
              <span className="flex items-center gap-2">
                <UserCheck className="h-4 w-4" />
                1. Direito à Revisão Humana (HITL)
              </span>
              <TermHelp term="hitl" />
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              Toda concessão de bônus ou intervenção sobre cliente de Alto Valor ou risco crítico aciona a flag <code>human_review = true</code>, impedindo o disparo automatizado sem assinatura de operador.
            </p>
          </Card>

          <Card className="p-4 space-y-2">
            <div className="flex items-center justify-between text-azul-action font-bold text-sm">
              <span className="flex items-center gap-2">
                <Eye className="h-4 w-4" />
                2. Direito à Explicação (SHAP)
              </span>
              <TermHelp term="shap" />
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              Disponibilização instantânea dos fatores preditivos SHAP decompostos com rótulos compreensíveis em português, permitindo justificar as deliberações com transparência total.
            </p>
          </Card>

          <Card className="p-4 space-y-2">
            <div className="flex items-center justify-between text-azul-action font-bold text-sm">
              <span className="flex items-center gap-2">
                <Lock className="h-4 w-4" />
                3. Trilha de Auditoria Imutável
              </span>
              <TermHelp term="art_20_lgpd" />
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              Registro em banco relacional e arquivo append-only <code>decisions.jsonl</code> com timestamp UTC, operador autenticado, ID da ação e hash SHA-256 de integridade criptográfica.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
