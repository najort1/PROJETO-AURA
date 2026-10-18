export interface ToolExecution {
  turn?: number;
  call_id?: string;
  tool?: string;
  arguments?: Record<string, unknown>;
  result_summary?: string;
}

export interface DecisionItem {
  timestamp: string;
  customer_id: string;
  action_id: string;
  action_name: string;
  status: 'suggested' | 'in_review' | 'approved' | 'edited' | 'dispatched' | 'completed' | 'rejected';
  operator?: string;
  original_message?: string;
  final_message: string;
  edited?: boolean;
  notes?: string | null;
  hash_signature: string;
  homologated?: boolean;
}

export interface ChatMessage {
  id: string; // crypto.randomUUID()
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  thought_process?: string[];
  tools_executed?: ToolExecution[];
  decisions_taken?: DecisionItem[];
  turns?: number;
  human_review_required?: boolean;
  finish_reason?: string;
  isStreaming?: boolean;
  isError?: boolean;
}

export interface ConciergeTelemetry {
  status: 'online' | 'offline';
  model: string;
  base_url: string;
  tools_available: string[];
}

export type ChatStatus = 'idle' | 'sending' | 'aborted' | 'error';

export interface PresetCustomer {
  id: string;
  label: string;
}

export const PRESET_CUSTOMERS: PresetCustomer[] = [
  { id: 'C000030', label: 'C000030 (Topázio • Atraso 31m • VaR R$ 2.4k)' },
  { id: 'C000032', label: 'C000032 (Diamante • Atraso Severo • VaR R$ 9.7k)' },
  { id: 'C000004', label: 'C000004 (Azul • Atraso 70m & Preço • Regional)' },
  { id: 'C038454', label: 'C038454 (Topázio • Churn 62% • Lazer)' },
];
