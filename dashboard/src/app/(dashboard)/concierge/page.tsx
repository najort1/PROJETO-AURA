"use client";

import * as React from "react";
import { Toaster } from "sonner";
import { ConciergeHeader } from "@/components/concierge/concierge-header";
import { CustomerContextBar } from "@/components/concierge/customer-context-bar";
import { ChatMessageList } from "@/components/concierge/chat-message-list";
import { ChatInputBar } from "@/components/concierge/chat-input-bar";
import { useConciergeChat } from "@/hooks/use-concierge-chat";

export default function ConciergeChatPage() {
  const {
    messages,
    input,
    setInput,
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
  } = useConciergeChat();

  const isOnline = telemetry?.status === "online";

  const handleQuickAction = React.useCallback(
    (prompt: string, actionType: "chat" | "evaluate" = "chat") => {
      sendMessage(prompt, actionType);
    },
    [sendMessage]
  );

  const handleSend = React.useCallback(
    (text?: string) => {
      sendMessage(text);
    },
    [sendMessage]
  );

  return (
    <div className="h-[calc(100dvh-126px)] sm:h-[calc(100dvh-142px)] lg:h-[calc(100dvh-158px)] flex flex-col overflow-hidden">
      <Toaster richColors position="top-right" closeButton />

      {/* Topo fixo: Header de telemetria e seletor de cliente ativo */}
      <div className="shrink-0 space-y-2 pb-2">
        <ConciergeHeader
          telemetry={telemetry}
          isLoadingTelemetry={isLoadingTelemetry}
          isOnline={isOnline}
          onClearChat={clearChat}
        />
        <CustomerContextBar
          selectedCustomerId={selectedCustomerId}
          onSelectCustomer={setSelectedCustomerId}
          onQuickAction={handleQuickAction}
          isLoading={isLoading}
          isOnline={isOnline}
        />
      </div>

      {/* Container Principal de Chat com Mensagens Roláveis e Input Pinned */}
      <div className="flex-1 flex flex-col min-h-0 bg-surface border border-border-subtle rounded-xl shadow-xs overflow-hidden">
        <ChatMessageList
          messages={messages}
          isLoading={isLoading}
          onAbort={abortChat}
          onDecisionUpdate={updateDecision}
          onRetryMessage={retryLastFailed}
        />

        <div className="shrink-0 border-t border-border-subtle bg-surface p-2.5 sm:p-3">
          <ChatInputBar
            value={input}
            onChange={setInput}
            onSend={handleSend}
            isLoading={isLoading}
            isOnline={isOnline}
            onAbort={abortChat}
            lastFailedPrompt={lastFailedPrompt}
            onRetry={retryLastFailed}
          />
        </div>
      </div>
    </div>
  );
}
