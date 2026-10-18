"use client";

import * as React from "react";
import { ChevronDown, ChevronRight, Zap } from "lucide-react";

interface ThoughtAccordionProps {
  id: string;
  thoughtProcess: string[];
}

export function ThoughtAccordion({ id, thoughtProcess }: ThoughtAccordionProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const contentId = `thought-content-${id}`;

  if (!thoughtProcess || thoughtProcess.length === 0) return null;

  return (
    <div className="mt-2.5 border-t border-border-subtle pt-2">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-controls={contentId}
        className="flex items-center gap-1.5 text-[11px] font-medium text-azul-action hover:text-azul-deep transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-azul-action rounded cursor-pointer"
      >
        <Zap className="size-3 text-azul-action" aria-hidden="true" />
        <span>Raciocínio do Modelo ({thoughtProcess.length} {thoughtProcess.length === 1 ? "passo" : "passos"})</span>
        {isOpen ? (
          <ChevronDown className="size-3" aria-hidden="true" />
        ) : (
          <ChevronRight className="size-3" aria-hidden="true" />
        )}
      </button>

      <div
        id={contentId}
        hidden={!isOpen}
        className={`mt-2 space-y-1.5 rounded-md bg-muted/40 p-2.5 text-[11px] font-mono text-text-secondary border border-border-subtle ${
          !isOpen ? "hidden" : ""
        }`}
      >
        {thoughtProcess.map((step, idx) => (
          <div key={`thought-${id}-${idx}`} className="flex gap-2">
            <span className="text-azul-action font-semibold shrink-0">#{idx + 1}</span>
            <span className="whitespace-pre-wrap leading-relaxed break-words">{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
