"use client";

import * as React from "react";
import { ChevronDown, ChevronRight, Cpu, Zap, Copy, Check } from "lucide-react";
import { toast } from "sonner";
import type { ToolExecution } from "@/types/concierge";

interface ToolsAccordionProps {
  id: string;
  tools: ToolExecution[];
}

export function ToolsAccordion({ id, tools }: ToolsAccordionProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [copiedIndex, setCopiedIndex] = React.useState<number | null>(null);
  const [expandedArgs, setExpandedArgs] = React.useState<Record<number, boolean>>({});
  const contentId = `tools-content-${id}`;

  if (!tools || tools.length === 0) return null;

  const toggleArgExpansion = (idx: number) => {
    setExpandedArgs((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleCopyArgs = async (t: ToolExecution, idx: number) => {
    const jsonStr = JSON.stringify(t.arguments || {}, null, 2);
    try {
      await navigator.clipboard.writeText(jsonStr);
      setCopiedIndex(idx);
      toast.success("Argumentos da ferramenta copiados!");
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch {
      toast.error("Não foi possível copiar os argumentos.");
    }
  };

  return (
    <div className="mt-2.5 rounded-md border border-azul-action/20 overflow-hidden bg-surface">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-controls={contentId}
        className="w-full flex items-center justify-between p-2.5 bg-azul-action/5 hover:bg-azul-action/10 text-[11px] font-mono font-bold text-azul-navy transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-azul-action cursor-pointer"
      >
        <span className="flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5 text-azul-action" aria-hidden="true" />
          Ferramentas Executadas com Sucesso ({tools.length})
        </span>
        {isOpen ? (
          <ChevronDown className="h-3.5 w-3.5 text-text-secondary" aria-hidden="true" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-text-secondary" aria-hidden="true" />
        )}
      </button>

      <div
        id={contentId}
        hidden={!isOpen}
        className={`p-3 bg-azul-action/5 space-y-2 border-t border-border-subtle font-mono text-[11px] ${
          !isOpen ? "hidden" : ""
        }`}
      >
          {tools.map((t, idx) => {
            const hasArgs = t.arguments && Object.keys(t.arguments).length > 0;
            const isArgsOpen = expandedArgs[idx] ?? true;
            const isCopied = copiedIndex === idx;

            return (
              <div
                key={`tool-${id}-${t.call_id || idx}`}
                className="p-2.5 bg-surface rounded border border-azul-action/20 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-azul-navy flex items-center gap-1">
                    <Zap className="h-3 w-3 text-azul-action" aria-hidden="true" />
                    {t.tool || "ferramenta"}
                  </span>
                  <span className="text-[10px] text-text-secondary">Turno {t.turn || 1}</span>
                </div>

                {hasArgs && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-text-secondary">
                      <button
                        type="button"
                        onClick={() => toggleArgExpansion(idx)}
                        className="flex items-center gap-1 font-semibold text-azul-action hover:underline focus-visible:outline-none cursor-pointer"
                        aria-expanded={isArgsOpen}
                        aria-label={`Alternar visualização de argumentos de ${t.tool || "ferramenta"}`}
                      >
                        <span>Argumentos JSON</span>
                        {isArgsOpen ? (
                          <ChevronDown className="h-2.5 w-2.5" aria-hidden="true" />
                        ) : (
                          <ChevronRight className="h-2.5 w-2.5" aria-hidden="true" />
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => handleCopyArgs(t, idx)}
                        aria-label={`Copiar argumentos JSON de ${t.tool || "ferramenta"}`}
                        className="flex items-center gap-1 hover:text-azul-navy transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-azul-action px-1 py-0.5 rounded cursor-pointer"
                      >
                        {isCopied ? (
                          <>
                            <Check className="h-3 w-3 text-emerald-600" aria-hidden="true" />
                            <span className="text-emerald-700 font-semibold">Copiado</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" aria-hidden="true" />
                            <span>Copiar JSON</span>
                          </>
                        )}
                      </button>
                    </div>

                    {isArgsOpen && (
                      <pre className="rounded bg-[#0B1E2E] text-slate-100 p-2 text-[10px] overflow-x-auto border border-azul-navy/30 leading-relaxed font-mono whitespace-pre">
                        {JSON.stringify(t.arguments, null, 2)}
                      </pre>
                    )}
                  </div>
                )}

                {t.result_summary && (
                  <div className="text-[10px] text-text-secondary bg-muted/40 p-2 rounded border border-border-subtle/60 leading-relaxed break-words">
                    <strong className="text-azul-navy font-semibold">Resultado: </strong>
                    <span>{t.result_summary}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
    </div>
  );
}
