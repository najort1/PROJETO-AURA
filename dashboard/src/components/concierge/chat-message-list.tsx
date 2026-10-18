"use client";

import * as React from "react";
import { ArrowDown } from "lucide-react";
import { ChatMessageItem } from "./chat-message-item";
import { LoadingIndicator } from "./loading-indicator";
import type { ChatMessage, DecisionItem } from "@/types/concierge";

interface ChatMessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
  elapsedSeconds: number;
  onAbort?: () => void;
  onDecisionUpdate?: (messageId: string, decisionIndex: number, newStatus: DecisionItem["status"]) => void;
  onRetryMessage?: () => void;
}

export const ChatMessageList = React.memo(function ChatMessageList({
  messages,
  isLoading,
  elapsedSeconds,
  onAbort,
  onDecisionUpdate,
  onRetryMessage,
}: ChatMessageListProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = React.useState(true);
  const isAtBottomRef = React.useRef(isAtBottom);
  isAtBottomRef.current = isAtBottom;

  const [hasUnreadBelow, setHasUnreadBelow] = React.useState(false);
  const prevMessagesCountRef = React.useRef(messages.length);

  const checkIsAtBottom = React.useCallback(() => {
    const el = containerRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 64;
  }, []);

  const handleScroll = React.useCallback(() => {
    const atBottom = checkIsAtBottom();
    setIsAtBottom(atBottom);
    if (atBottom) {
      setHasUnreadBelow(false);
    }
  }, [checkIsAtBottom]);

  const scrollToBottom = React.useCallback((smooth = true) => {
    const el = containerRef.current;
    if (!el) return;
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    el.scrollTo({
      top: el.scrollHeight,
      behavior: smooth && !prefersReduced ? "smooth" : "auto",
    });
    setIsAtBottom(true);
    setHasUnreadBelow(false);
  }, []);

  // Auto-scroll inteligente: sincroniza prevMessagesCountRef e reseta hasUnreadBelow em reduções de lista (ex: limpar chat)
  React.useEffect(() => {
    if (messages.length > prevMessagesCountRef.current) {
      if (isAtBottom) {
        scrollToBottom();
      } else {
        setHasUnreadBelow(true);
      }
    } else if (messages.length <= 1 || messages.length < prevMessagesCountRef.current) {
      setHasUnreadBelow(false);
    }
    prevMessagesCountRef.current = messages.length;
  }, [messages.length, isAtBottom, scrollToBottom]);

  // Se entrar em estado de carregamento e o usuário estava no fundo, acompanha
  React.useEffect(() => {
    if (isLoading && isAtBottom) {
      scrollToBottom();
    }
  }, [isLoading, isAtBottom, scrollToBottom]);

  // ResizeObserver para acompanhar expansão vertical do efeito typewriter da última mensagem
  React.useEffect(() => {
    const container = containerRef.current;
    if (!container || typeof ResizeObserver === "undefined") return;

    const observer = new ResizeObserver(() => {
      if (isAtBottomRef.current) {
        const prefersReduced =
          typeof window !== "undefined" &&
          window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        container.scrollTo({
          top: container.scrollHeight,
          behavior: prefersReduced ? "auto" : "smooth",
        });
      }
    });

    const lastChild = container.lastElementChild;
    if (lastChild) {
      observer.observe(lastChild);
    }

    return () => {
      observer.disconnect();
    };
  }, [messages, isLoading]);

  return (
    <div className="relative flex-1 min-h-0 flex flex-col">
      <div
        ref={containerRef}
        onScroll={handleScroll}
        role="log"
        aria-live="polite"
        aria-label="Histórico de mensagens do chat"
        className="flex-1 overflow-y-auto overscroll-contain min-h-0 p-3 sm:p-4 space-y-4"
      >
        {messages.map((msg) => (
          <ChatMessageItem
            key={msg.id}
            message={msg}
            onDecisionUpdate={onDecisionUpdate}
            onRetryMessage={onRetryMessage}
          />
        ))}

        {isLoading && (
          <LoadingIndicator elapsedSeconds={elapsedSeconds} onAbort={onAbort} />
        )}
      </div>

      {/* Botão flutuante para rolar para as novas mensagens */}
      {hasUnreadBelow && (
        <div className="absolute bottom-3 right-4 z-10 pointer-events-auto">
          <button
            type="button"
            onClick={() => scrollToBottom(true)}
            aria-label="Rolar até as mensagens mais recentes"
            className="flex items-center gap-1.5 rounded-full bg-azul-navy text-white px-3 py-1.5 text-xs font-semibold shadow-lg hover:bg-azul-deep transition-all cursor-pointer animate-bounce motion-reduce:animate-none"
          >
            <ArrowDown className="size-3.5" aria-hidden="true" />
            <span>Novas mensagens</span>
          </button>
        </div>
      )}
    </div>
  );
});
