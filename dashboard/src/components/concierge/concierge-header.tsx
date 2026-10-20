"use client";

import * as React from "react";
import { Sparkles, CheckCircle2, ShieldAlert, ShieldCheck, Cpu, RefreshCw, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ConciergeTelemetry } from "@/types/concierge";

interface ConciergeHeaderProps {
  telemetry: ConciergeTelemetry | null;
  isLoadingTelemetry?: boolean;
  onClearChat: () => void;
  isOnline?: boolean;
}

export function ConciergeHeader({
  telemetry,
  isLoadingTelemetry = false,
  onClearChat,
  isOnline: isOnlineProp,
}: ConciergeHeaderProps) {
  const isOnline = typeof isOnlineProp === "boolean" ? isOnlineProp : telemetry?.status === "online";
  const modelName = telemetry?.model || "principal-combo";
  const toolsCount = telemetry?.tools_available?.length ?? 8;

  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2 border-b border-border-subtle">
      <div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-[#B81D7D] flex items-center gap-1">
            <Sparkles className="size-3" aria-hidden="true" />
            Agente Autônomo Interativo
          </span>
          <span className="text-border-subtle">•</span>
          {isLoadingTelemetry ? (
            <Badge variant="outline" className="text-[10px] font-mono flex items-center gap-1">
              <Loader2 className="size-2.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
              Sincronizando...
            </Badge>
          ) : isOnline ? (
            <Badge variant="success" className="text-[10px] font-mono flex items-center gap-1">
              <CheckCircle2 className="size-2.5" aria-hidden="true" />
              {modelName} (Online)
            </Badge>
          ) : (
            <Badge variant="destructive" className="text-[10px] font-mono flex items-center gap-1">
              <ShieldAlert className="size-2.5" aria-hidden="true" />
              Motor Desconectado (Modo Consulta)
            </Badge>
          )}
        </div>
        <h1 className="text-lg sm:text-xl font-extrabold text-azul-navy tracking-tight mt-0.5">
          Aura Concierge • Copilot IA em Tempo Real
        </h1>
      </div>

      {/* Telemetria do Motor e Ações */}
      <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
        <Badge
          variant="outline"
          className="bg-surface text-text-secondary border-border-subtle flex items-center gap-1 text-[11px] py-1"
          title={telemetry?.tools_available?.join(", ")}
        >
          <Cpu className="size-3 text-azul-action" aria-hidden="true" />
          <span>{toolsCount} Tools Conectadas</span>
        </Badge>

        <Badge
          variant="outline"
          className="bg-surface text-text-secondary border-border-subtle flex items-center gap-1 text-[11px] py-1"
        >
          <ShieldCheck className="size-3 text-emerald-600" aria-hidden="true" />
          <span>Autonomia L1/L2</span>
        </Badge>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onClearChat}
          className="text-xs font-mono h-7 px-2.5 hover:bg-muted cursor-pointer"
          aria-label="Limpar histórico de mensagens do chat"
        >
          <RefreshCw className="size-3 mr-1 text-text-secondary" aria-hidden="true" />
          Limpar
        </Button>
      </div>
    </header>
  );
}
