"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

export interface KeySequenceRouteMap {
  [secondKey: string]: string;
}

export const DEFAULT_G_SHORTCUTS: KeySequenceRouteMap = {
  b: "/clientes",
  c: "/carteira",
  p: "/personas",
  "3": "/cliente-360",
  a: "/concierge",
  k: "/agente",
  s: "/atritos",
  f: "/simulador",
  i: "/ia-responsavel",
};

interface UseKeySequenceOptions {
  shortcuts?: KeySequenceRouteMap;
  leaderKey?: string;
  timeoutMs?: number;
  enabled?: boolean;
}

function isEditableElement(element: Element | null): boolean {
  if (!element) return false;
  const tagName = element.tagName.toLowerCase();
  if (tagName === "input" || tagName === "textarea" || tagName === "select") {
    return true;
  }
  if (element.hasAttribute("contenteditable") && element.getAttribute("contenteditable") !== "false") {
    return true;
  }
  return false;
}

export function useKeySequence(options: UseKeySequenceOptions = {}) {
  const {
    shortcuts = DEFAULT_G_SHORTCUTS,
    leaderKey = "g",
    timeoutMs = 800,
    enabled = true,
  } = options;

  const router = useRouter();
  const leaderPressedRef = React.useRef(false);
  const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearLeader = React.useCallback(() => {
    leaderPressedRef.current = false;
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  React.useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignorar combinações com modificadores de sistema (Ctrl, Meta, Alt)
      if (event.ctrlKey || event.metaKey || event.altKey) {
        clearLeader();
        return;
      }

      // Ignorar se o foco estiver em campo de entrada de texto
      const activeElement = document.activeElement;
      if (isEditableElement(activeElement)) {
        clearLeader();
        return;
      }

      const key = event.key.toLowerCase();

      // Primeiro passo: tecla líder 'g'
      if (!leaderPressedRef.current) {
        if (key === leaderKey.toLowerCase()) {
          leaderPressedRef.current = true;
          timeoutRef.current = setTimeout(() => {
            leaderPressedRef.current = false;
            timeoutRef.current = null;
          }, timeoutMs);
        }
        return;
      }

      // Segundo passo: tecla de atalho dentro da janela de tempo
      const destination = shortcuts[key];
      if (destination) {
        event.preventDefault();
        clearLeader();
        router.push(destination);
      } else {
        // Tecla diferente: limpa o líder
        clearLeader();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [enabled, shortcuts, leaderKey, timeoutMs, router, clearLeader]);
}
