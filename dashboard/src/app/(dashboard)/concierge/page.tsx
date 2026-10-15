"use client";

import * as React from "react";
import Link from "next/link";
import {
  Sparkles,
  Bot,
  User,
  Send,
  Loader2,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
  Terminal,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Zap,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Plane,
  Gift,
  ArrowRight,
  Database,
  Cpu,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ToolExecution {
  turn?: number;
  tool?: string;
  arguments?: Record<string, any>;
  result_summary?: string;
}

interface DecisionItem {
  timestamp: string;
  customer_id: string;
  action_id: string;
  action_name: string;
  status: string;
  operator?: string;
  final_message: string;
  hash_signature: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  thought_process?: string[];
  tools_executed?: ToolExecution[];
  decisions_taken?: DecisionItem[];
  turns?: number;
  human_review_required?: boolean;
}

const PRESET_CUSTOMERS = [
  { id: "C000030", label: "C000030 (Topázio • Atraso 31m • VaR R$ 2.4k)", atrito: "Atraso operacional em CGB-VCP" },
  { id: "C000032", label: "C000032 (Diamante • Atraso Severo • VaR R$ 9.7k)", atrito: "Atraso de voo e risco de evasão" },
  { id: "C000004", label: "C000004 (Azul • Atraso 70m & Preço • Regional)", atrito: "Atraso no voo AD4015 e queixa de tarifa" },
  { id: "C038454", label: "C038454 (Topázio • Churn 62% • Lazer)", atrito: "Queda de frequência e pontos a expirar" },
];

export default function ConciergeChatPage() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Olá! Sou o **Aura Concierge**, o agente autônomo inteligente do CRM Azul Fidelidade. Conectado ao modelo de raciocínio `principal-combo` (550B parâmetros) com **8 ferramentas corporativas nativas** e matriz de governança L1/L2.\n\nVocê pode me pedir diagnósticos de clientes, investigação de voos com atrito, fundamentação em artigos do regulamento (RAG), concessão de cortesias ou varreduras completas da carteira sem precisar usar o terminal CLI.\n\n**Selecione um cliente sugerido ou digite sua solicitação abaixo:**",
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const [input, setInput] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = React.useState("C000030");
  const [openThoughts, setOpenThoughts] = React.useState<Record<string, boolean>>({});
  const [openTools, setOpenTools] = React.useState<Record<string, boolean>>({});
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const toggleThought = (id: string) => {
    setOpenThoughts((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleTools = (id: string) => {
    setOpenTools((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const sendMessage = async (overrideText?: string, actionType: "chat" | "evaluate" = "chat") => {
    const textToSend = overrideText || input;
    if (!textToSend.trim() || isLoading) return;

    const userMsgId = `user_${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMsgId,
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!overrideText) setInput("");
    setIsLoading(true);

    try {
      const payload = {
        action: actionType,
        message: textToSend,
        customer_id: selectedCustomerId,
        history: messages
          .filter((m) => m.role !== "system" && m.id !== "welcome")
          .map((m) => ({ role: m.role, content: m.content })),
      };

      const res = await fetch("/api/concierge/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      const assistantMsgId = `asst_${Date.now()}`;
      const assistantMessage: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        content: data.reply || (data.error ? `⚠️ **Erro retornado:** ${data.error}` : "Nenhuma resposta gerada."),
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        thought_process: data.thought_process || [],
        tools_executed: data.tools_executed || [],
        decisions_taken: data.decisions_taken || [],
        turns: data.turns || 1,
        human_review_required: data.human_review_required || false,
      };

      // Abre automaticamente pensamentos se houver raciocínio
      if (data.thought_process?.length > 0) {
        setOpenThoughts((prev) => ({ ...prev, [assistantMsgId]: true }));
      }
      if (data.tools_executed?.length > 0) {
        setOpenTools((prev) => ({ ...prev, [assistantMsgId]: true }));
      }

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: "assistant",
          content: `Falha de comunicação com o backend do Concierge: ${err.message}`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (actionPrompt: string, actionType: "chat" | "evaluate" = "chat") => {
    sendMessage(actionPrompt, actionType);
  };

  const clearChat = () => {
    setMessages([
      {
        id: "welcome_reset",
        role: "assistant",
        content:
          "Conversa reiniciada. O Aura Concierge está pronto para novas consultas e comandos com as 8 ferramentas do CRM Azul Fidelidade.",
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  };

  return (
    <div className="space-y-5 pb-8 max-w-6xl mx-auto">
      {/* Header com Telemetria e Badges */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-magenta-cta flex items-center gap-1">
              <Sparkles className="h-3.5 w-3.5" />
              Agente Autônomo Interativo
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="success" className="text-[11px] font-mono flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              principal-combo (Online)
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5 flex items-center gap-2">
            Aura Concierge • Copilot IA em Tempo Real
          </h1>
          <p className="text-sm text-text-secondary">
            Interface direta para administradores conversarem com o LLM, acionarem ferramentas corporativas e homologarem retenção.
          </p>
        </div>

        {/* Telemetria do Motor */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <Badge variant="outline" className="bg-surface text-text-secondary border-border-subtle flex items-center gap-1.5 py-1">
            <Cpu className="h-3.5 w-3.5 text-azul-action" />
            <span>8 Tools Conectadas</span>
          </Badge>
          <Badge variant="outline" className="bg-surface text-text-secondary border-border-subtle flex items-center gap-1.5 py-1">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Autonomia L1/L2</span>
          </Badge>
          <Button variant="outline" size="sm" onClick={clearChat} className="text-xs font-mono h-7 px-2">
            <RefreshCw className="h-3 w-3 mr-1" />
            Limpar Chat
          </Button>
        </div>
      </div>

      {/* Barra de Seleção Rápida de Clientes e Ações Pré-Programadas */}
      <Card className="border-border-subtle bg-surface shadow-xs">
        <CardContent className="p-3.5 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-azul-navy uppercase tracking-wider">
                Cliente Ativo no Contexto:
              </span>
              <select
                value={selectedCustomerId}
                onChange={(e) => setSelectedCustomerId(e.target.value)}
                className="text-xs font-mono font-semibold bg-muted/50 border border-border-subtle rounded-md px-2.5 py-1 text-azul-navy focus:outline-none focus:ring-1 focus:ring-azul-action"
              >
                {PRESET_CUSTOMERS.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleQuickAction(`Avalie completamente o cliente ${selectedCustomerId}, consulte o perfil 360, atritos e tome as ações necessárias de retenção.`, "evaluate")}
                disabled={isLoading}
                className="text-xs font-semibold h-7 bg-azul-action/10 text-azul-action border-azul-action/30 hover:bg-azul-action/20"
              >
                <Zap className="h-3 w-3 mr-1 text-azul-action fill-azul-action" />
                Ciclo Autônomo Completo ({selectedCustomerId})
              </Button>
            </div>
          </div>

          {/* Chips de Ações Rápidas em Linguagem Natural */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-border-subtle/60 text-xs">
            <span className="text-[11px] font-semibold text-text-muted mr-1">Sugestões:</span>
            <button
              onClick={() => handleQuickAction(`Consulte a visão 360 do cliente ${selectedCustomerId} e me diga o tier, CLV, risco de churn e os fatores SHAP dominantes.`)}
              disabled={isLoading}
              className="px-2 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary text-[11px] transition-colors border border-border-subtle/50"
            >
              🔍 Visão 360° & SHAP
            </button>
            <button
              onClick={() => handleQuickAction(`Quais foram os atritos e atrasos de voo recentes enfrentados pelo cliente ${selectedCustomerId}?`)}
              disabled={isLoading}
              className="px-2 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary text-[11px] transition-colors border border-border-subtle/50"
            >
              ✈️ Histórico de Atritos
            </button>
            <button
              onClick={() => handleQuickAction(`Consulte no regulamento oficial quais são as regras de Resgate Especial e teto de pontos para clientes Diamante e Safira.`)}
              disabled={isLoading}
              className="px-2 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary text-[11px] transition-colors border border-border-subtle/50"
            >
              📜 Consultar Regulamento (RAG)
            </button>
            <button
              onClick={() => handleQuickAction(`Liste os 5 clientes de maior valor com atrito recente e risco de perda na carteira.`)}
              disabled={isLoading}
              className="px-2 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary text-[11px] transition-colors border border-border-subtle/50"
            >
              🛡️ Varredura de Risco
            </button>
            <button
              onClick={() => handleQuickAction(`Explique quais são as suas 8 ferramentas e como funcionam as alçadas de Autonomia L1 e L2.`)}
              disabled={isLoading}
              className="px-2 py-0.5 rounded-full bg-muted/60 hover:bg-muted text-text-secondary text-[11px] transition-colors border border-border-subtle/50"
            >
              ℹ️ Catálogo de Ferramentas
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Janela de Mensagens do Chat */}
      <Card className="border-border-subtle bg-surface shadow-xs min-h-[500px] flex flex-col justify-between">
        <CardContent className="p-4 space-y-4 overflow-y-auto max-h-[680px]">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role !== "user" && (
                <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-lg bg-azul-navy text-white shadow-xs">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div className={`space-y-2 max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div className="flex items-center gap-2 text-[11px] text-text-muted">
                  <span className="font-semibold text-azul-navy">
                    {msg.role === "user" ? "Administrador CRM" : "Aura Concierge"}
                  </span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>
                  {msg.turns && msg.turns > 1 && (
                    <Badge variant="outline" className="text-[10px] py-0 px-1 font-mono">
                      {msg.turns} turnos ReAct
                    </Badge>
                  )}
                  {msg.human_review_required && (
                    <Badge variant="destructive" className="text-[10px] py-0 px-1 font-mono flex items-center gap-1">
                      <ShieldAlert className="h-3 w-3" />
                      HITL Ativo
                    </Badge>
                  )}
                </div>

                {/* Bolha de Conteúdo */}
                <div
                  className={`rounded-xl p-4 text-xs leading-relaxed space-y-2.5 ${
                    msg.role === "user"
                      ? "bg-azul-action text-white rounded-tr-none shadow-xs"
                      : "bg-muted/40 border border-border-subtle text-text-primary rounded-tl-none shadow-xs"
                  }`}
                >
                  <div className="whitespace-pre-wrap font-sans space-y-1.5">
                    {msg.content}
                  </div>
                </div>

                {/* Bloco Retrátil: Raciocínio Analítico (Thought Process) */}
                {msg.thought_process && msg.thought_process.length > 0 && (
                  <div className="rounded-lg border border-border-subtle bg-surface text-xs overflow-hidden">
                    <button
                      onClick={() => toggleThought(msg.id)}
                      className="w-full flex items-center justify-between p-2.5 bg-muted/30 hover:bg-muted/50 text-[11px] font-mono font-bold text-azul-navy transition-colors"
                    >
                      <span className="flex items-center gap-1.5">
                        <Terminal className="h-3.5 w-3.5 text-azul-action" />
                        Raciocínio Analítico Interno ({msg.thought_process.length} ponderações)
                      </span>
                      {openThoughts[msg.id] ? (
                        <ChevronDown className="h-3.5 w-3.5 text-text-muted" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5 text-text-muted" />
                      )}
                    </button>
                    {openThoughts[msg.id] && (
                      <div className="p-3 bg-muted/10 space-y-2 border-t border-border-subtle font-mono text-[11px] text-text-secondary leading-relaxed">
                        {msg.thought_process.map((t, idx) => (
                          <div key={idx} className="p-2 bg-surface rounded border border-border-subtle/60 whitespace-pre-wrap">
                            <span className="text-azul-action font-bold block mb-1">Passo #{idx + 1}:</span>
                            {t}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Bloco Retrátil: Ferramentas Corporativas Executadas */}
                {msg.tools_executed && msg.tools_executed.length > 0 && (
                  <div className="rounded-lg border border-border-subtle bg-surface text-xs overflow-hidden">
                    <button
                      onClick={() => toggleTools(msg.id)}
                      className="w-full flex items-center justify-between p-2.5 bg-azul-action/5 hover:bg-azul-action/10 text-[11px] font-mono font-bold text-azul-navy transition-colors"
                    >
                      <span className="flex items-center gap-1.5">
                        <Cpu className="h-3.5 w-3.5 text-azul-action" />
                        Ferramentas Executadas com Sucesso ({msg.tools_executed.length})
                      </span>
                      {openTools[msg.id] ? (
                        <ChevronDown className="h-3.5 w-3.5 text-text-muted" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5 text-text-muted" />
                      )}
                    </button>
                    {openTools[msg.id] && (
                      <div className="p-3 bg-azul-action/5 space-y-2 border-t border-border-subtle font-mono text-[11px]">
                        {msg.tools_executed.map((t, idx) => (
                          <div key={idx} className="p-2.5 bg-surface rounded border border-azul-action/20 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-azul-navy flex items-center gap-1">
                                <Zap className="h-3 w-3 text-azul-action" />
                                {t.tool || "ferramenta"}
                              </span>
                              <span className="text-[10px] text-text-muted">Turno {t.turn || 1}</span>
                            </div>
                            <div className="text-[10px] text-text-muted truncate">
                              <strong>Args:</strong> {JSON.stringify(t.arguments || {})}
                            </div>
                            {t.result_summary && (
                              <div className="text-[10px] text-text-secondary bg-muted/40 p-1.5 rounded truncate">
                                <strong>Resultado:</strong> {t.result_summary}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Cards de Decisões Registradas na Base de Auditoria */}
                {msg.decisions_taken && msg.decisions_taken.length > 0 && (
                  <div className="space-y-2 pt-1">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                      Decisões Gravadas na Esteira (decisions.jsonl):
                    </span>
                    <div className="grid grid-cols-1 gap-2">
                      {msg.decisions_taken.map((dec, idx) => {
                        const isApproved = dec.status === "approved";
                        const isReview = dec.status === "in_review";
                        return (
                          <div
                            key={idx}
                            className={`p-3 rounded-lg border text-xs space-y-1.5 ${
                              isApproved
                                ? "bg-emerald-50/60 border-emerald-300"
                                : isReview
                                ? "bg-amber-50/60 border-amber-300"
                                : "bg-muted/40 border-border-subtle"
                            }`}
                          >
                            <div className="flex flex-wrap items-center justify-between gap-1">
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-azul-navy">
                                  {dec.customer_id}
                                </span>
                                <Badge variant="outline" className="font-mono text-[10px]">
                                  {dec.action_id}
                                </Badge>
                              </div>

                              <Badge
                                variant={isApproved ? "success" : isReview ? "warning" : "secondary"}
                                className="text-[10px] uppercase font-mono font-bold"
                              >
                                {isApproved ? "L1 • Aprovado" : isReview ? "L2 • Em Revisão (HITL)" : dec.status}
                              </Badge>
                            </div>

                            <p className="text-[11px] text-text-primary italic border-l-2 border-azul-action pl-2">
                              &quot;{dec.final_message}&quot;
                            </p>

                            <div className="flex flex-wrap items-center justify-between gap-1 pt-1 border-t border-border-subtle/50 text-[10px] text-text-muted font-mono">
                              <span title={dec.hash_signature}>
                                SHA-256: {dec.hash_signature.substring(0, 16)}...
                              </span>
                              <Link
                                href="/agente"
                                className="text-azul-action hover:underline font-sans font-semibold flex items-center gap-0.5"
                              >
                                Ver no Kanban
                                <ExternalLink className="h-2.5 w-2.5" />
                              </Link>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-lg bg-azul-action text-white shadow-xs">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-azul-navy text-white shadow-xs">
                <Bot className="h-4 w-4" />
              </div>
              <div className="p-4 rounded-xl bg-muted/40 border border-border-subtle rounded-tl-none space-y-2">
                <div className="flex items-center gap-2 text-xs text-text-secondary font-mono">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-azul-action" />
                  <span>Aura Concierge raciocinando e executando ferramentas ReAct...</span>
                </div>
                <div className="text-[11px] text-text-muted font-sans">
                  Consultando base DuckDB, avaliando atritos operacionais e calculando alçadas L1/L2 com guardrails.
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>

        {/* Input Bar e Disparo */}
        <div className="p-3 border-t border-border-subtle bg-surface rounded-b-xl space-y-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            className="flex items-center gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Pergunte algo ou solicite uma ação (ex: "Verifique o cliente ${selectedCustomerId} e emita um voucher de Espaço Azul se elegível")...`}
              disabled={isLoading}
              className="text-xs h-10 bg-muted/30 focus-visible:ring-azul-action"
            />
            <Button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="h-10 px-4 bg-azul-action hover:bg-azul-action/90 text-white font-semibold text-xs"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>

          <div className="flex flex-wrap items-center justify-between text-[11px] text-text-muted px-1">
            <span className="flex items-center gap-1">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              Idempotência e teto orçamentário ativos • LGPD Art. 20 Compliant
            </span>
            <span className="font-mono">
              Modelo: <strong>principal-combo</strong> @ :20128/v1
            </span>
          </div>
        </div>
      </Card>
    </div>
  );
}
