"use client";

import * as React from "react";
import { Bot, User, ShieldAlert, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { MarkdownRenderer } from "./markdown-renderer";
import { ThoughtAccordion } from "./thought-accordion";
import { ToolsAccordion } from "./tools-accordion";
import { DecisionsList } from "./decisions-list";
import type { ChatMessage, DecisionItem } from "@/types/concierge";

// Rastreia mensagens cujo typewriter já foi concluído nesta sessão (evita re-animação em remounts sem re-escrever no state/storage)
const completedStreamingIds = new Set<string>();

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

  const alreadyCompleted = completedStreamingIds.has(message.id);
  const shouldAnimate = Boolean(message.isStreaming) && !alreadyCompleted && !isUser && !isSystem;

  const [isTyping, setIsTyping] = React.useState<boolean>(() => {
    if (!shouldAnimate) return false;
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      completedStreamingIds.add(message.id);
      return false;
    }
    return true;
  });

  const [displayedContent, setDisplayedContent] = React.useState<string>(() => {
    if (!shouldAnimate) return message.content;
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return message.content;
    }
    return "";
  });

  React.useEffect(() => {
    if (!shouldAnimate) {
      setDisplayedContent(message.content);
      setIsTyping(false);
      return;
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      completedStreamingIds.add(message.id);
      setDisplayedContent(message.content);
      setIsTyping(false);
      return;
    }

    let i = 0;
    const len = message.content.length;
    const step = Math.max(1, Math.floor(len / 35));
    const timer = setInterval(() => {
      i += step;
      if (i >= len) {
        completedStreamingIds.add(message.id);
        setDisplayedContent(message.content);
        setIsTyping(false);
        clearInterval(timer);
      } else {
        setDisplayedContent(message.content.slice(0, i));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [shouldAnimate, message.content, message.id]);

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

        {/* Bolha de Conteúdo Principal */}
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
          ) : isTyping ? (
            <>
              <div aria-hidden="true">
                <MarkdownRenderer content={displayedContent} />
              </div>
              <span className="sr-only">Aura Concierge gerando resposta...</span>
            </>
          ) : (
            <MarkdownRenderer content={message.content} />
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
