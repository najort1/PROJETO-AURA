import * as React from "react";
import {
  Bot,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Send,
  Layers,
  BookOpen,
  CheckCircle2,
  Phone,
  Mail,
  MessageSquare,
  Bell,
  FileCheck2,
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
import {
  getKanbanBoard,
  getAgentRecommendations,
} from "@/lib/data/reader";
import { KanbanBoard } from "@/components/kanban/kanban-board";
import { TermHelp } from "@/components/help/term-help";

export const metadata = {
  title: "04 · Cockpit Agente & Kanban | PROJETO AURA 2.0",
  description: "Recomendações NBA, citações formais RAG e esteira de retenção Kanban",
};

export default async function AgentePage() {
  const [kanbanBoard, recommendations] = await Promise.all([
    getKanbanBoard(),
    getAgentRecommendations(),
  ]);

  // Exemplo em destaque de NBA com citação de regulamento
  const featuredRec =
    recommendations.find((r) => r.citations.length > 0) || recommendations[0];

  const getChannelIcon = (channel: string) => {
    switch (channel.toLowerCase()) {
      case "whatsapp":
        return <MessageSquare className="h-4 w-4 text-emerald-600" />;
      case "email":
        return <Mail className="h-4 w-4 text-azul-action" />;
      case "push":
        return <Bell className="h-4 w-4 text-amber-500" />;
      case "telefone":
        return <Phone className="h-4 w-4 text-azul-deep" />;
      default:
        return <Send className="h-4 w-4 text-text-muted" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-magenta-cta">
              Módulo 04
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="destructive" className="text-[11px] font-mono flex items-center gap-1">
              <span>HITL Ativo (Art. 20 LGPD)</span>
              <TermHelp term="hitl" />
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5 flex items-center gap-2">
            <span>Cockpit do Agente de Retenção & Pipeline Kanban</span>
            <TermHelp term="nba" />
          </h1>
          <p className="text-sm text-text-secondary">
            Despacho assistido por IA, citações regulatórias fact-checked e esteira operacional ágil.
          </p>
        </div>
      </div>

      {/* Destaque de Cockpit NBA & Auditoria de Regulamento (RAG Fact Verification) */}
      {featuredRec && (
        <Card className="border-l-4 border-l-azul-action shadow-xs">
          <CardHeader className="pb-3 border-b border-border-subtle">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-azul-action/10 text-azul-action">
                  <Bot className="h-5 w-5" />
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-azul-navy">
                      {featuredRec.customer_id}
                    </span>
                    <Badge variant="outline" className="font-mono text-[11px] flex items-center gap-1">
                      <span>{featuredRec.action_id}</span>
                      <TermHelp term="nba" />
                    </Badge>
                    <span className="flex items-center gap-1 text-xs text-text-muted">
                      {getChannelIcon(featuredRec.channel)}
                      <span className="uppercase font-semibold">{featuredRec.channel}</span>
                    </span>
                  </div>
                  <CardTitle className="text-base text-azul-navy mt-0.5">
                    {featuredRec.action_name}
                  </CardTitle>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant="success" className="text-xs font-mono">
                  Confiança: {(featuredRec.confidence * 100).toFixed(1)}%
                </Badge>
                {featuredRec.human_review && (
                  <Badge variant="destructive" className="flex items-center gap-1">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    <span>Revisão HITL Mandatória</span>
                    <TermHelp term="hitl" />
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent className="pt-4 space-y-4">
            {/* Mensagem Gerada */}
            <div className="rounded-lg bg-muted/40 p-4 border border-border-subtle space-y-1.5">
              <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider block">
                Mensagem Sugerida pelo Agente:
              </span>
              <p className="text-xs text-text-primary leading-relaxed font-sans">
                &quot;{featuredRec.message}&quot;
              </p>
            </div>

            {/* Citações Auditáveis de Regulamento (Fact-Checking RAG) */}
            {featuredRec.citations && featuredRec.citations.length > 0 && (
              <div className="space-y-2 border-t border-border-subtle pt-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-azul-navy flex items-center gap-1.5">
                    <FileCheck2 className="h-4 w-4 text-azul-action" />
                    Citação Formal do Regulamento (Fact Verification Auditável)
                  </span>
                  <span className="font-mono text-[10px] text-text-muted">
                    Snapshot: {featuredRec.snapshot_version || "research-2026-10-12"}
                  </span>
                </div>

                <div className="space-y-2">
                  {featuredRec.citations.map((cit, idx) => (
                    <div
                      key={idx}
                      className="rounded-md border border-azul-action/20 bg-azul-action/5 p-3 text-xs space-y-1.5"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-1 text-[11px]">
                        <span className="font-mono font-bold text-azul-navy">
                          FACT-ID: {cit.fact_id}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-text-muted">
                            Vigência: {cit.valid_from}
                          </span>
                          <Badge variant="success" className="text-[10px] py-0 px-1.5">
                            {cit.verification_status}
                          </Badge>
                        </div>
                      </div>
                      <p className="italic text-text-secondary border-l-2 border-azul-action pl-2.5 py-0.5">
                        &quot;{cit.quote || cit.text || cit.source_label || "Citação oficial do regulamento"}&quot;
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Pipeline Kanban de Retenção */}
      <div className="space-y-3 pt-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-azul-navy flex items-center gap-2">
              <Layers className="h-5 w-5 text-azul-action" />
              Pipeline Kanban de Retenção CRM
            </h2>
            <p className="text-xs text-text-secondary">
              Arraste os cards entre os estágios para atualizar a esteira com sincronização transacional em <code>decisions.jsonl</code>.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-text-muted font-mono">
            <span>Audit Trail: Dual-Write Ativo</span>
          </div>
        </div>

        {/* Quadro Interativo */}
        <KanbanBoard initialState={kanbanBoard} />
      </div>
    </div>
  );
}
