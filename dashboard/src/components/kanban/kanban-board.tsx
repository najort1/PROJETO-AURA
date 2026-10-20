"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import {
  ShieldAlert,
  Sparkles,
  ArrowRight,
  Edit3,
  Check,
  XCircle,
  AlertTriangle,
  Maximize2,
  Minimize2,
  Layers,
} from "lucide-react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import type { KanbanBoardState, KanbanCardData, DecisionStatus } from "@/types/actions";
import { TierBadge } from "@/components/branding/tier-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { formatIntegerBRL } from "@/lib/format";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { OperatorContext } from "@/components/layout/operator-context";
import { toast } from "sonner";

interface KanbanBoardProps {
  initialState: Record<DecisionStatus, KanbanCardData[]> | KanbanBoardState;
  initialCustomerId?: string;
  initialFilter?: string;
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
    accentColor: "border-t-[#B81D7D]",
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
  {
    id: "rejected",
    title: "6. Rejeitados",
    badgeVariant: "destructive",
    accentColor: "border-t-red-600",
    description: "Descartadas / Não Aplicáveis",
  },
];

interface KanbanCardProps {
  card: KanbanCardData;
  currentColumnId: DecisionStatus;
  viewport: "desktop" | "mobile";
  isTargetHighlighted: boolean;
  onDragStart: (card: KanbanCardData) => void;
  onApprove: (card: KanbanCardData) => void;
  onOpenReject: (card: KanbanCardData) => void;
  onOpenEdit: (card: KanbanCardData) => void;
  onMoveCard: (card: KanbanCardData, targetColumn: DecisionStatus) => void;
}

/**
 * Card individual do Kanban memoizado com React.memo (C1-3).
 * Evita re-render de 150+ cards quando apenas um card se move ou o estado superior muda.
 */
const KanbanCard = React.memo(function KanbanCard({
  card,
  currentColumnId,
  viewport,
  isTargetHighlighted,
  onDragStart,
  onApprove,
  onOpenReject,
  onOpenEdit,
  onMoveCard,
}: KanbanCardProps) {
  return (
    <div
      id={`kanban-card-${viewport}-${card.customer_id}`}
      draggable
      onDragStart={() => onDragStart(card)}
      className={`group rounded-md border bg-surface p-3 shadow-xs hover:shadow-md transition-all select-none space-y-2 cursor-grab active:cursor-grabbing ${
        isTargetHighlighted
          ? "ring-2 ring-azul-action ring-offset-2 border-azul-action shadow-md bg-azul-primary/5"
          : "border-border-subtle hover:border-azul-action/60"
      }`}
    >
      {/* Top Bar: ID, Tier e HITL */}
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs font-bold text-azul-navy">
          {card.customer_id}
        </span>
        <TierBadge tier={card.tier} showNewBadge={false} />
      </div>

      {/* Métricas Principais com Intl compartilhado em módulo (C1-5 & C4) */}
      <div className="grid grid-cols-2 gap-1 text-[11px] font-mono bg-muted/40 p-1.5 rounded">
        <div>
          <span className="text-[9px] text-text-muted block font-sans">VaR:</span>
          <span className="font-bold text-magenta-text">
            R$ {formatIntegerBRL(card.valor_em_risco)}
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
        <div className="flex items-center gap-1 rounded bg-[#B81D7D]/10 px-1.5 py-0.5 text-[10px] font-bold text-magenta-text border border-[#B81D7D]/20">
          <ShieldAlert className="h-3 w-3 shrink-0" />
          <span>Revisão HITL Mandatória</span>
        </div>
      )}

      {/* Mensagem sugerida truncada */}
      <p className="text-[11px] text-text-secondary line-clamp-2 italic border-l-2 border-azul-action pl-2 leading-relaxed">
        &quot;{card.message}&quot;
      </p>

      {/* Botões de Ação Inline + Menu Radix "Mover para..." (P0-6) */}
      <div className="pt-1.5 flex flex-wrap items-center gap-1 border-t border-border-subtle">
        {/* Botão Aprovar quando não estiver em approved/dispatched/completed/rejected */}
        {currentColumnId !== "approved" &&
          currentColumnId !== "dispatched" &&
          currentColumnId !== "completed" &&
          currentColumnId !== "rejected" && (
            <Button
              variant="default"
              size="sm"
              className="h-6 text-[10px] flex-1 px-1.5 bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
              onClick={() => onApprove(card)}
              aria-label={`Aprovar ação para cliente ${card.customer_id}`}
            >
              <Check className="h-3 w-3 mr-1" /> Aprovar
            </Button>
          )}

        {/* Botão Rejeitar quando não estiver em rejected/completed */}
        {currentColumnId !== "rejected" && currentColumnId !== "completed" && (
          <Button
            variant="outline"
            size="sm"
            className="h-6 text-[10px] px-1.5 border-red-200 text-red-700 hover:bg-red-50 cursor-pointer"
            onClick={() => onOpenReject(card)}
            aria-label={`Rejeitar ação para cliente ${card.customer_id}`}
          >
            <XCircle className="h-3 w-3 mr-0.5" /> Rejeitar
          </Button>
        )}

        {/* Botão Editar Mensagem */}
        <Button
          variant="outline"
          size="sm"
          className="h-6 text-[10px] px-1.5 text-text-secondary cursor-pointer"
          onClick={() => onOpenEdit(card)}
          aria-label={`Editar mensagem para cliente ${card.customer_id}`}
        >
          <Edit3 className="h-3 w-3" />
        </Button>

        {/* Menu Dropdown Radix "Mover para..." acessível por teclado e touch (P0-6) */}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="h-6 text-[10px] px-1.5 flex items-center gap-1 text-text-secondary hover:text-azul-navy cursor-pointer"
              aria-label={`Mover card do cliente ${card.customer_id} para outra etapa`}
            >
              <span>Mover</span>
              <ArrowRight className="size-2.5" aria-hidden="true" />
            </Button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="z-50 min-w-[190px] overflow-hidden rounded-md border border-border-subtle bg-surface p-1 text-xs text-text-primary shadow-xl animate-in fade-in-80"
              sideOffset={4}
            >
              <DropdownMenu.Label className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Mover para etapa:
              </DropdownMenu.Label>
              {COLUMN_CONFIG.map((targetCol) => {
                const isCurrent = targetCol.id === currentColumnId;
                return (
                  <DropdownMenu.Item
                    key={targetCol.id}
                    disabled={isCurrent}
                    onSelect={() => {
                      if (targetCol.id === "rejected") {
                        onOpenReject(card);
                      } else {
                        onMoveCard(card, targetCol.id);
                      }
                    }}
                    className="flex items-center justify-between rounded px-2 py-1.5 text-xs text-azul-navy hover:bg-azul-action/10 hover:text-azul-action focus:bg-azul-action/10 focus:text-azul-action focus:outline-none cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <span>{targetCol.title}</span>
                    {isCurrent && <Check className="size-3 text-emerald-600" aria-hidden="true" />}
                  </DropdownMenu.Item>
                );
              })}
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </div>
  );
});

interface EditMessageModalProps {
  card: KanbanCardData | null;
  operatorString: string;
  onClose: () => void;
  onSaveDraft: (card: KanbanCardData, message: string) => Promise<void>;
  onSaveAndApprove: (card: KanbanCardData, message: string) => Promise<void>;
}

/**
 * Modal de Edição isolado com estado de textarea local (C1-2).
 * Digitação não propaga re-renders para a esteira inteira.
 */
function EditMessageModal({
  card,
  operatorString,
  onClose,
  onSaveDraft,
  onSaveAndApprove,
}: EditMessageModalProps) {
  const [editedMessage, setEditedMessage] = React.useState(card?.message || "");
  const [editError, setEditError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (card) {
      setEditedMessage(card.message);
      setEditError(null);
    }
  }, [card]);

  if (!card) return null;

  const handleDraft = () => {
    const cleanMessage = editedMessage.trim();
    if (!cleanMessage) {
      setEditError("O texto da mensagem não pode estar em branco.");
      return;
    }
    onSaveDraft(card, cleanMessage);
  };

  const handleApprove = () => {
    const cleanMessage = editedMessage.trim();
    if (!cleanMessage) {
      setEditError("O texto da mensagem não pode estar em branco.");
      return;
    }
    onSaveAndApprove(card, cleanMessage);
  };

  return (
    <Dialog open={Boolean(card)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-azul-navy">
            <Edit3 className="h-4 w-4 text-azul-action" />
            Personalizar Mensagem de Retenção ({card.customer_id})
          </DialogTitle>
          <DialogDescription>
            Ação: <strong>{card.action_name}</strong> • Canal:{" "}
            <strong className="uppercase">{card.channel}</strong> • Etapa Atual:{" "}
            <strong className="uppercase">{card.status}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2 text-xs">
          <div>
            <label htmlFor="modal-edit-textarea" className="font-semibold text-text-primary block mb-1">
              Texto da Mensagem (Auditado com Registro Imutável):
            </label>
            <textarea
              id="modal-edit-textarea"
              rows={4}
              className={`w-full rounded-md border p-3 text-sm focus:outline-none focus:ring-1 focus:ring-azul-action leading-relaxed ${
                editError ? "border-red-500 bg-red-50/20" : "border-border-dark"
              }`}
              value={editedMessage}
              onChange={(e) => {
                setEditedMessage(e.target.value);
                if (editError) setEditError(null);
              }}
              placeholder="Redija a mensagem personalizada para o cliente..."
            />
            {editError && (
              <p className="text-[11px] font-semibold text-red-600 mt-1 flex items-center gap-1">
                <AlertTriangle className="size-3" aria-hidden="true" />
                {editError}
              </p>
            )}
          </div>

          <div className="rounded bg-muted p-2.5 text-[11px] text-text-secondary space-y-1">
            <p className="font-semibold text-azul-navy">Salvaguarda de Auditoria LGPD:</p>
            <p>
              A edição humana será registrada na trilha imutável <code>decisions.jsonl</code> com
              carimbo temporal UTC e assinatura nominal do operador logado (
              <strong>{operatorString}</strong>).
            </p>
          </div>
        </div>

        <DialogFooter className="flex flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="cursor-pointer"
          >
            Cancelar
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleDraft}
            className="cursor-pointer"
            aria-label="Salvar rascunho da mensagem mantendo a etapa atual"
          >
            Salvar Rascunho
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleApprove}
            className="bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
            aria-label="Salvar mensagem editada e aprovar imediatamente"
          >
            <Check className="h-3.5 w-3.5 mr-1" /> Salvar & Aprovar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface RejectJustificationModalProps {
  card: KanbanCardData | null;
  operatorString: string;
  onClose: () => void;
  onConfirmReject: (card: KanbanCardData, justification: string) => void;
}

/**
 * Diálogo de Rejeição Justificada isolado com estado de textarea local (C1-2).
 */
function RejectJustificationModal({
  card,
  operatorString,
  onClose,
  onConfirmReject,
}: RejectJustificationModalProps) {
  const [rejectJustification, setRejectJustification] = React.useState("");
  const [rejectError, setRejectError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (card) {
      setRejectJustification("");
      setRejectError(null);
    }
  }, [card]);

  if (!card) return null;

  const handleConfirm = () => {
    const cleanJust = rejectJustification.trim();
    if (!cleanJust) {
      setRejectError("A justificativa de rejeição é obrigatória para conformidade e auditoria LGPD.");
      return;
    }
    onConfirmReject(card, cleanJust);
  };

  return (
    <Dialog open={Boolean(card)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-700">
            <XCircle className="h-5 w-5 text-red-600" />
            Rejeitar Ação de Retenção ({card.customer_id})
          </DialogTitle>
          <DialogDescription>
            Ação: <strong>{card.action_name}</strong> • Canal:{" "}
            <strong className="uppercase">{card.channel}</strong>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2 text-xs">
          <div>
            <label htmlFor="reject-justification-textarea" className="font-semibold text-text-primary block mb-1">
              Justificativa de Rejeição (Obrigatória para Conformidade e LGPD):
            </label>
            <textarea
              id="reject-justification-textarea"
              rows={3}
              className={`w-full rounded-md border p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-red-500 leading-relaxed ${
                rejectError ? "border-red-500 bg-red-50/20" : "border-border-dark"
              }`}
              value={rejectJustification}
              onChange={(e) => {
                setRejectJustification(e.target.value);
                if (rejectError) setRejectError(null);
              }}
              placeholder="Ex: Cliente manifestou desinteresse em viagens no semestre; política de teto de cortesias já atingida."
            />
            {rejectError && (
              <p className="text-[11px] font-semibold text-red-600 mt-1 flex items-center gap-1">
                <AlertTriangle className="size-3" aria-hidden="true" />
                {rejectError}
              </p>
            )}
          </div>

          <div className="rounded bg-red-50/60 border border-red-200/80 p-2.5 text-[11px] text-red-950 space-y-1">
            <p className="font-semibold text-red-900">Registro de Descarte Regulatório:</p>
            <p>
              O descarte será gravado na trilha com status <code>rejected</code>, assinado por{" "}
              <strong>{operatorString}</strong>.
            </p>
          </div>
        </div>

        <DialogFooter className="flex flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="cursor-pointer"
          >
            Cancelar
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleConfirm}
            className="cursor-pointer bg-red-600 hover:bg-red-700 text-white"
            aria-label="Confirmar rejeição da recomendação"
          >
            <XCircle className="h-3.5 w-3.5 mr-1" /> Confirmar Rejeição
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function KanbanBoardInner({ initialState, initialCustomerId = "", initialFilter = "" }: KanbanBoardProps) {
  const searchParams = useSearchParams();

  // Consumo nominal do operador ativo via OperatorContext (Contrato 2 da spec)
  const operatorContext = React.useContext(OperatorContext);
  const currentProfile = operatorContext?.currentProfile || {
    name: "Carolina Silva",
    role: "Analista de Retenção CRM (HITL)",
  };
  const operatorString = `${currentProfile.name} (${currentProfile.role})`;

  // Estado do board organizado pelas 6 colunas canônicas (incluindo 'rejected')
  const [board, setBoard] = React.useState<Record<DecisionStatus, KanbanCardData[]>>(() => {
    const raw = "columns" in initialState ? initialState.columns : initialState;
    return {
      suggested: raw.suggested || [],
      in_review: raw.in_review || [],
      approved: raw.approved || [],
      edited: raw.edited || [],
      dispatched: raw.dispatched || [],
      completed: raw.completed || [],
      rejected: raw.rejected || [],
    };
  });

  // Refs de sincronização para garantir callbacks estáveis sem re-criar closures (C1-3)
  const boardRef = React.useRef(board);
  boardRef.current = board;

  const operatorStringRef = React.useRef(operatorString);
  operatorStringRef.current = operatorString;

  // Viewport detection SSR-safe (C1-1): renderiza ambos no SSR/hidratação inicial
  // evitando flash de layout com as classes CSS existentes; após montagem, preserva apenas a árvore ativa no DOM.
  const [isMounted, setIsMounted] = React.useState(false);
  const [isDesktop, setIsDesktop] = React.useState(true);

  React.useEffect(() => {
    setIsMounted(true);
    const mql = window.matchMedia("(min-width: 768px)");
    setIsDesktop(mql.matches);
    const handler = (e: MediaQueryListEvent) => setIsDesktop(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  // Filtros de query parameter (Contrato 3 & P1-11 & B9)
  const queryCustomerId =
    initialCustomerId !== undefined
      ? initialCustomerId
      : searchParams?.get("customer_id") || "";
  const queryFilter =
    initialFilter !== undefined
      ? initialFilter
      : searchParams?.get("filter") || "";

  const [highlightedCustomerId, setHighlightedCustomerId] = React.useState<string>(queryCustomerId);
  const [filterHitl, setFilterHitl] = React.useState<boolean>(queryFilter === "hitl");
  const [activeMobileTab, setActiveMobileTab] = React.useState<DecisionStatus>(() => {
    if (queryFilter === "hitl") return "in_review";
    return "in_review";
  });

  // Sincronização em navegação interna / reatividade de props (B4 & B9)
  React.useEffect(() => {
    if (initialFilter !== undefined) {
      setFilterHitl(initialFilter === "hitl");
      if (initialFilter === "hitl") {
        setActiveMobileTab("in_review");
      }
    }
  }, [initialFilter]);

  React.useEffect(() => {
    if (initialCustomerId !== undefined) {
      setHighlightedCustomerId(initialCustomerId);
    }
  }, [initialCustomerId]);

  // Drag-and-Drop state
  const [draggedCard, setDraggedCard] = React.useState<KanbanCardData | null>(null);

  // Modais de Edição e Rejeição (abertura controlada apenas por objeto selecionado, estado de digitação local)
  const [editingCard, setEditingCard] = React.useState<KanbanCardData | null>(null);
  const [rejectingCard, setRejectingCard] = React.useState<KanbanCardData | null>(null);

  // Modo Foco / Tela Cheia (Zen Mode / Focus Mode)
  const [isFocusMode, setIsFocusMode] = React.useState<boolean>(false);

  // Efeito para tecla Escape sair do Modo Foco (se nenhum modal estiver aberto)
  React.useEffect(() => {
    if (!isFocusMode) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (editingCard || rejectingCard) return;
        setIsFocusMode(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFocusMode, editingCard, rejectingCard]);

  // Trava o overflow da janela em modo foco para garantir 100% da viewport sem scroll duplo
  React.useEffect(() => {
    if (isFocusMode) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [isFocusMode]);

  // Contadores rápidos para a barra de ferramentas
  const totalCardsCount = React.useMemo(() => {
    return Object.values(board).reduce((acc, cards) => acc + cards.length, 0);
  }, [board]);

  const hitlCardsCount = React.useMemo(() => {
    return Object.values(board).reduce(
      (acc, cards) => acc + cards.filter((c) => c.human_review).length,
      0
    );
  }, [board]);

  // Efeito para scrollIntoView e anel de destaque com dependência estrita no customer_id (C1-4)
  // Evita re-disparar scroll e resetar aba ativa a cada mutação subsequente do board
  const lastScrolledCustomerIdRef = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (!highlightedCustomerId) {
      lastScrolledCustomerIdRef.current = null;
      return;
    }
    const targetUpper = highlightedCustomerId.trim().toUpperCase();
    if (lastScrolledCustomerIdRef.current === targetUpper) return;
    lastScrolledCustomerIdRef.current = targetUpper;

    const currentBoard = boardRef.current;
    for (const col of Object.keys(currentBoard) as DecisionStatus[]) {
      if (currentBoard[col]?.some((c) => c.customer_id.toUpperCase() === targetUpper)) {
        setActiveMobileTab(col);
        break;
      }
    }

    const timer = setTimeout(() => {
      const isDesktopView =
        typeof window !== "undefined" &&
        window.matchMedia("(min-width: 768px)").matches;
      const targetId = isDesktopView
        ? `kanban-card-desktop-${targetUpper}`
        : `kanban-card-mobile-${targetUpper}`;
      const el = document.getElementById(targetId);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [highlightedCustomerId]);

  // Movimentação genérica de card entre etapas com snapshot e rollback defensivo (B3 & B5)
  const handleMoveCard = React.useCallback(
    async (
      card: KanbanCardData,
      targetColumn: DecisionStatus,
      noteText?: string
    ) => {
      const sourceColumn = card.status;
      if (sourceColumn === targetColumn) return;

      const previousBoard = boardRef.current;
      const currentOperator = operatorStringRef.current;

      const updatedCard: KanbanCardData = {
        ...card,
        status: targetColumn,
        updated_at: new Date().toISOString(),
      };

      setBoard((prev) => {
        const sourceList = (prev[sourceColumn] || []).filter(
          (c) => c.customer_id !== card.customer_id
        );
        const targetList = [
          updatedCard,
          ...(prev[targetColumn] || []).filter(
            (c) => c.customer_id !== card.customer_id
          ),
        ];
        return {
          ...prev,
          [sourceColumn]: sourceList,
          [targetColumn]: targetList,
        };
      });

      try {
        const res = await fetch("/api/agent/decisions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            customer_id: updatedCard.customer_id,
            action_id: updatedCard.action_id,
            action_name: updatedCard.action_name,
            status: targetColumn,
            operator: currentOperator,
            original_message: updatedCard.message,
            final_message: updatedCard.message,
            edited: false,
            notes: noteText || `Movido de ${sourceColumn} para ${targetColumn} via Kanban`,
          }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(
            errData.error || `Falha ao persistir transição de ${updatedCard.customer_id}`
          );
        }

        toast.success(
          `Cliente ${updatedCard.customer_id} movido para ${targetColumn.toUpperCase()} (Auditado em decisions.jsonl)`
        );
      } catch (err: unknown) {
        console.error("Falha ao registrar decisão via Kanban:", err);
        setBoard(previousBoard);
        const msg =
          err instanceof Error
            ? err.message
            : "Erro de rede ao registrar transição no audit trail.";
        toast.error(msg);
      }
    },
    []
  );

  // Handlers estáveis para Drag-and-Drop e ações de card
  const handleDragStart = React.useCallback((card: KanbanCardData) => {
    setDraggedCard(card);
  }, []);

  const handleDrop = React.useCallback(
    (targetColumn: DecisionStatus) => {
      if (!draggedCard) return;
      if (targetColumn === "rejected") {
        setRejectingCard(draggedCard);
        setDraggedCard(null);
        return;
      }
      const card = draggedCard;
      setDraggedCard(null);
      handleMoveCard(card, targetColumn, `Movido via arrastar e soltar (DnD) para ${targetColumn}`);
    },
    [draggedCard, handleMoveCard]
  );

  const handleApprove = React.useCallback(
    (card: KanbanCardData) => {
      handleMoveCard(card, "approved", "Aprovação imediata de recomendação pelo operador");
    },
    [handleMoveCard]
  );

  const handleOpenReject = React.useCallback((card: KanbanCardData) => {
    setRejectingCard(card);
  }, []);

  const handleOpenEdit = React.useCallback((card: KanbanCardData) => {
    setEditingCard(card);
  }, []);

  const handleCloseEdit = React.useCallback(() => {
    setEditingCard(null);
  }, []);

  const handleCloseReject = React.useCallback(() => {
    setRejectingCard(null);
  }, []);

  // P1-10: Salvar Rascunho mantendo etapa atual
  const handleSaveDraft = React.useCallback(
    async (card: KanbanCardData, cleanMessage: string) => {
      const previousBoard = boardRef.current;
      const currentOperator = operatorStringRef.current;

      const updatedCard: KanbanCardData = {
        ...card,
        message: cleanMessage,
        updated_at: new Date().toISOString(),
      };

      setBoard((prev) => {
        const colList = (prev[card.status] || []).map((c) =>
          c.customer_id === card.customer_id ? updatedCard : c
        );
        return {
          ...prev,
          [card.status]: colList,
        };
      });

      setEditingCard(null);

      try {
        const res = await fetch("/api/agent/decisions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            customer_id: card.customer_id,
            action_id: card.action_id,
            action_name: card.action_name,
            status: card.status,
            operator: currentOperator,
            original_message: card.message,
            final_message: cleanMessage,
            edited: true,
            notes: "Rascunho de mensagem personalizado pelo operador mantendo etapa atual",
          }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(
            errData.error || `Falha ao persistir rascunho de ${card.customer_id}`
          );
        }

        toast.success(`Rascunho de mensagem para ${card.customer_id} salvo com sucesso!`);
      } catch (err: unknown) {
        console.error("Erro ao salvar rascunho:", err);
        setBoard(previousBoard);
        const msg =
          err instanceof Error ? err.message : "Erro ao gravar rascunho no servidor.";
        toast.error(msg);
      }
    },
    []
  );

  // P1-10: Salvar & Aprovar movendo para etapa approved
  const handleSaveAndApprove = React.useCallback(
    async (card: KanbanCardData, cleanMessage: string) => {
      const previousBoard = boardRef.current;
      const currentOperator = operatorStringRef.current;
      const sourceColumn = card.status;

      const updatedCard: KanbanCardData = {
        ...card,
        message: cleanMessage,
        status: "approved",
        updated_at: new Date().toISOString(),
      };

      setBoard((prev) => {
        const sourceList = (prev[sourceColumn] || []).filter(
          (c) => c.customer_id !== card.customer_id
        );
        const approvedList = [
          updatedCard,
          ...(prev.approved || []).filter(
            (c) => c.customer_id !== card.customer_id
          ),
        ];
        return {
          ...prev,
          [sourceColumn]: sourceList,
          approved: approvedList,
        };
      });

      setEditingCard(null);

      try {
        const res = await fetch("/api/agent/decisions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            customer_id: card.customer_id,
            action_id: card.action_id,
            action_name: card.action_name,
            status: "approved",
            operator: currentOperator,
            original_message: card.message,
            final_message: cleanMessage,
            edited: true,
            notes: "Mensagem personalizada e aprovada pelo operador",
          }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(
            errData.error || `Falha ao aprovar mensagem de ${card.customer_id}`
          );
        }

        toast.success(`Mensagem de ${card.customer_id} personalizada e aprovada!`);
      } catch (err: unknown) {
        console.error("Erro ao aprovar mensagem editada:", err);
        setBoard(previousBoard);
        const msg =
          err instanceof Error ? err.message : "Erro ao registrar aprovação no servidor.";
        toast.error(msg);
      }
    },
    []
  );

  const handleConfirmReject = React.useCallback(
    (card: KanbanCardData, justification: string) => {
      setRejectingCard(null);
      handleMoveCard(card, "rejected", `Rejeitado pelo operador: ${justification}`);
    },
    [handleMoveCard]
  );

  return (
    <div
      className={cn(
        isFocusMode
          ? "fixed inset-0 z-50 flex flex-col bg-canvas overflow-hidden p-4 sm:p-6 animate-in fade-in duration-150"
          : "space-y-3"
      )}
    >
      {/* Barra Superior do Modo Foco */}
      {isFocusMode ? (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border-subtle shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#07243D] text-white shadow-md">
              <Layers className="h-5 w-5 text-azul-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm sm:text-base font-bold text-azul-navy tracking-tight">
                  AURA 2.0 • Esteira de Retenção (Modo Foco)
                </h2>
                <Badge variant="outline" className="text-[10px] font-mono bg-accent/50 text-azul-action">
                  6 Colunas Ativas
                </Badge>
              </div>
              <p className="text-[11px] text-text-secondary">
                Visão ampliada de tela cheia • Pressione <kbd className="rounded border border-border-dark bg-surface px-1 py-0.2 font-mono text-[10px] text-azul-navy font-semibold">Esc</kbd> para sair
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <Badge variant="outline" className="font-mono text-xs bg-muted/60 text-azul-navy hidden sm:inline-flex">
              Total: {totalCardsCount} {totalCardsCount === 1 ? "cliente" : "clientes"}
            </Badge>

            <Button
              type="button"
              variant={filterHitl ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterHitl(!filterHitl)}
              className={cn(
                "h-8 gap-1.5 text-xs font-semibold cursor-pointer",
                filterHitl
                  ? "bg-amber-600 hover:bg-amber-700 text-white border-amber-600"
                  : "border-border-subtle bg-surface text-text-secondary hover:bg-muted hover:text-azul-navy"
              )}
            >
              <ShieldAlert className={cn("h-3.5 w-3.5", filterHitl ? "text-white" : "text-amber-600")} />
              <span>Apenas HITL ({hitlCardsCount})</span>
            </Button>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setIsFocusMode(false)}
                  className="h-8 gap-1.5 bg-azul-navy hover:bg-azul-navy/90 text-white shadow-xs cursor-pointer text-xs font-semibold"
                  aria-label="Sair do Modo Foco (Esc)"
                >
                  <Minimize2 className="h-3.5 w-3.5 text-azul-primary" />
                  <span>Sair do Modo Foco (Esc)</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                Restaurar visualização normal (ou pressione Esc)
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      ) : (
        /* Barra de Ferramentas do Kanban (Modo Normal) */
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-0.5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="font-mono text-[11px] bg-muted/50 text-text-secondary">
              {totalCardsCount} {totalCardsCount === 1 ? "caso" : "casos"} na esteira
            </Badge>

            <Button
              type="button"
              variant={filterHitl ? "default" : "outline"}
              size="sm"
              onClick={() => setFilterHitl(!filterHitl)}
              className={cn(
                "h-8 gap-1.5 text-xs font-semibold cursor-pointer",
                filterHitl
                  ? "bg-amber-600 hover:bg-amber-700 text-white border-amber-600"
                  : "border-border-subtle bg-surface text-text-secondary hover:bg-muted hover:text-azul-navy"
              )}
            >
              <ShieldAlert className={cn("h-3.5 w-3.5", filterHitl ? "text-white" : "text-amber-600")} />
              <span>Apenas HITL ({hitlCardsCount})</span>
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsFocusMode(true)}
                  className="h-8 gap-1.5 border-border-subtle bg-surface text-azul-navy hover:bg-muted cursor-pointer text-xs font-medium shadow-2xs"
                  aria-label="Modo Foco (Tela Cheia)"
                >
                  <Maximize2 className="h-3.5 w-3.5 text-azul-action" />
                  <span>Modo Foco (Tela Cheia)</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                Expandir esteira ocupando toda a tela (esconde cabeçalho e menu lateral)
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      )}

      {/* Banners Informativos de Filtro e Deep Link (P1-11) */}
      {filterHitl && (
        <div className="flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-300 text-xs text-amber-900 shadow-xs shrink-0">
          <div className="flex items-center gap-2">
            <ShieldAlert className="size-4 text-amber-700 shrink-0" aria-hidden="true" />
            <span>
              Filtro Ativo: Exibindo exclusivamente pendências de <strong>Revisão Humana Mandatória (HITL)</strong>.
            </span>
          </div>
          <button
            type="button"
            onClick={() => setFilterHitl(false)}
            className="text-[11px] font-semibold text-azul-action hover:underline cursor-pointer"
          >
            Exibir todos os cards
          </button>
        </div>
      )}

      {highlightedCustomerId && (
        <div className="flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg bg-azul-primary/10 border border-azul-action/30 text-xs text-azul-navy shadow-xs shrink-0">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-azul-action shrink-0" aria-hidden="true" />
            <span>
              Cliente Selecionado via Link: <strong>{highlightedCustomerId}</strong> (destacado no board).
            </span>
          </div>
          <button
            type="button"
            onClick={() => setHighlightedCustomerId("")}
            className="text-[11px] font-semibold text-azul-action hover:underline cursor-pointer"
          >
            Limpar destaque
          </button>
        </div>
      )}

      {/* VISUALIZAÇÃO MOBILE (< 768px): Radix Tabs por Estágio (P2-20) */}
      {/* Condicional pós-hidratação (C1-1): elimina toda a árvore mobile no desktop */}
      {(!isMounted || !isDesktop) && (
        <div className={cn("block md:hidden", isFocusMode && "flex-1 min-h-0 overflow-y-auto pt-2")}>
          <Tabs
            value={activeMobileTab}
            onValueChange={(val) => setActiveMobileTab(val as DecisionStatus)}
            className="w-full"
          >
            <TabsList className="w-full flex overflow-x-auto justify-start gap-1 p-1 bg-muted/60 rounded-lg">
              {COLUMN_CONFIG.map((col) => {
                const allCards = board[col.id] || [];
                const displayCards = filterHitl ? allCards.filter((c) => c.human_review) : allCards;
                return (
                  <TabsTrigger
                    key={col.id}
                    value={col.id}
                    className="text-xs shrink-0 flex items-center gap-1.5 py-1 px-2.5"
                  >
                    <span>{col.title.replace(/^\d+\.\s*/, "")}</span>
                    <span className="rounded-full bg-surface px-1.5 py-0.2 text-[10px] font-mono font-bold text-azul-navy shadow-2xs">
                      {displayCards.length}
                    </span>
                  </TabsTrigger>
                );
              })}
            </TabsList>

            {COLUMN_CONFIG.map((col) => {
              const allCards = board[col.id] || [];
              const displayCards = filterHitl ? allCards.filter((c) => c.human_review) : allCards;

              return (
                <TabsContent key={col.id} value={col.id} className="mt-3">
                  <div
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={() => handleDrop(col.id)}
                    className={`rounded-lg border border-border-subtle bg-surface shadow-xs flex flex-col min-h-[460px] ${col.accentColor} border-t-4`}
                  >
                    <div className="p-3 border-b border-border-subtle bg-muted/20 flex items-center justify-between">
                      <div>
                        <h3 className="text-xs font-bold text-azul-navy tracking-tight">{col.title}</h3>
                        <p className="text-[10px] text-text-muted mt-0.5">{col.description}</p>
                      </div>
                      <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-mono font-bold text-text-primary">
                        {displayCards.length} cards
                      </span>
                    </div>

                    <div className="flex-1 p-2 space-y-2.5">
                      {displayCards.length === 0 ? (
                        <div className="h-32 flex items-center justify-center rounded border border-dashed border-border-subtle text-[11px] text-text-muted text-center p-3">
                          Nenhum card nesta etapa.
                        </div>
                      ) : (
                        displayCards.map((card) => (
                          <KanbanCard
                            key={card.customer_id}
                            card={card}
                            currentColumnId={col.id}
                            viewport="mobile"
                            isTargetHighlighted={
                              Boolean(highlightedCustomerId) &&
                              card.customer_id.toUpperCase() === highlightedCustomerId.toUpperCase()
                            }
                            onDragStart={handleDragStart}
                            onApprove={handleApprove}
                            onOpenReject={handleOpenReject}
                            onOpenEdit={handleOpenEdit}
                            onMoveCard={handleMoveCard}
                          />
                        ))
                      )}
                    </div>
                  </div>
                </TabsContent>
              );
            })}
          </Tabs>
        </div>
      )}

      {/* VISUALIZAÇÃO TABLET & DESKTOP (>= 768px): Rolagem Horizontal Fluida com Colunas Estáveis (P2-20) */}
      {/* Condicional pós-hidratação (C1-1): elimina toda a árvore desktop no mobile */}
      {(!isMounted || isDesktop) && (
        <div
          className={cn(
            "hidden md:flex overflow-x-auto gap-3.5 items-stretch",
            isFocusMode ? "flex-1 min-h-0 pt-2 pb-1" : "pb-4 items-start"
          )}
        >
          {COLUMN_CONFIG.map((col) => {
            const allCards = board[col.id] || [];
            const displayCards = filterHitl ? allCards.filter((c) => c.human_review) : allCards;

            return (
              <div
                key={col.id}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => handleDrop(col.id)}
                className={cn(
                  "rounded-lg border border-border-subtle bg-surface shadow-xs flex flex-col border-t-4",
                  col.accentColor,
                  isFocusMode
                    ? "flex-1 min-w-[210px] max-w-none h-full"
                    : "min-h-[520px] max-h-[750px] w-[280px] shrink-0"
                )}
              >
                {/* Header da Coluna */}
                <div className="p-3 border-b border-border-subtle bg-muted/20 shrink-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-azul-navy tracking-tight">{col.title}</h3>
                    <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-mono font-bold text-text-primary">
                      {displayCards.length}
                    </span>
                  </div>
                  <p className="text-[10px] text-text-muted mt-0.5">{col.description}</p>
                </div>

                {/* Lista de Cards */}
                <div className="flex-1 overflow-y-auto p-2 space-y-2.5 min-h-0">
                  {displayCards.length === 0 ? (
                    <div className="h-28 flex items-center justify-center rounded border border-dashed border-border-subtle text-[11px] text-text-muted text-center p-3">
                      Nenhum cliente nesta etapa. Arraste cards aqui.
                    </div>
                  ) : (
                    displayCards.map((card) => (
                      <KanbanCard
                        key={card.customer_id}
                        card={card}
                        currentColumnId={col.id}
                        viewport="desktop"
                        isTargetHighlighted={
                          Boolean(highlightedCustomerId) &&
                          card.customer_id.toUpperCase() === highlightedCustomerId.toUpperCase()
                        }
                        onDragStart={handleDragStart}
                        onApprove={handleApprove}
                        onOpenReject={handleOpenReject}
                        onOpenEdit={handleOpenEdit}
                        onMoveCard={handleMoveCard}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal de Edição de Mensagem isolado (C1-2) */}
      <EditMessageModal
        card={editingCard}
        operatorString={operatorString}
        onClose={handleCloseEdit}
        onSaveDraft={handleSaveDraft}
        onSaveAndApprove={handleSaveAndApprove}
      />

      {/* Diálogo de Rejeição Justificada isolado (C1-2) */}
      <RejectJustificationModal
        card={rejectingCard}
        operatorString={operatorString}
        onClose={handleCloseReject}
        onConfirmReject={handleConfirmReject}
      />
    </div>
  );
}

export function KanbanBoard(props: KanbanBoardProps) {
  return (
    <React.Suspense
      fallback={
        <div className="grid grid-cols-1 md:grid-cols-5 xl:grid-cols-6 gap-3.5 animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-96 rounded-lg bg-muted/40 border border-border-subtle" />
          ))}
        </div>
      }
    >
      <KanbanBoardInner {...props} />
    </React.Suspense>
  );
}
