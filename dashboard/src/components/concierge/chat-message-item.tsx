"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import { Bot, User, ShieldAlert, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ThoughtAccordion } from "./thought-accordion";
import { ToolsAccordion } from "./tools-accordion";
import { DecisionsList } from "./decisions-list";
import type { ChatMessage, DecisionItem } from "@/types/concierge";

// Fallback único compartilhado: idêntico durante SSR (Suspense) e no cliente (dynamic loading)
function MarkdownFallback() {
  return (
    <div className="text-xs text-text-secondary animate-pulse" aria-hidden="true">
      Carregando mensagem...
    </div>
  );
}

const MarkdownRenderer = dynamic(
  () => import("./markdown-renderer").then((mod) => mod.MarkdownRenderer),
  {
    ssr: false,
    loading: () => <MarkdownFallback />,
  }
);

interface ChatMessageItemProps {
  message: ChatMessage;
  onDecisionUpdate?: (messageId: string, decisionIndex: number, newStatus: DecisionItem["status"]) => void;
  onRetryMessage?: () => void;
}

export const ChatMessageItem = React.memo(function ChatMessageItem({
  message,
  onDecisionUpdate,
  onRetryMessage,
}: ChatMessageItemProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <div className="rounded-lg border border-amber-200/80 bg-amber-50/80 px-3.5 py-2 text-[11px] text-amber-900 flex items-center gap-2 max-w-xl">
          <AlertTriangle className="size-3.5 text-amber-700 shrink-0" aria-hidden="true" />
          <p className="leading-relaxed break-words">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-2.5 sm:gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div
          className={`flex size-8 shrink-0 select-none items-center justify-center rounded-lg shadow-xs mt-0.5 ${
            message.isError ? "bg-red-600 text-white" : "bg-azul-navy text-white"
          }`}
          aria-hidden="true"
        >
          {message.isError ? <ShieldAlert className="size-4" /> : <Bot className="size-4" />}
        </div>
      )}

      <div className={`space-y-2 max-w-[90%] sm:max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
        {/* Metadados da Mensagem */}
        <div className={`flex items-center gap-2 text-[11px] text-text-secondary ${isUser ? "justify-end" : "justify-start"}`}>
          <span className="font-semibold text-azul-navy">
            {isUser ? "Administrador CRM" : "Aura Concierge"}
          </span>
          <span aria-hidden="true">•</span>
          <time dateTime={message.timestamp}>{message.timestamp}</time>

          {message.turns && message.turns > 1 && (
            <Badge variant="outline" className="text-[10px] py-0 px-1 font-mono text-text-secondary">
              {message.turns} turnos ReAct
            </Badge>
          )}

          {message.human_review_required && (
            <Badge variant="destructive" className="text-[10px] py-0 px-1 font-mono flex items-center gap-1">
              <ShieldAlert className="size-3" aria-hidden="true" />
              HITL Ativo
            </Badge>
          )}

          {message.isError && (
            <Badge variant="destructive" className="text-[10px] py-0 px-1 font-mono">
              Falha de Execução
            </Badge>
          )}
        </div>

        {/* Bolha de Conteúdo Principal (Renderização direta sem falso efeito typewriter ou aria-hidden) */}
        <div
          className={`rounded-xl p-3.5 sm:p-4 text-xs leading-relaxed space-y-2 shadow-xs transition-colors ${
            isUser
              ? "bg-azul-action text-white rounded-tr-none"
              : message.isError
              ? "bg-red-50/70 border border-red-200 text-red-950 rounded-tl-none"
              : "bg-surface border border-border-subtle text-text-primary rounded-tl-none"
          }`}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap font-sans space-y-1.5 break-words">{message.content}</div>
          ) : (
            // Suspense boundary absorve o bailout de SSR do next/dynamic (ssr:false)
            // sem transformá-lo em erro 500 no render do servidor.
            <React.Suspense fallback={<MarkdownFallback />}>
              <MarkdownRenderer content={message.content} />
            </React.Suspense>
          )}

          {/* Botão de retry caso seja erro com possibilidade de retentativa */}
          {message.isError && onRetryMessage && (
            <div className="pt-2 border-t border-red-200/60 flex items-center justify-between">
              <span className="text-[10px] text-red-700">A execução encontrou um erro no motor local.</span>
              <button
                type="button"
                onClick={onRetryMessage}
                className="text-[11px] font-semibold text-azul-action hover:underline cursor-pointer"
              >
                Tentar Novamente
              </button>
            </div>
          )}
        </div>

        {/* Acordeão de Raciocínio ReAct */}
        {message.thought_process && message.thought_process.length > 0 && (
          <ThoughtAccordion id={message.id} thoughtProcess={message.thought_process} />
        )}

        {/* Acordeão de Ferramentas Executadas */}
        {message.tools_executed && message.tools_executed.length > 0 && (
          <ToolsAccordion id={message.id} tools={message.tools_executed} />
        )}

        {/* Lista de Decisões Auditáveis com HITL inline */}
        {message.decisions_taken && message.decisions_taken.length > 0 && (
          <DecisionsList
            messageId={message.id}
            decisions={message.decisions_taken}
            onDecisionUpdate={onDecisionUpdate}
          />
        )}
      </div>

      {isUser && (
        <div
          className="flex size-8 shrink-0 select-none items-center justify-center rounded-lg bg-azul-primary/20 text-azul-navy shadow-xs mt-0.5"
          aria-hidden="true"
        >
          <User className="size-4" />
        </div>
      )}
    </div>
  );
});
