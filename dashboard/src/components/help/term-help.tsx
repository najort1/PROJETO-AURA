"use client";

import * as React from "react";
import { HelpCircle } from "lucide-react";
import { GLOSSARY, type GlossaryTermKey } from "@/lib/constants/glossary";
import { useHelpSettings } from "@/contexts/help-settings-context";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export interface TermHelpProps {
  term: GlossaryTermKey;
  children?: React.ReactNode;
  showIcon?: boolean;
  className?: string;
  side?: "top" | "right" | "bottom" | "left";
  align?: "start" | "center" | "end";
}

export function TermHelp({
  term,
  children,
  showIcon = true,
  className,
  side = "top",
  align = "center",
}: TermHelpProps) {
  const { showTooltips } = useHelpSettings();
  const termData = GLOSSARY[term];

  if (!termData) {
    return children ? <>{children}</> : null;
  }

  // Se o dicionário estiver desativado pelo usuário
  if (!showTooltips) {
    return children ? <>{children}</> : null;
  }

  const tooltipBody = (
    <TooltipContent
      side={side}
      align={align}
      className="max-w-xs sm:max-w-sm p-3.5 space-y-2 bg-surface text-text-primary border border-border-subtle shadow-xl rounded-lg text-left z-50 pointer-events-auto"
    >
      <div className="flex items-start justify-between gap-2 border-b border-border-subtle pb-1.5">
        <span className="font-bold text-xs text-azul-navy tracking-tight leading-tight">
          {termData.title}
        </span>
        <span className="shrink-0 text-[10px] font-semibold text-azul-action bg-accent px-1.5 py-0.5 rounded">
          {termData.category}
        </span>
      </div>

      <p className="text-xs text-text-primary leading-relaxed font-normal">
        {termData.shortDefinition}
      </p>

      {termData.details && (
        <p className="text-[11px] text-text-secondary leading-snug">
          {termData.details}
        </p>
      )}

      {termData.formula && (
        <div className="rounded bg-muted/70 p-2 border border-border-subtle space-y-0.5">
          <span className="block text-[9px] uppercase font-bold text-text-muted tracking-wider">
            Fórmula Canônica:
          </span>
          <code className="text-[10px] font-mono text-azul-navy break-all font-semibold block">
            {termData.formula}
          </code>
        </div>
      )}
    </TooltipContent>
  );

  return (
    <Tooltip>
      {children ? (
        showIcon ? (
          <span className={cn("inline-flex items-center gap-1 align-middle", className)}>
            {children}
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={(e) => e.stopPropagation()}
                aria-label={`Ajuda sobre ${termData.title}`}
                className="inline-flex items-center justify-center text-text-muted hover:text-azul-action transition-colors rounded-full p-0.5 cursor-help focus:outline-none focus-visible:ring-1 focus-visible:ring-azul-action"
              >
                <HelpCircle className="h-3.5 w-3.5 shrink-0" />
              </button>
            </TooltipTrigger>
          </span>
        ) : (
          <TooltipTrigger asChild>
            <span
              onClick={(e) => e.stopPropagation()}
              className={cn(
                "inline-flex items-center cursor-help border-b border-dotted border-border-dark hover:border-azul-action transition-colors",
                className
              )}
            >
              {children}
            </span>
          </TooltipTrigger>
        )
      ) : (
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={(e) => e.stopPropagation()}
            aria-label={`Ajuda sobre ${termData.title}`}
            className={cn(
              "inline-flex items-center justify-center text-text-muted hover:text-azul-action transition-colors rounded-full p-0.5 cursor-help focus:outline-none focus-visible:ring-1 focus-visible:ring-azul-action align-middle",
              className
            )}
          >
            <HelpCircle className="h-3.5 w-3.5 shrink-0" />
          </button>
        </TooltipTrigger>
      )}
      {tooltipBody}
    </Tooltip>
  );
}
