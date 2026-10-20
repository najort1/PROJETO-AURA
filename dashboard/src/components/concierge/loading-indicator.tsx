"use client";

import * as React from "react";
import { Loader2, Square, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

interface LoadingIndicatorProps {
  elapsedSeconds?: number;
  initialSeconds?: number;
  onAbort?: () => void;
}

const HINT_STEPS = [
  { threshold: 0, text: "Iniciando raciocínio ReAct e formulando hipóteses..." },
  { threshold: 5, text: "Consultando bases analíticas e perfil 360 do cliente..." },
  { threshold: 12, text: "Cruzando regras do regulamento Azul Fidelidade (RAG)..." },
  { threshold: 20, text: "Validando governança de alçadas L1/L2 e antifraude..." },
  { threshold: 30, text: "Sintetizando plano de ação e redigindo resposta final..." },
];

export function LoadingIndicator({
  elapsedSeconds: controlledSeconds,
  initialSeconds = 0,
  onAbort,
}: LoadingIndicatorProps) {
  const [internalSeconds, setInternalSeconds] = React.useState(initialSeconds);

  React.useEffect(() => {
    if (controlledSeconds !== undefined) return;

    const interval = setInterval(() => {
      setInternalSeconds((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [controlledSeconds]);

  const elapsedSeconds = controlledSeconds !== undefined ? controlledSeconds : internalSeconds;

  const currentHint = React.useMemo(() => {
    let hint = HINT_STEPS[0].text;
    for (const step of HINT_STEPS) {
      if (elapsedSeconds >= step.threshold) {
        hint = step.text;
      }
    }
    return hint;
  }, [elapsedSeconds]);

  return (
    <div className="flex items-start gap-3 p-3.5 rounded-xl bg-azul-primary/5 border border-azul-action/20 max-w-2xl text-xs text-text-primary shadow-xs">
      <div className="sr-only">Aura Concierge processando solicitação...</div>

      <div className="size-7 rounded-lg bg-azul-action/10 flex items-center justify-center shrink-0 mt-0.5 text-azul-action">
        <Sparkles className="size-4 animate-pulse motion-reduce:animate-none" aria-hidden="true" />
      </div>

      <div className="flex-1 space-y-1.5 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 font-semibold text-azul-navy">
            <Loader2 className="size-3.5 animate-spin text-azul-action motion-reduce:animate-none" aria-hidden="true" />
            <span>Aura Concierge processando</span>
            <span
              className="font-mono text-[11px] text-text-secondary bg-surface px-1.5 py-0.5 rounded border border-border-subtle"
              aria-hidden="true"
            >
              {elapsedSeconds}s decorridos
            </span>
          </div>

          {onAbort && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onAbort}
              className="h-6 px-2 text-[10px] text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700 cursor-pointer"
              aria-label="Interromper geração de resposta"
            >
              <Square className="size-2.5 fill-current mr-1" aria-hidden="true" />
              Interromper
            </Button>
          )}
        </div>

        <p className="text-[11px] text-text-secondary italic leading-relaxed" aria-hidden="true">
          {currentHint}
        </p>

        <p className="text-[10px] text-slate-500">
          O motor ReAct realiza múltiplos turnos de raciocínio e chamadas a ferramentas corporativas em ambiente local.
        </p>
      </div>
    </div>
  );
}
