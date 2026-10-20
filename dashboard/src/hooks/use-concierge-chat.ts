"use client";

import * as React from "react";
import { toast } from "sonner";
import type {
  ChatMessage,
  ChatStatus,
  ConciergeTelemetry,
  DecisionItem,
} from "@/types/concierge";

const STORAGE_KEY = "aura_concierge_history_v2";

const INITIAL_WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Olá! Sou o **Aura Concierge**, o agente autônomo inteligente do CRM Azul Fidelidade. Conectado ao modelo de raciocínio `principal-combo` com **8 ferramentas corporativas nativas** e matriz de governança L1/L2.\n\nVocê pode me pedir diagnósticos de clientes, investigação de voos com atrito, fundamentação em artigos do regulamento (RAG), concessão de cortesias ou varreduras completas da carteira sem precisar usar o terminal CLI.\n\n**Selecione um cliente sugerido ou digite sua solicitação abaixo:**",
  timestamp: "10:00",
};

export function useConciergeChat(initialCustomerId = "C000030") {
  const [messages, setMessages] = React.useState<ChatMessage[]>([INITIAL_WELCOME_MESSAGE]);
  const [input, setInput] = React.useState("");
  const [status, setStatus] = React.useState<ChatStatus>("idle");
  const [selectedCustomerId, setSelectedCustomerId] = React.useState(initialCustomerId);
  const [telemetry, setTelemetry] = React.useState<ConciergeTelemetry | null>(null);
  const [isLoadingTelemetry, setIsLoadingTelemetry] = React.useState(false);
  const [lastFailedPrompt, setLastFailedPrompt] = React.useState<string>("");
  const [isHydrated, setIsHydrated] = React.useState(false);

  const abortControllerRef = React.useRef<AbortController | null>(null);

  // Refs sincronizados diretamente no render (elimina qualquer janela de staleness pós-commit)
  const inputRef = React.useRef(input);
  inputRef.current = input;

  const messagesRef = React.useRef(messages);
  messagesRef.current = messages;

  const selectedCustomerIdRef = React.useRef(selectedCustomerId);
  selectedCustomerIdRef.current = selectedCustomerId;

  const lastSerializedStorageRef = React.useRef<string>("");

  const isLoading = status === "sending";

  // Carregamento de telemetria
  const fetchTelemetry = React.useCallback(async () => {
    setIsLoadingTelemetry(true);
    try {
      const res = await fetch("/api/concierge/chat", { method: "GET" });
      if (res.ok) {
        const data = await res.json();
        setTelemetry({
          status: data.status === "online" ? "online" : "offline",
          model: data.model || "principal-combo",
          base_url: data.base_url || "http://localhost:20128/v1",
          tools_available: data.tools_available || [
            "consultar_cliente_360",
            "consultar_historico_atritos_voos",
            "consultar_regras_regulamento",
            "conceder_milhas_cortesia",
            "emitir_voucher_servico",
            "propor_acao_retencao_kanban",
            "escalar_atendimento_vip",
            "listar_clientes_em_risco_ou_atrito",
          ],
        });
      } else {
        setTelemetry({
          status: "offline",
          model: "principal-combo",
          base_url: "http://localhost:20128/v1",
          tools_available: [],
        });
      }
    } catch {
      setTelemetry({
        status: "offline",
        model: "principal-combo",
        base_url: "http://localhost:20128/v1",
        tools_available: [],
      });
    } finally {
      setIsLoadingTelemetry(false);
    }
  }, []);

  // Hidratação segura do localStorage com validação de registros (Anti-Hydration mismatch)
  React.useEffect(() => {
    setIsHydrated(true);
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const validMessages = parsed.filter(
            (m: unknown): m is ChatMessage =>
              typeof m === "object" &&
              m !== null &&
              typeof (m as ChatMessage).id === "string" &&
              typeof (m as ChatMessage).content === "string" &&
              typeof (m as ChatMessage).role === "string"
          );
          if (validMessages.length > 0) {
            // Desativa animação de streaming para mensagens recuperadas do storage
            const cleaned = validMessages.map((m) => ({ ...m, isStreaming: false }));
            setMessages(cleaned);
          }
        }
      }
    } catch (e) {
      console.warn("Erro ao carregar histórico do localStorage:", e);
    }
    fetchTelemetry();
  }, [fetchTelemetry]);

  // Persistência segura no localStorage (Capped at 30 items, pula no-ops para evitar double-write)
  React.useEffect(() => {
    if (!isHydrated) return;
    try {
      const capped = messages.slice(-30).map((m) => ({ ...m, isStreaming: false }));
      const serialized = JSON.stringify(capped);
      if (serialized !== lastSerializedStorageRef.current) {
        lastSerializedStorageRef.current = serialized;
        localStorage.setItem(STORAGE_KEY, serialized);
      }
    } catch (e) {
      console.warn("Erro ao salvar histórico no localStorage:", e);
    }
  }, [messages, isHydrated]);

  // AbortController
  const abortChat = React.useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("aborted");
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "system",
        content:
          "⚠️ Geração interrompida localmente na interface. Nota: O motor Python ainda pode processar a requisição em background antes de liberar a próxima execução.",
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    toast.info("A requisição foi cancelada na interface do usuário.");
  }, []);

  // Envio de mensagens desacoplado do estado 'input' e 'messages' via refs
  const sendMessage = React.useCallback(
    async (overrideText?: string, actionType: "chat" | "evaluate" = "chat") => {
      const textToSend = (overrideText ?? inputRef.current).trim();
      if (!textToSend || status === "sending") return;

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: textToSend,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, userMessage]);
      if (!overrideText) {
        setInput("");
      }
      setLastFailedPrompt("");
      setStatus("sending");

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const filteredHistory = messagesRef.current
          .filter(
            (m) =>
              (m.role === "user" || m.role === "assistant") &&
              !m.isError &&
              m.id !== "welcome" &&
              m.id !== "welcome_reset"
          )
          .map((m) => ({ role: m.role, content: m.content }));

        // Janela deslizante: mantém os últimos 8 turnos anteriores de histórico [B3]
        const boundedHistory = filteredHistory.slice(-8);

        const payload = {
          action: actionType,
          message: textToSend,
          customer_id: selectedCustomerIdRef.current || null,
          history: boundedHistory,
        };

        const res = await fetch("/api/concierge/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok || data.success === false || data.finish_reason === "error") {
          const errorMessage =
            data.reply ||
            data.error ||
            `Erro ${res.status}: O motor autônomo falhou ao processar a resposta.`;

          setStatus("error");
          setLastFailedPrompt(textToSend);

          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: errorMessage,
              timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
              isError: true,
              finish_reason: "error",
            },
          ]);
          toast.error("O Aura Concierge retornou um erro na execução.");
          return;
        }

        const toolsExecutedList = Array.isArray(data.tools_executed)
          ? data.tools_executed
          : Array.isArray(data.tool_calls_executed)
          ? data.tool_calls_executed
          : [];

        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.reply || data.final_message || "Resposta do agente autônomo recebida com sucesso.",
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          thought_process: Array.isArray(data.thought_process) ? data.thought_process : [],
          tools_executed: toolsExecutedList,
          decisions_taken: Array.isArray(data.decisions_taken) ? data.decisions_taken : [],
          turns: typeof data.turns === "number" ? data.turns : 1,
          human_review_required: Boolean(data.human_review_required),
          finish_reason: data.finish_reason || "stop",
          isStreaming: true,
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setStatus("idle");
      } catch (err: unknown) {
        if (controller.signal.aborted) {
          // Já tratado em abortChat
          return;
        }

        const msg = err instanceof Error ? err.message : "Falha na conexão com o servidor.";
        setStatus("error");
        setLastFailedPrompt(textToSend);

        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: `Desculpe, ocorreu uma instabilidade ao conectar com o motor autônomo do Concierge (${msg}). Verifique se o serviço local do modelo está ativo.`,
            timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
            isError: true,
            finish_reason: "error",
          },
        ]);
        toast.error("Falha de rede ou timeout ao conectar com o backend.");
      } finally {
        abortControllerRef.current = null;
      }
    },
    [status]
  );

  // Retentativa do último prompt falho: remove a bolha de erro e a bolha de usuário que falhou para não duplicar turnos
  const retryLastFailed = React.useCallback(() => {
    const promptToRetry = lastFailedPrompt;
    if (!promptToRetry || status === "sending") return;

    let cleaned = [...messagesRef.current];
    if (cleaned.length > 0 && cleaned[cleaned.length - 1].isError) {
      cleaned.pop();
    }
    if (
      cleaned.length > 0 &&
      cleaned[cleaned.length - 1].role === "user" &&
      cleaned[cleaned.length - 1].content === promptToRetry
    ) {
      cleaned.pop();
    }
    messagesRef.current = cleaned;
    setMessages(cleaned);

    sendMessage(promptToRetry);
  }, [lastFailedPrompt, status, sendMessage]);

  // Limpeza de histórico
  const clearChat = React.useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("idle");
    setLastFailedPrompt("");
    const resetWelcome: ChatMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content:
        "Conversa reiniciada. O Aura Concierge está pronto para novas consultas e comandos com as 8 ferramentas do CRM Azul Fidelidade.",
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages([resetWelcome]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn("Erro ao limpar localStorage:", e);
    }
    toast.success("Histórico do chat reiniciado com sucesso.");
  }, []);

  // Atualização otimista de decisão (HITL): define homologated: true para decisões aprovadas/rejeitadas pelo operador
  const updateDecision = React.useCallback(
    (messageId: string, decisionIndex: number, newStatus: DecisionItem["status"]) => {
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id !== messageId || !msg.decisions_taken) return msg;
          const updatedDecisions = [...msg.decisions_taken];
          if (updatedDecisions[decisionIndex]) {
            updatedDecisions[decisionIndex] = {
              ...updatedDecisions[decisionIndex],
              status: newStatus,
              homologated: true,
            };
          }
          return {
            ...msg,
            decisions_taken: updatedDecisions,
          };
        })
      );
    },
    []
  );

  return {
    messages,
    input,
    setInput,
    status,
    isLoading,
    selectedCustomerId,
    setSelectedCustomerId,
    telemetry,
    isLoadingTelemetry,
    lastFailedPrompt,
    sendMessage,
    abortChat,
    retryLastFailed,
    clearChat,
    updateDecision,
  };
}
