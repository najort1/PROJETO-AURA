"use client";

import * as React from "react";
import Link from "next/link";
import { CheckCircle2, ExternalLink, Copy, Check, CheckCircle, XCircle, Loader2, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { OperatorContext } from "@/components/layout/operator-context";
import { toast } from "sonner";
import type { DecisionItem } from "@/types/concierge";

interface DecisionsListProps {
  messageId: string;
  decisions: DecisionItem[];
  onDecisionUpdate?: (messageId: string, decisionIndex: number, newStatus: DecisionItem["status"]) => void;
}

export function DecisionsList({ messageId, decisions, onDecisionUpdate }: DecisionsListProps) {
  const [submittingIdx, setSubmittingIdx] = React.useState<number | null>(null);
  const [copiedHashIdx, setCopiedHashIdx] = React.useState<number | null>(null);

  // Consumo nominal do operador ativo via OperatorContext (Contrato 2 da spec)
  const operatorContext = React.useContext(OperatorContext);
  const currentProfile = operatorContext?.currentProfile || {
    name: "Carolina Silva",
    role: "Analista de Retenção CRM (HITL)",
  };

  if (!decisions || decisions.length === 0) return null;

  const handleDecisionAction = async (
    idx: number,
    dec: DecisionItem,
    targetStatus: "approved" | "rejected"
  ) => {
    setSubmittingIdx(idx);
    const previousStatus = dec.status;

    // Atualização otimista
    onDecisionUpdate?.(messageId, idx, targetStatus);

    try {
      const res = await fetch("/api/decisions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: dec.customer_id.trim().toUpperCase(),
          action_id: dec.action_id,
          action_name: dec.action_name,
          status: targetStatus,
          operator: `${currentProfile.name} (${currentProfile.role})`,
          original_message: dec.original_message || dec.final_message,
          final_message: dec.final_message,
          notes: `Homologação via Concierge Chat (${targetStatus === "approved" ? "Aprovado L2" : "Rejeitado"})`,
          edited: false,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Erro HTTP ${res.status} ao processar decisão`);
      }

      if (targetStatus === "approved") {
        toast.success("Decisão L2 homologada com sucesso no registro auditável.");
      } else {
        toast.success("Decisão rejeitada e registrada na trilha auditável.");
      }
    } catch (err: unknown) {
      // Reverte otimista
      onDecisionUpdate?.(messageId, idx, previousStatus);
      const msg = err instanceof Error ? err.message : "Falha ao gravar decisão";
      toast.error(msg);
    } finally {
      setSubmittingIdx(null);
    }
  };

  const handleCopyHash = async (hash: string, idx: number) => {
    try {
      await navigator.clipboard.writeText(hash);
      setCopiedHashIdx(idx);
      toast.success("Hash SHA-256 copiado para auditoria!");
      setTimeout(() => setCopiedHashIdx(null), 2000);
    } catch {
      toast.error("Não foi possível copiar o hash.");
    }
  };

  return (
    <div className="space-y-2 pt-1">
      <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1">
        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" />
        Trilha de Decisões Auditadas (LGPD):
      </span>
      <div className="grid grid-cols-1 gap-2">
        {decisions.map((dec, idx) => {
          const isApproved = dec.status === "approved";
          const isReview = dec.status === "in_review";
          const isRejected = dec.status === "rejected";
          const isBusy = submittingIdx === idx;
          const isHashCopied = copiedHashIdx === idx;
          const approvedLabel = dec.homologated ? "L2 • Aprovado" : "L1 • Aprovado";

          return (
            <div
              key={`dec-${messageId}-${dec.action_id || idx}`}
              className={`p-3 rounded-lg border text-xs space-y-2 transition-colors ${
                isApproved
                  ? "bg-emerald-50/60 border-emerald-300"
                  : isReview
                  ? "bg-amber-50/60 border-amber-300"
                  : isRejected
                  ? "bg-red-50/60 border-red-200"
                  : "bg-muted/40 border-border-subtle"
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-azul-navy">
                    {dec.customer_id}
                  </span>
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {dec.action_id}
                  </Badge>
                </div>

                <Badge
                  variant={isApproved ? "success" : isReview ? "warning" : isRejected ? "destructive" : "secondary"}
                  className="text-[10px] uppercase font-mono font-bold"
                >
                  {isApproved
                    ? approvedLabel
                    : isReview
                    ? "L2 • Em Revisão (HITL)"
                    : isRejected
                    ? "Rejeitado"
                    : dec.status}
                </Badge>
              </div>

              <p className="text-[11px] text-text-primary italic border-l-2 border-azul-action pl-2 leading-relaxed">
                &quot;{dec.final_message}&quot;
              </p>

              {/* Botões de Ação HITL quando em revisão */}
              {isReview && (
                <div className="flex items-center gap-2 pt-1 border-t border-amber-200/60">
                  <Button
                    type="button"
                    size="sm"
                    disabled={isBusy}
                    onClick={() => handleDecisionAction(idx, dec, "approved")}
                    className="h-7 text-xs bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-2.5 cursor-pointer"
                    aria-label={`Aprovar decisão ${dec.action_id} para cliente ${dec.customer_id}`}
                  >
                    {isBusy ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-1 motion-reduce:animate-none" aria-hidden="true" />
                    ) : (
                      <CheckCircle className="h-3 w-3 mr-1" aria-hidden="true" />
                    )}
                    Aprovar (L2)
                  </Button>

                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={isBusy}
                    onClick={() => handleDecisionAction(idx, dec, "rejected")}
                    className="h-7 text-xs border-red-300 text-red-700 hover:bg-red-50 font-medium px-2.5 cursor-pointer"
                    aria-label={`Rejeitar decisão ${dec.action_id} para cliente ${dec.customer_id}`}
                  >
                    <XCircle className="h-3 w-3 mr-1" aria-hidden="true" />
                    Rejeitar
                  </Button>
                </div>
              )}

              <div className="flex flex-wrap items-center justify-between gap-1 pt-1 border-t border-border-subtle/50 text-[10px] text-text-secondary font-mono">
                <div className="flex items-center gap-1.5">
                  <TooltipProvider delayDuration={150}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="cursor-help flex items-center gap-1 hover:text-azul-navy underline decoration-dotted">
                          <Info className="size-3 text-azul-action shrink-0" aria-hidden="true" />
                          <span>
                            SHA-256: {dec.hash_signature ? `${dec.hash_signature.substring(0, 16)}...` : "n/a"}
                          </span>
                        </span>
                      </TooltipTrigger>
                      <TooltipContent
                        side="top"
                        className="max-w-xs p-2.5 text-xs bg-surface border border-border-subtle shadow-xl space-y-1.5 text-text-primary"
                      >
                        <p className="font-bold text-azul-navy">
                          Assinatura Criptográfica Imutável
                        </p>
                        <p className="text-[11px] text-text-secondary leading-relaxed">
                          Garante a integridade da auditoria contra alterações retroativas na trilha de decisões (Art. 20 LGPD).
                        </p>
                        {dec.hash_signature && (
                          <div className="pt-1 border-t border-border-subtle">
                            <span className="text-[10px] text-text-muted block font-sans">Hash Completo:</span>
                            <code className="text-[10px] font-mono break-all text-azul-navy block bg-muted/60 p-1 rounded mt-0.5 select-all">
                              {dec.hash_signature}
                            </code>
                          </div>
                        )}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>

                  {dec.hash_signature && (
                    <button
                      type="button"
                      onClick={() => handleCopyHash(dec.hash_signature, idx)}
                      aria-label="Copiar Hash SHA-256 completo da decisão"
                      className="hover:text-azul-navy focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-azul-action rounded p-0.5 cursor-pointer"
                    >
                      {isHashCopied ? (
                        <Check className="h-3 w-3 text-emerald-600" aria-hidden="true" />
                      ) : (
                        <Copy className="h-3 w-3" aria-hidden="true" />
                      )}
                    </button>
                  )}
                </div>
                <Link
                  href={`/agente?customer_id=${encodeURIComponent(dec.customer_id)}`}
                  className="text-azul-action hover:underline font-sans font-semibold flex items-center gap-0.5"
                >
                  Ver no Kanban
                  <ExternalLink className="h-2.5 w-2.5" aria-hidden="true" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
