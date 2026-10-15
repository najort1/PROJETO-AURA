import { z } from 'zod';
import type { TierLevel } from './analytics.ts';

export interface CitationItem {
  fact_id: string;
  text?: string;
  quote?: string;
  verification_status: string;
  valid_from: string;
  snapshot_version: string;
  source_label?: string;
  source?: string;
  score?: number;
}

export interface AgentRecommendation {
  customer_id: string;
  action_id: string;
  action_name: string;
  channel: 'whatsapp' | 'email' | 'app_push' | 'telefone' | 'nenhum' | string;
  message: string;
  justification_json: string;
  citations_json: string;
  citations: CitationItem[];
  confidence: number;
  human_review: boolean;
  mode: string;
  snapshot_version: string;
  recommended_at: string;
}

export type DecisionStatus =
  | 'suggested'
  | 'in_review'
  | 'approved'
  | 'edited'
  | 'dispatched'
  | 'completed'
  | 'rejected';

export const DecisionRecordSchema = z.object({
  timestamp: z.string().datetime().optional(), // ISO-8601 UTC
  customer_id: z.string().min(3),
  action_id: z.string().min(3),
  action_name: z.string().min(2),
  status: z.enum(['suggested', 'in_review', 'approved', 'edited', 'dispatched', 'completed', 'rejected']),
  operator: z.string().default('operador_nextjs'),
  original_message: z.string(),
  final_message: z.string(),
  edited: z.boolean().default(false),
  notes: z.string().nullable().optional(),
  hash_signature: z.string().optional(),
});

export type DecisionRecord = z.infer<typeof DecisionRecordSchema> & {
  timestamp: string;
  edited: boolean;
};

export interface KanbanCardData {
  customer_id: string;
  tier: TierLevel;
  persona: string;
  valor_em_risco: number;
  clv_12m_previsto: number;
  churn_prob: number;
  action_id: string;
  action_name: string;
  channel: string;
  message: string;
  human_review: boolean;
  status: DecisionStatus;
  has_citations: boolean;
  updated_at: string;
}

export interface KanbanBoardState {
  columns: Record<DecisionStatus, KanbanCardData[]>;
  total_cards: number;
}
