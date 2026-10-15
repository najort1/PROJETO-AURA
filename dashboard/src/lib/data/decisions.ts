import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { DecisionRecordSchema } from '../../types/actions.ts';
import type { DecisionRecord } from '../../types/actions.ts';

function getAnalyticsDir(): string {
  const directPath = path.resolve(process.cwd(), 'data/analytics');
  if (fs.existsSync(directPath)) return directPath;
  const parentPath = path.resolve(process.cwd(), '../data/analytics');
  if (fs.existsSync(parentPath)) return parentPath;
  // Fallback seguro criando o diretório local se necessário
  return directPath;
}

function getDecisionsFilePath(): string {
  const dir = getAnalyticsDir();
  return path.join(dir, 'decisions.jsonl');
}

function computeDecisionHash(record: Omit<DecisionRecord, 'hash_signature'>): string {
  const payload = [
    record.timestamp,
    record.customer_id,
    record.action_id,
    record.status,
    record.operator,
    record.final_message.trim(),
  ].join('|');
  return crypto.createHash('sha256').update(payload, 'utf8').digest('hex');
}

// Mutex em memória para controle de concorrência no processo Node.js
let isWriting = false;
const writeQueue: Array<() => Promise<void>> = [];

async function enqueueWrite<T>(op: () => Promise<T>): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const task = async () => {
      try {
        const res = await op();
        resolve(res);
      } catch (err) {
        reject(err);
      }
    };
    writeQueue.push(task);
    processNext();
  });
}

function processNext() {
  if (isWriting || writeQueue.length === 0) return;
  isWriting = true;
  const next = writeQueue.shift()!;
  next().finally(() => {
    isWriting = false;
    processNext();
  });
}

/**
 * Registra a decisão do operador de forma atômica com dual-write em decisions.jsonl.
 * Preserva retrocompatibilidade total com pipelines Python (app/loader.py e tests/test_app_smoke.py).
 */
export async function recordDecision(input: {
  customer_id: string;
  action_id: string;
  action_name: string;
  status: 'suggested' | 'in_review' | 'approved' | 'edited' | 'dispatched' | 'completed' | 'rejected';
  operator?: string;
  original_message: string;
  final_message: string;
  edited?: boolean;
  notes?: string | null;
}): Promise<DecisionRecord> {
  const timestamp = new Date().toISOString();
  const operator = input.operator || 'operador_nextjs';
  const edited =
    typeof input.edited === 'boolean'
      ? input.edited
      : input.original_message.trim() !== input.final_message.trim();

  const partialRecord: Omit<DecisionRecord, 'hash_signature'> = {
    timestamp,
    customer_id: input.customer_id,
    action_id: input.action_id,
    action_name: input.action_name,
    status: input.status,
    operator,
    original_message: input.original_message,
    final_message: input.final_message,
    edited,
    notes: input.notes ?? null,
  };

  const hash_signature = computeDecisionHash(partialRecord);
  const fullRecord: DecisionRecord = {
    ...partialRecord,
    hash_signature,
  };

  // Validação estrita via Zod
  const validated = DecisionRecordSchema.parse(fullRecord);

  // Execução atômica e segura contra colisão de I/O
  return enqueueWrite(async () => {
    const filePath = getDecisionsFilePath();
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const line = JSON.stringify(validated) + '\n';
    // Append síncrono atômico
    fs.appendFileSync(filePath, line, { encoding: 'utf8' });

    return fullRecord;
  });
}

/**
 * Lê o histórico de decisões em decisions.jsonl.
 * Protocolo Fail Loud: linhas corrompidas geram log explícito com número da linha.
 */
export async function getRecordedDecisions(customerId?: string): Promise<{
  decisions: DecisionRecord[];
  corrupted_lines: number[];
}> {
  const filePath = getDecisionsFilePath();
  const decisions: DecisionRecord[] = [];
  const corrupted_lines: number[] = [];

  if (!fs.existsSync(filePath)) {
    return { decisions, corrupted_lines };
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    try {
      const parsed = JSON.parse(line);
      if (customerId && parsed.customer_id !== customerId) {
        continue;
      }
      decisions.push(parsed as DecisionRecord);
    } catch (err) {
      console.warn(`[WARN decisions.jsonl] Linha ${i + 1} corrompida ignorada na leitura:`, err);
      corrupted_lines.push(i + 1);
    }
  }

  // Ordena por data decrescente (mais recente primeiro)
  decisions.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return { decisions, corrupted_lines };
}
