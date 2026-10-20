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
      await fs.promises.mkdir(dir, { recursive: true });
    }

    const line = JSON.stringify(validated) + '\n';
    await fs.promises.appendFile(filePath, line, { encoding: 'utf8' });

    // Coordenação cache/append: a leitura inicial de decisions.jsonl pode estar em voo
    // com um snapshot capturado ANTES deste append. Aguardamos a MESMA promise de carga
    // (loadDecisionsCache reutiliza loadPromise em voo; nunca dispara uma segunda leitura
    // concorrente), garantindo que o cache exista ao final da gravação. Se o snapshot em
    // voo for anterior ao append, o registro ainda não estará no cache e é inserido abaixo;
    // se o snapshot já o incluir (leitura pós-append), a checagem de identidade da cabeça
    // evita a inserção duplicada.
    await loadDecisionsCache();

    if (decisionsCache) {
      const cleanId = fullRecord.customer_id.trim().toUpperCase();
      const decisionsList = decisionsCache.decisions;
      const head = decisionsList.length > 0 ? decisionsList[0] : null;
      const alreadyAtHead =
        head !== null &&
        head.timestamp === fullRecord.timestamp &&
        head.customer_id === fullRecord.customer_id &&
        head.hash_signature === fullRecord.hash_signature;

      if (!alreadyAtHead) {
        decisionsList.unshift(fullRecord);
        const list = decisionsCache.byCustomer.get(cleanId) || [];
        list.unshift(fullRecord);
        decisionsCache.byCustomer.set(cleanId, list);
        if (cleanId !== fullRecord.customer_id) {
          const rawList = decisionsCache.byCustomer.get(fullRecord.customer_id) || [];
          rawList.unshift(fullRecord);
          decisionsCache.byCustomer.set(fullRecord.customer_id, rawList);
        }
      }
    }

    return fullRecord;
  });
}

// Cache em memória para evitar releitura e re-parse contínuos de decisions.jsonl
interface DecisionsCache {
  decisions: DecisionRecord[];
  corrupted_lines: number[];
  byCustomer: Map<string, DecisionRecord[]>;
}

let decisionsCache: DecisionsCache | null = null;
let loadPromise: Promise<DecisionsCache> | null = null;

export function _clearDecisionsCacheForTesting(): void {
  decisionsCache = null;
  loadPromise = null;
}

async function loadDecisionsCache(): Promise<DecisionsCache> {
  if (decisionsCache) return decisionsCache;
  if (loadPromise) return loadPromise;

  loadPromise = (async () => {
    const filePath = getDecisionsFilePath();
    const decisions: DecisionRecord[] = [];
    const corrupted_lines: number[] = [];
    const byCustomer = new Map<string, DecisionRecord[]>();

    try {
      const content = await fs.promises.readFile(filePath, 'utf8');
      const lines = content.split('\n');

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        try {
          const parsed = JSON.parse(line) as DecisionRecord;
          decisions.push(parsed);
        } catch (err) {
          console.warn(`[WARN decisions.jsonl] Linha ${i + 1} corrompida ignorada na leitura:`, err);
          corrupted_lines.push(i + 1);
        }
      }

      // Ordena por data decrescente (mais recente primeiro) UMA VEZ no parse inicial
      decisions.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      for (const d of decisions) {
        const cleanId = d.customer_id.trim().toUpperCase();
        let list = byCustomer.get(cleanId);
        if (!list) {
          list = [];
          byCustomer.set(cleanId, list);
        }
        list.push(d);

        if (d.customer_id !== cleanId) {
          let rawList = byCustomer.get(d.customer_id);
          if (!rawList) {
            rawList = [];
            byCustomer.set(d.customer_id, rawList);
          }
          rawList.push(d);
        }
      }
    } catch (err: any) {
      if (err.code !== 'ENOENT') {
        console.error('Erro ao ler decisions.jsonl:', err);
      }
    }

    decisionsCache = { decisions, corrupted_lines, byCustomer };
    loadPromise = null;
    return decisionsCache;
  })();

  return loadPromise;
}

/**
 * Lê o histórico de decisões em decisions.jsonl com cache assíncrono em memória.
 * Protocolo Fail Loud: linhas corrompidas geram log explícito com número da linha.
 */
export async function getRecordedDecisions(customerId?: string): Promise<{
  decisions: DecisionRecord[];
  corrupted_lines: number[];
}> {
  const cached = await loadDecisionsCache();

  if (customerId) {
    const cleanId = customerId.trim().toUpperCase();
    const list = cached.byCustomer.get(cleanId) || cached.byCustomer.get(customerId) || [];
    return {
      decisions: [...list],
      corrupted_lines: cached.corrupted_lines,
    };
  }

  return {
    decisions: [...cached.decisions],
    corrupted_lines: cached.corrupted_lines,
  };
}
