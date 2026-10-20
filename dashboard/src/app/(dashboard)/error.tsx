"use client";

import * as React from "react";
import Link from "next/link";
import { AlertTriangle, RotateCcw, Home, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DashboardErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: DashboardErrorProps) {
  React.useEffect(() => {
    // Registro do erro em monitoramento/telemetria
    console.error("Dashboard error boundary capturou exceção:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4">
      <div className="w-full max-w-xl rounded-xl border border-border-subtle bg-surface p-6 sm:p-8 shadow-lg">
        {/* Header Institucional com Ícone de Alerta */}
        <div className="flex items-start gap-4 border-b border-border-subtle pb-5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600 border border-amber-500/20">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-azul-navy tracking-tight">
              Instabilidade no Carregamento do Módulo
            </h2>
            <p className="text-xs text-text-secondary leading-relaxed">
              Ocorreu uma falha inesperada durante a execução deste componente analítico. O estado da sessão e a integridade dos dados permanecem protegidos.
            </p>
          </div>
        </div>

        {/* Diagnóstico Técnico do Erro */}
        <div className="my-5 rounded-lg border border-border-subtle bg-muted/40 p-4 space-y-2">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
            <ShieldAlert className="h-3.5 w-3.5 text-azul-action" />
            <span>Diagnóstico do Sistema</span>
          </div>
          <p className="font-mono text-xs text-text-primary break-all bg-surface/80 p-2.5 rounded border border-border-subtle">
            {error.message || "Erro desconhecido capturado pela camada de integridade."}
          </p>
          {error.digest && (
            <p className="text-[10px] text-text-muted font-mono">
              Código de rastreamento (Digest): {error.digest}
            </p>
          )}
        </div>

        {/* Ações de Recuperação */}
        <div className="flex flex-col-reverse sm:flex-row sm:items-center sm:justify-end gap-3 pt-2">
          <Link href="/carteira" className="w-full sm:w-auto">
            <Button
              variant="outline"
              className="w-full gap-2 border-border-subtle text-xs text-text-secondary hover:text-azul-navy cursor-pointer"
            >
              <Home className="h-4 w-4" />
              Visão da Carteira
            </Button>
          </Link>
          <Button
            onClick={() => reset()}
            className="w-full sm:w-auto gap-2 bg-azul-action hover:bg-azul-action/90 text-white text-xs font-semibold shadow-xs cursor-pointer"
          >
            <RotateCcw className="h-4 w-4" />
            Tentar Novamente
          </Button>
        </div>
      </div>
    </div>
  );
}
