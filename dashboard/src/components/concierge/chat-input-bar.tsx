"use client";

import * as React from "react";
import { Send, Square, RotateCcw, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatInputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (text?: string) => void;
  isLoading: boolean;
  isOnline?: boolean;
  onAbort?: () => void;
  lastFailedPrompt?: string;
  onRetry?: () => void;
}

export function ChatInputBar({
  value,
  onChange,
  onSend,
  isLoading,
  isOnline = true,
  onAbort,
  lastFailedPrompt,
  onRetry,
}: ChatInputBarProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  // Ajusta automaticamente a altura entre 40px e 120px
  React.useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const nextHeight = Math.min(Math.max(el.scrollHeight, 40), 120);
    el.style.height = `${nextHeight}px`;
  }, [value]);

  const hasMountedRef = React.useRef(false);
  const wasLoadingRef = React.useRef(isLoading);

  // Restaura foco automático apenas nas transições de término do loading (não na montagem inicial)
  React.useEffect(() => {
    if (!hasMountedRef.current) {
      hasMountedRef.current = true;
      wasLoadingRef.current = isLoading;
      return;
    }
    if (wasLoadingRef.current && !isLoading) {
      textareaRef.current?.focus();
    }
    wasLoadingRef.current = isLoading;
  }, [isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading && isOnline) {
        onSend();
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim() && !isLoading && isOnline) {
      onSend();
    }
  };

  return (
    <div className="space-y-1.5">
      {/* Banner amigável quando o motor estiver offline */}
      {!isOnline && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-300 text-xs text-amber-900 shadow-xs">
          <AlertTriangle className="size-4 text-amber-700 shrink-0" aria-hidden="true" />
          <div className="flex-1">
            <span className="font-semibold block">Motor Local Desconectado — Operação em Modo Somente Consulta</span>
            <span className="text-[11px] text-amber-800">
              O backend de inferência local (porta 20128) está offline. O envio de novas mensagens e ações autônomas está temporariamente desabilitado.
            </span>
          </div>
        </div>
      )}

      {/* Banner de Retry quando houver prompt que falhou */}
      {lastFailedPrompt && !isLoading && isOnline && (
        <div className="flex items-center justify-between gap-2 px-3 py-1.5 rounded-md bg-amber-50 border border-amber-200 text-xs text-amber-900">
          <span className="truncate">
            <strong>Prompt não enviado:</strong> &quot;{lastFailedPrompt}&quot;
          </span>
          <div className="flex items-center gap-1.5 shrink-0">
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="flex items-center gap-1 text-[11px] font-semibold text-azul-action hover:underline cursor-pointer"
                aria-label="Tentar enviar o prompt anterior novamente"
              >
                <RotateCcw className="size-3" aria-hidden="true" />
                Tentar Novamente
              </button>
            )}
            <button
              type="button"
              onClick={() => onChange(lastFailedPrompt)}
              className="text-[11px] font-medium text-text-secondary hover:text-azul-navy cursor-pointer"
              aria-label="Restaurar texto do prompt anterior para o campo de edição"
            >
              Editar
            </button>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="relative flex items-end gap-2">
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            id="concierge-message-input"
            name="message"
            rows={1}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isOnline
                ? "Digite uma mensagem, comando ou solicitação analítica... (Shift+Enter para quebra de linha)"
                : "Motor local desconectado. Operação em modo somente consulta..."
            }
            aria-label="Mensagem para o Aura Concierge"
            disabled={isLoading || !isOnline}
            className="w-full resize-none rounded-xl border border-border-subtle bg-surface px-3.5 py-2.5 text-xs text-text-primary placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-azul-action/40 disabled:opacity-60 disabled:cursor-not-allowed leading-relaxed shadow-xs transition-colors"
            style={{ maxHeight: "120px", minHeight: "40px" }}
          />
        </div>

        <div className="flex items-center gap-1.5 shrink-0 pb-1">
          {isLoading && onAbort ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onAbort}
              className="h-9 px-3 text-xs border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 cursor-pointer"
              aria-label="Interromper geração atual"
            >
              <Square className="size-3 fill-current mr-1.5" aria-hidden="true" />
              Parar
            </Button>
          ) : (
            <Button
              type="submit"
              disabled={!value.trim() || isLoading || !isOnline}
              size="sm"
              className="h-9 px-3.5 text-xs bg-azul-action text-white hover:bg-azul-action/90 font-medium cursor-pointer shadow-xs disabled:opacity-40"
              aria-label="Enviar mensagem para o Aura Concierge"
            >
              <Send className="size-3.5 mr-1.5" aria-hidden="true" />
              Enviar
            </Button>
          )}
        </div>
      </form>

      <div className="flex items-center justify-between px-1 text-[10px] text-text-secondary">
        <span>
          Pressione <kbd className="font-mono bg-muted px-1 py-0.5 rounded text-azul-navy border border-border-subtle">Enter</kbd> para enviar • <kbd className="font-mono bg-muted px-1 py-0.5 rounded text-azul-navy border border-border-subtle">Shift + Enter</kbd> para nova linha
        </span>
        <span>Aura Agent ReAct v2.0 • 8 Ferramentas</span>
      </div>
    </div>
  );
}
