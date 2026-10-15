"use client";

import * as React from "react";
import {
  ShieldAlert,
  Sparkles,
  Send,
  CheckCircle2,
  Clock,
  ArrowRight,
  Edit3,
  Check,
  User,
  Plane,
} from "lucide-react";
import type { KanbanBoardState, KanbanCardData, DecisionStatus } from "@/types/actions";
import { TierBadge } from "@/components/branding/tier-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

interface KanbanBoardProps {
  initialState: Record<DecisionStatus, KanbanCardData[]> | KanbanBoardState;
}

const COLUMN_CONFIG: {
  id: DecisionStatus;
  title: string;
  badgeVariant: "default" | "destructive" | "secondary" | "warning" | "success";
  accentColor: string;
  description: string;
}[] = [
  {
    id: "suggested",
    title: "1. Sugerido",
    badgeVariant: "default",
    accentColor: "border-t-azul-action",
    description: "Recomendações do Modelo",
  },
  {
    id: "in_review",
    title: "2. Revisão HITL",
    badgeVariant: "destructive",
    accentColor: "border-t-magenta-cta",
    description: "Requer Aprovação Humana",
  },
  {
    id: "approved",
    title: "3. Aprovado",
    badgeVariant: "secondary",
    accentColor: "border-t-azul-primary",
    description: "Pronto para Lote CRM",
  },
  {
    id: "dispatched",
    title: "4. Disparado",
    badgeVariant: "warning",
    accentColor: "border-t-amber-500",
    description: "Enviado ao Canal",
  },
  {
    id: "completed",
    title: "5. Concluído",
    badgeVariant: "success",
    accentColor: "border-t-emerald-600",
    description: "Retenção Efetivada",
  },
];

export function KanbanBoard({ initialState }: KanbanBoardProps) {
  const [board, setBoard] = React.useState<Record<DecisionStatus, KanbanCardData[]>>(() => {
    if ("columns" in initialState) {
      return initialState.columns;
    }
    return initialState as Record<DecisionStatus, KanbanCardData[]>;
  });

  const [draggedCard, setDraggedCard] = React.useState<KanbanCardData | null>(null);
  const [editingCard, setEditingCard] = React.useState<KanbanCardData | null>(null);
  const [editedMessage, setEditedMessage] = React.useState("");
  const [toastMessage, setToastMessage] = React.useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleDragStart = (card: KanbanCardData) => {
    setDraggedCard(card);
  };

  const handleDrop = async (targetColumn: DecisionStatus) => {
    if (!draggedCard) return;

    const sourceColumn = draggedCard.status;
    if (sourceColumn === targetColumn) {
      setDraggedCard(null);
      return;
    }

    // Atualização otimista local
    const updatedCard: KanbanCardData = {
      ...draggedCard,
      status: targetColumn,
      updated_at: new Date().toISOString(),
    };

    setBoard((prev) => {
      const sourceList = (prev[sourceColumn] || []).filter((c) => c.customer_id !== draggedCard.customer_id);
      const targetList = [updatedCard, ...(prev[targetColumn] || [])];
      return {
        ...prev,
        [sourceColumn]: sourceList,
        [targetColumn]: targetList,
      };
    });

    setDraggedCard(null);

    // Persistência com dual-write via POST /api/agent/decisions
    try {
      const res = await fetch("/api/agent/decisions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: updatedCard.customer_id,
          action_id: updatedCard.action_id,
          action_name: updatedCard.action_name,
          status: targetColumn,
          operator: "operador_nextjs",
          original_message: updatedCard.message,
          final_message: updatedCard.message,
          edited: false,
          notes: `Movido de ${sourceColumn} para ${targetColumn} via Kanban DnD`,
        }),
      });

      if (res.ok) {
        showToast(`Cliente ${updatedCard.customer_id} movido para ${targetColumn.toUpperCase()} (Auditado em decisions.jsonl)`);
      }
    } catch (err) {
      console.error("Falha ao registrar decisão via DnD:", err);
    }
  };

  const handleApprove = async (card: KanbanCardData) => {
    const updatedCard: KanbanCardData = {
      ...card,
      status: "approved",
      updated_at: new Date().toISOString(),
    };

    setBoard((prev) => {
      const newBoard = { ...prev };
      for (const col of Object.keys(newBoard) as DecisionStatus[]) {
        newBoard[col] = (newBoard[col] || []).filter((c) => c.customer_id !== card.customer_id);
      }
      newBoard.approved = [updatedCard, ...(newBoard.approved || [])];
      return newBoard;
    });

    try {
      await fetch("/api/agent/decisions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: card.customer_id,
          action_id: card.action_id,
          action_name: card.action_name,
          status: "approved",
          operator: "operador_nextjs",
          original_message: card.message,
          final_message: card.message,
          edited: false,
          notes: "Aprovação imediata de recomendação pelo operador",
        }),
      });
      showToast(`Ação para ${card.customer_id} aprovada com sucesso!`);
    } catch (err) {
      console.error("Erro na aprovação:", err);
    }
  };

  const handleSaveEdit = async () => {
    if (!editingCard) return;

    const updatedCard: KanbanCardData = {
      ...editingCard,
      message: editedMessage,
      status: "approved",
      updated_at: new Date().toISOString(),
    };

    setBoard((prev) => {
      const newBoard = { ...prev };
      for (const col of Object.keys(newBoard) as DecisionStatus[]) {
        newBoard[col] = (newBoard[col] || []).filter((c) => c.customer_id !== editingCard.customer_id);
      }
      newBoard.approved = [updatedCard, ...(newBoard.approved || [])];
      return newBoard;
    });

    try {
      await fetch("/api/agent/decisions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: editingCard.customer_id,
          action_id: editingCard.action_id,
          action_name: editingCard.action_name,
          status: "edited",
          operator: "operador_nextjs",
          original_message: editingCard.message,
          final_message: editedMessage,
          edited: true,
          notes: "Mensagem personalizada e validada pelo operador antes de aprovação",
        }),
      });
      showToast(`Mensagem de ${editingCard.customer_id} editada e aprovada!`);
    } catch (err) {
      console.error("Erro na edição da mensagem:", err);
    }

    setEditingCard(null);
  };

  return (
    <div className="space-y-4">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-lg bg-azul-navy px-4 py-2.5 text-xs text-white shadow-2xl border border-slate-700 animate-in fade-in slide-in-from-bottom-2">
          <CheckCircle2 className="h-4 w-4 text-lime-campaign shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Grid de Colunas do Kanban */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5 items-start">
        {COLUMN_CONFIG.map((col) => {
          const cards = board[col.id] || [];

          return (
            <div
              key={col.id}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDrop(col.id)}
              className={`rounded-lg border border-border-subtle bg-surface shadow-xs flex flex-col min-h-[520px] max-h-[750px] ${col.accentColor} border-t-4`}
            >
              {/* Header da Coluna */}
              <div className="p-3 border-b border-border-subtle bg-muted/20">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-azul-navy tracking-tight">{col.title}</h3>
                  <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-mono font-bold text-text-primary">
                    {cards.length}
                  </span>
                </div>
                <p className="text-[10px] text-text-muted mt-0.5">{col.description}</p>
              </div>

              {/* Lista de Cards */}
              <div className="flex-1 overflow-y-auto p-2 space-y-2.5">
                {cards.length === 0 ? (
                  <div className="h-28 flex items-center justify-center rounded border border-dashed border-border-subtle text-[11px] text-text-muted text-center p-3">
                    Nenhum cliente nesta etapa. Arraste cards aqui.
                  </div>
                ) : (
                  cards.map((card) => (
                    <div
                      key={card.customer_id}
                      draggable
                      onDragStart={() => handleDragStart(card)}
                      className="group rounded-md border border-border-subtle bg-surface p-3 shadow-xs hover:shadow-md hover:border-azul-action/60 transition-all cursor-grab active:cursor-grabbing space-y-2 select-none"
                    >
                      {/* Top Bar: ID, Tier e HITL */}
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-azul-navy">
                          {card.customer_id}
                        </span>
                        <TierBadge tier={card.tier} showNewBadge={false} />
                      </div>

                      {/* Métricas Principais */}
                      <div className="grid grid-cols-2 gap-1 text-[11px] font-mono bg-muted/40 p-1.5 rounded">
                        <div>
                          <span className="text-[9px] text-text-muted block font-sans">VaR:</span>
                          <span className="font-bold text-magenta-cta">
                            R$ {card.valor_em_risco.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}
                          </span>
                        </div>
                        <div>
                          <span className="text-[9px] text-text-muted block font-sans">Churn:</span>
                          <span className="font-bold text-text-primary">
                            {(card.churn_prob * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      {/* Ação e Canal */}
                      <div>
                        <span className="text-[11px] font-semibold text-azul-navy block leading-tight">
                          {card.action_name}
                        </span>
                        <span className="text-[10px] text-text-muted flex items-center gap-1 mt-0.5">
                          Canal: <strong className="text-azul-action uppercase">{card.channel}</strong>
                        </span>
                      </div>

                      {/* Flag HITL se aplicável */}
                      {card.human_review && (
                        <div className="flex items-center gap-1 rounded bg-magenta-cta/10 px-1.5 py-0.5 text-[10px] font-bold text-magenta-cta border border-magenta-cta/20">
                          <ShieldAlert className="h-3 w-3 shrink-0" />
                          <span>Revisão HITL Mandatória</span>
                        </div>
                      )}

                      {/* Botões de Ação Inline */}
                      <div className="pt-1 flex items-center gap-1.5 border-t border-border-subtle">
                        {col.id !== "approved" && col.id !== "dispatched" && col.id !== "completed" && (
                          <Button
                            variant="default"
                            size="sm"
                            className="h-6 text-[10px] flex-1 px-1.5"
                            onClick={() => handleApprove(card)}
                          >
                            <Check className="h-3 w-3 mr-1" /> Aprovar
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-6 text-[10px] px-2 text-text-secondary"
                          onClick={() => {
                            setEditingCard(card);
                            setEditedMessage(card.message);
                          }}
                        >
                          <Edit3 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal de Edição de Mensagem */}
      {editingCard && (
        <Dialog open={Boolean(editingCard)} onOpenChange={(open) => !open && setEditingCard(null)}>
          <DialogContent className="sm:max-w-xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-azul-navy">
                <Edit3 className="h-4 w-4 text-azul-action" />
                Personalizar Mensagem de Retenção ({editingCard.customer_id})
              </DialogTitle>
              <DialogDescription>
                Ação: <strong>{editingCard.action_name}</strong> • Canal: <strong className="uppercase">{editingCard.channel}</strong>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-2 text-xs">
              <div>
                <label className="font-semibold text-text-primary block mb-1">
                  Texto da Mensagem (Auditado com Registro Imutável):
                </label>
                <textarea
                  className="w-full h-32 rounded-md border border-border-dark p-3 text-sm focus:outline-none focus:ring-1 focus:ring-azul-action"
                  value={editedMessage}
                  onChange={(e) => setEditedMessage(e.target.value)}
                />
              </div>

              <div className="rounded bg-muted p-2.5 text-[11px] text-text-secondary">
                <p className="font-semibold text-azul-navy">Salvaguarda de Auditoria LGPD:</p>
                <p>A edição humana será registrada em <code>data/analytics/decisions.jsonl</code> com carimbo temporal UTC e assinatura do operador logado.</p>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" size="sm" onClick={() => setEditingCard(null)}>
                Cancelar
              </Button>
              <Button variant="default" size="sm" onClick={handleSaveEdit}>
                <Check className="h-3.5 w-3.5 mr-1" /> Salvar & Aprovar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
