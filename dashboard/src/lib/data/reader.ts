import fs from 'fs';
import path from 'path';
import { parquetRead } from 'hyparquet';
import { compressors } from 'hyparquet-compressors';
import type {
  CustomerScore,
  PersonaSummary,
  CustomerTimelineEvent,
  ClvShapRecord,
  FrictionRecord,
  FairnessMetric,
  PortfolioSummary,
  PortfolioCharts,
  HistogramBin,
  LorenzPoint,
  PersonaVarBarItem,
  TierLevel,
} from '../../types/analytics.ts';
import type {
  AgentRecommendation,
  CitationItem,
  KanbanBoardState,
  DecisionStatus,
  DecisionRecord,
} from '../../types/actions.ts';
import { getRecordedDecisions } from './decisions.ts';

// Resolve o caminho de data/analytics em qualquer ambiente de execução
function resolveAnalyticsPath(fileName: string): string {
  const directPath = path.resolve(process.cwd(), 'data/analytics', fileName);
  if (fs.existsSync(directPath)) return directPath;
  const parentPath = path.resolve(process.cwd(), '../data/analytics', fileName);
  if (fs.existsSync(parentPath)) return parentPath;
  throw new Error(`Arquivo não encontrado em data/analytics: ${fileName}`);
}

// Normaliza BigInt para Number para segurança na serialização JSON do Next.js
function sanitizeRow<T extends Record<string, any>>(row: T): T {
  const result: Record<string, any> = {};
  for (const [key, value] of Object.entries(row)) {
    if (typeof value === 'bigint') {
      result[key] = Number(value);
    } else {
      result[key] = value;
    }
  }
  return result as T;
}

// Helper para ler qualquer Parquet em array de objetos tipados
async function readParquetFile<T extends Record<string, any>>(fileName: string): Promise<T[]> {
  const filePath = resolveAnalyticsPath(fileName);
  const fileBuffer = fs.readFileSync(filePath);
  const arrayBuffer = fileBuffer.buffer.slice(
    fileBuffer.byteOffset,
    fileBuffer.byteOffset + fileBuffer.byteLength
  );

  return new Promise<T[]>((resolve, reject) => {
    parquetRead({
      file: arrayBuffer,
      compressors,
      rowFormat: 'object',
      onComplete: (data: any[]) => {
        const sanitized = data.map((row) => sanitizeRow<T>(row));
        resolve(sanitized);
      },
    }).catch(reject);
  });
}

// Cache em memória (Singleton) para evitar re-leitura contínua dos arquivos em disco
interface InMemoryCache {
  customersScores: CustomerScore[] | null;
  customersById: Map<string, CustomerScore> | null;
  sortedCustomersByVar: CustomerScore[] | null;
  personasSummary: PersonaSummary[] | null;
  customerTimeline: CustomerTimelineEvent[] | null;
  timelineByCustomer: Map<string, CustomerTimelineEvent[]> | null;
  agentRecommendations: AgentRecommendation[] | null;
  recommendationsById: Map<string, AgentRecommendation> | null;
  recommendationsHumanReviewTrue: AgentRecommendation[] | null;
  recommendationsHumanReviewFalse: AgentRecommendation[] | null;
  top150Recommendations: AgentRecommendation[] | null;
  top150CustomerIdsSet: Set<string> | null;
  clvShap: ClvShapRecord[] | null;
  shapById: Map<string, ClvShapRecord> | null;
  frictionMap: FrictionRecord[] | null;
  fairnessMetrics: FairnessMetric[] | null;
  portfolioSummary: PortfolioSummary | null;
  portfolioCharts: PortfolioCharts | null;
  lastLoaded: number;
}

const cache: InMemoryCache = {
  customersScores: null,
  customersById: null,
  sortedCustomersByVar: null,
  personasSummary: null,
  customerTimeline: null,
  timelineByCustomer: null,
  agentRecommendations: null,
  recommendationsById: null,
  recommendationsHumanReviewTrue: null,
  recommendationsHumanReviewFalse: null,
  top150Recommendations: null,
  top150CustomerIdsSet: null,
  clvShap: null,
  shapById: null,
  frictionMap: null,
  fairnessMetrics: null,
  portfolioSummary: null,
  portfolioCharts: null,
  lastLoaded: 0,
};

export function _clearReaderCacheForTesting(): void {
  cache.customersScores = null;
  cache.customersById = null;
  cache.sortedCustomersByVar = null;
  cache.personasSummary = null;
  cache.customerTimeline = null;
  cache.timelineByCustomer = null;
  cache.agentRecommendations = null;
  cache.recommendationsById = null;
  cache.recommendationsHumanReviewTrue = null;
  cache.recommendationsHumanReviewFalse = null;
  cache.top150Recommendations = null;
  cache.top150CustomerIdsSet = null;
  cache.clvShap = null;
  cache.shapById = null;
  cache.frictionMap = null;
  cache.fairnessMetrics = null;
  cache.portfolioSummary = null;
  cache.portfolioCharts = null;
  cache.lastLoaded = 0;
}

/**
 * Retorna os 50.000 clientes com scores, tiers, personas e métricas
 */
export async function getCustomersScores(): Promise<CustomerScore[]> {
  if (cache.customersScores) return cache.customersScores;
  const raw = await readParquetFile<CustomerScore>('customers_scores.parquet');
  cache.customersScores = raw;

  const byId = new Map<string, CustomerScore>();
  for (const c of raw) {
    byId.set(c.customer_id.trim().toUpperCase(), c);
  }
  cache.customersById = byId;

  // Pré-ordena por maior valor_em_risco desc uma única vez
  cache.sortedCustomersByVar = [...raw].sort(
    (a, b) => (Number(b.valor_em_risco) || 0) - (Number(a.valor_em_risco) || 0)
  );

  return raw;
}

/**
 * Retorna um cliente específico por customer_id em O(1) via Map indexado
 */
export async function getCustomerById(id: string): Promise<CustomerScore | null> {
  if (!cache.customersById) {
    await getCustomersScores();
  }
  const cleanId = id.trim().toUpperCase();
  return cache.customersById?.get(cleanId) || null;
}

/**
 * Retorna a lista completa de clientes pré-ordenada por valor_em_risco desc (cache O(1))
 */
export async function getSortedCustomersByVar(): Promise<CustomerScore[]> {
  if (cache.sortedCustomersByVar) return cache.sortedCustomersByVar;
  await getCustomersScores();
  return cache.sortedCustomersByVar!;
}

/**
 * Retorna os top N clientes com maior valor em risco (cache O(1))
 */
export async function getTopCustomersByVar(limit = 5): Promise<CustomerScore[]> {
  const sorted = await getSortedCustomersByVar();
  return sorted.slice(0, limit);
}

/**
 * Retorna o sumário analítico das 6 personas
 */
export async function getPersonasSummary(): Promise<PersonaSummary[]> {
  if (cache.personasSummary) return cache.personasSummary;
  const raw = await readParquetFile<PersonaSummary>('personas_summary.parquet');
  // Ordena por clientes_count descendente
  raw.sort((a, b) => b.clientes_count - a.clientes_count);
  cache.personasSummary = raw;
  return raw;
}

async function ensureTimelineLoaded(): Promise<void> {
  if (cache.timelineByCustomer && cache.customerTimeline) return;
  const raw = await readParquetFile<CustomerTimelineEvent>('customer_timeline.parquet');
  // Filtro temporal mandatório (Anti-Data Leakage)
  const filtered = raw.filter((ev) => ev.data <= '2025-08-31');
  cache.customerTimeline = filtered;

  const byCustomer = new Map<string, CustomerTimelineEvent[]>();
  for (const ev of filtered) {
    const key = ev.customer_id.trim().toUpperCase();
    const list = byCustomer.get(key);
    if (list) {
      list.push(ev);
    } else {
      byCustomer.set(key, [ev]);
    }
  }

  // Pré-ordena cada timeline individual cronologicamente decrescente uma única vez
  for (const events of byCustomer.values()) {
    events.sort((a, b) => (b.data > a.data ? 1 : b.data < a.data ? -1 : 0));
  }

  cache.timelineByCustomer = byCustomer;
}

/**
 * Retorna a linha do tempo de um cliente específico em O(1) via Map indexado
 */
export async function getTimelineByCustomerId(id: string): Promise<CustomerTimelineEvent[]> {
  await ensureTimelineLoaded();
  const cleanId = id.trim().toUpperCase();
  const events = cache.timelineByCustomer?.get(cleanId);
  return events ? [...events] : [];
}

/**
 * Retorna os eventos da linha do tempo do cliente.
 * Aplica o guardrail temporal estrito anti-vazamento: data_evento <= '2025-08-31'
 */
export async function getCustomerTimeline(customerId?: string): Promise<CustomerTimelineEvent[]> {
  if (customerId) {
    return getTimelineByCustomerId(customerId);
  }

  await ensureTimelineLoaded();
  return [...(cache.customerTimeline || [])].sort((a, b) => (b.data > a.data ? 1 : b.data < a.data ? -1 : 0));
}

/**
 * Retorna as recomendações do Agente de Retenção com citações do regulamento parseadas
 */
export async function getAgentRecommendations(): Promise<AgentRecommendation[]> {
  if (cache.agentRecommendations) return cache.agentRecommendations;

  const raw = await readParquetFile<any>('agent_recommendations.parquet');
  const processed: AgentRecommendation[] = raw.map((row) => {
    let citations: CitationItem[] = [];
    if (row.citations_json) {
      try {
        citations = typeof row.citations_json === 'string'
          ? JSON.parse(row.citations_json)
          : row.citations_json;
      } catch {
        citations = [];
      }
    }

    return {
      customer_id: row.customer_id,
      action_id: row.action_id,
      action_name: row.action_name,
      channel: row.channel,
      message: row.message,
      justification_json: row.justification_json,
      citations_json: row.citations_json,
      citations,
      confidence: Number(row.confidence),
      human_review: Boolean(row.human_review),
      mode: row.mode,
      snapshot_version: row.snapshot_version,
      recommended_at: row.recommended_at,
    };
  });

  cache.agentRecommendations = processed;

  const byId = new Map<string, AgentRecommendation>();
  const hrTrue: AgentRecommendation[] = [];
  const hrFalse: AgentRecommendation[] = [];

  for (const r of processed) {
    byId.set(r.customer_id.trim().toUpperCase(), r);
    if (r.human_review) {
      hrTrue.push(r);
    } else {
      hrFalse.push(r);
    }
  }

  cache.recommendationsById = byId;
  cache.recommendationsHumanReviewTrue = hrTrue;
  cache.recommendationsHumanReviewFalse = hrFalse;

  return processed;
}

/**
 * Retorna a recomendação do agente para um cliente específico em O(1) via Map indexado
 */
export async function getRecommendationByCustomerId(id: string): Promise<AgentRecommendation | null> {
  if (!cache.recommendationsById) {
    await getAgentRecommendations();
  }
  const cleanId = id.trim().toUpperCase();
  return cache.recommendationsById?.get(cleanId) || null;
}

/**
 * Retorna o subconjunto pré-filtrado de recomendações com ou sem human_review em O(1)
 */
export async function getAgentRecommendationsByHumanReview(isHumanReview: boolean): Promise<AgentRecommendation[]> {
  if (!cache.recommendationsHumanReviewTrue || !cache.recommendationsHumanReviewFalse) {
    await getAgentRecommendations();
  }
  return isHumanReview ? cache.recommendationsHumanReviewTrue! : cache.recommendationsHumanReviewFalse!;
}

/**
 * Retorna os fatores locais SHAP do modelo de CLV para o gráfico Waterfall
 */
export async function getClvShap(): Promise<ClvShapRecord[]> {
  if (cache.clvShap) return cache.clvShap;
  const raw = await readParquetFile<ClvShapRecord>('clv_shap.parquet');
  cache.clvShap = raw;

  const byId = new Map<string, ClvShapRecord>();
  for (const s of raw) {
    byId.set(s.customer_id.trim().toUpperCase(), s);
  }
  cache.shapById = byId;

  return raw;
}

/**
 * Retorna os fatores locais SHAP de um cliente específico em O(1) via Map indexado
 */
export async function getClvShapById(id: string): Promise<ClvShapRecord | null> {
  if (!cache.shapById) {
    await getClvShap();
  }
  const cleanId = id.trim().toUpperCase();
  return cache.shapById?.get(cleanId) || null;
}

/**
 * Retorna o mapa de atritos em 7 aspectos ao longo dos 7 semestres
 */
export async function getFrictionMap(): Promise<FrictionRecord[]> {
  if (cache.frictionMap) return cache.frictionMap;
  const raw = await readParquetFile<FrictionRecord>('friction_map.parquet');
  cache.frictionMap = raw;
  return raw;
}

/**
 * Retorna as 16 linhas de auditoria Four-Fifths de IA Responsável
 */
export async function getFairnessMetrics(): Promise<FairnessMetric[]> {
  if (cache.fairnessMetrics) return cache.fairnessMetrics;
  const raw = await readParquetFile<FairnessMetric>('fairness_metrics.parquet');
  cache.fairnessMetrics = raw;
  return raw;
}

/**
 * Calcula e retorna os KPIs consolidados da carteira para a Tela 01 (/carteira)
 */
export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  if (cache.portfolioSummary) return cache.portfolioSummary;

  const customers = await getCustomersScores();
  const total_customers = customers.length;

  let var_total = 0;
  let clv_total = 0;
  let alto_valor_count = 0;
  const clv_list: number[] = [];

  for (const c of customers) {
    const clv = Number(c.clv_12m_previsto || 0);
    const churn = Number(c.churn_prob || 0);
    clv_total += clv;
    var_total += clv * churn;
    clv_list.push(clv);
    if (c.alto_valor) {
      alto_valor_count++;
    }
  }

  clv_list.sort((a, b) => a - b);
  const media_clv = total_customers > 0 ? clv_total / total_customers : 0;
  const mediana_clv =
    total_customers > 0
      ? (clv_list[Math.floor(total_customers / 2)] +
          clv_list[Math.ceil(total_customers / 2)]) /
        2
      : 0;

  // Cálculo do Gini via Trapézio (paridade estrita com app/views/01_carteira.py)
  let trapSum = 0;
  let cumClv = 0;
  for (let i = 0; i < total_customers; i++) {
    const prevCum = cumClv / clv_total;
    cumClv += clv_list[i];
    const currCum = cumClv / clv_total;
    const dx = 1 / total_customers;
    trapSum += ((prevCum + currCum) / 2) * dx;
  }
  const gini = Number((1.0 - 2.0 * trapSum).toFixed(2));

  // Ponto 80/20: Top 20% detém qual % do CLV?
  const idx80 = Math.floor(total_customers * 0.8);
  let clvBottom80 = 0;
  for (let i = 0; i < idx80; i++) {
    clvBottom80 += clv_list[i];
  }
  const pareto_80_20_clv_pct = Number(((1.0 - clvBottom80 / clv_total) * 100).toFixed(1));

  const summary: PortfolioSummary = {
    total_customers,
    var_total: Number(var_total.toFixed(2)),
    clv_total: Number(clv_total.toFixed(2)),
    alto_valor_count,
    alto_valor_pct: Number((alto_valor_count / total_customers).toFixed(4)),
    custo_medio_acao: 45.0, // [PREMISSA DE NEGÓCIO]
    gini,
    pareto_80_20_clv_pct,
    media_clv: Number(media_clv.toFixed(2)),
    mediana_clv: Number(mediana_clv.toFixed(2)),
  };

  cache.portfolioSummary = summary;
  return summary;
}

/**
 * Gera as séries de dados dos gráficos da Tela 01 (Histograma, Lorenz, VaR por Persona)
 */
export async function getPortfolioCharts(): Promise<PortfolioCharts> {
  if (cache.portfolioCharts) return cache.portfolioCharts;

  const [customers, personas, summary] = await Promise.all([
    getCustomersScores(),
    getPersonasSummary(),
    getPortfolioSummary(),
  ]);

  const clvValues = customers.map((c) => Number(c.clv_12m_previsto || 0)).sort((a, b) => a - b);
  const total = clvValues.length;
  const p95Value = clvValues[Math.floor(total * 0.95)] || 2950;

  // 1. Histograma de CLV (15 faixas de 0 a R$ 6.000+)
  const binStep = 400;
  const maxBin = 6000;
  const numBins = Math.ceil(maxBin / binStep);
  const bins: HistogramBin[] = [];

  for (let b = 0; b < numBins; b++) {
    const start = b * binStep;
    const end = (b + 1) * binStep;
    bins.push({
      bin_start: start,
      bin_end: end,
      label: `R$ ${start}-${end}`,
      count: 0,
      is_p95: end >= p95Value,
    });
  }
  // Último bin overflow (+6000)
  const overflowBin: HistogramBin = {
    bin_start: maxBin,
    bin_end: 50000,
    label: `R$ ${maxBin}+`,
    count: 0,
    is_p95: true,
  };

  for (const v of clvValues) {
    if (v >= maxBin) {
      overflowBin.count++;
    } else {
      const idx = Math.min(Math.floor(v / binStep), numBins - 1);
      bins[idx].count++;
    }
  }
  const histogram = [...bins, overflowBin];

  // 2. Curva de Lorenz (100 pontos para alta resolução suave)
  const lorenz_curve: LorenzPoint[] = [{ p: 0, l_p: 0 }];
  const steps = 100;
  const stepSize = Math.floor(total / steps);
  let runningClv = 0;
  const totalClv = summary.clv_total;

  for (let s = 1; s <= steps; s++) {
    const endIdx = s === steps ? total : s * stepSize;
    const startIdx = (s - 1) * stepSize;
    for (let i = startIdx; i < endIdx; i++) {
      runningClv += clvValues[i];
    }
    const p = Number((endIdx / total).toFixed(4));
    const l_p = Number((runningClv / totalClv).toFixed(4));
    lorenz_curve.push({ p, l_p });
  }

  // 3. VaR e CLV por Persona
  const personaMap: Record<
    string,
    { var_total: number; clv_total: number; count: number; churn_sum: number }
  > = {};

  for (const c of customers) {
    if (!personaMap[c.persona]) {
      personaMap[c.persona] = { var_total: 0, clv_total: 0, count: 0, churn_sum: 0 };
    }
    const clv = Number(c.clv_12m_previsto || 0);
    const churn = Number(c.churn_prob || 0);
    personaMap[c.persona].var_total += clv * churn;
    personaMap[c.persona].clv_total += clv;
    personaMap[c.persona].churn_sum += churn;
    personaMap[c.persona].count++;
  }

  const persona_var: PersonaVarBarItem[] = personas.map((p) => {
    const metrics = personaMap[p.persona] || {
      var_total: 0,
      clv_total: 0,
      count: p.clientes_count,
      churn_sum: 0,
    };
    return {
      persona: p.persona,
      nome_display: p.nome_display,
      cor: p.cor,
      var_total: Number(metrics.var_total.toFixed(2)),
      clv_total: Number(metrics.clv_total.toFixed(2)),
      clientes_count: metrics.count,
      churn_medio: metrics.count > 0 ? Number((metrics.churn_sum / metrics.count).toFixed(4)) : 0,
    };
  });

  // Ordena por VaR descendente
  persona_var.sort((a, b) => b.var_total - a.var_total);

  const charts: PortfolioCharts = {
    histogram,
    lorenz_curve,
    persona_var,
    gini: summary.gini,
    p80_clv_share: summary.pareto_80_20_clv_pct,
  };

  cache.portfolioCharts = charts;
  return charts;
}

async function ensureKanbanBasePrecomputed(): Promise<{
  top150: AgentRecommendation[];
  top150Set: Set<string>;
  customersById: Map<string, CustomerScore>;
}> {
  if (cache.top150Recommendations && cache.top150CustomerIdsSet && cache.customersById) {
    return {
      top150: cache.top150Recommendations,
      top150Set: cache.top150CustomerIdsSet,
      customersById: cache.customersById,
    };
  }

  const [_, recommendations] = await Promise.all([
    getCustomersScores(),
    getAgentRecommendations(),
  ]);

  const customersById = cache.customersById!;
  const top150 = [...recommendations]
    .sort((a, b) => {
      const cA = customersById.get(a.customer_id.trim().toUpperCase());
      const cB = customersById.get(b.customer_id.trim().toUpperCase());
      return (cB?.valor_em_risco || 0) - (cA?.valor_em_risco || 0);
    })
    .slice(0, 150);

  const top150Set = new Set<string>();
  for (const r of top150) {
    top150Set.add(r.customer_id.trim().toUpperCase());
  }

  cache.top150Recommendations = top150;
  cache.top150CustomerIdsSet = top150Set;

  return { top150, top150Set, customersById };
}

/**
 * Retorna o estado do Kanban Board de Retenção consolidando dados do agente e decisões do operador.
 * Otimizado: base Top 150 pré-calculada uma única vez; apenas decisões dinâmicas são re-aplicadas por requisição.
 */
export async function getKanbanBoard(targetCustomerId?: string): Promise<KanbanBoardState> {
  const [{ top150, top150Set, customersById }, recorded] = await Promise.all([
    ensureKanbanBasePrecomputed(),
    getRecordedDecisions(),
  ]);

  let priorityRecs = top150;

  // Se um cliente alvo for solicitado via deep link e não estiver no Top 150, inclui sua recomendação se existir
  if (targetCustomerId) {
    const cleanTarget = targetCustomerId.trim().toUpperCase();
    if (!top150Set.has(cleanTarget)) {
      const targetRec = cache.recommendationsById?.get(cleanTarget);
      if (targetRec) {
        priorityRecs = [...top150, targetRec];
      }
    }
  }

  // Mapa de status e decisão mais recente por customer_id (B6)
  const statusMap = new Map<string, DecisionStatus>();
  const decisionMap = new Map<string, DecisionRecord>();
  for (const d of recorded.decisions) {
    const cleanId = d.customer_id.trim().toUpperCase();
    if (!statusMap.has(cleanId)) {
      statusMap.set(cleanId, d.status as DecisionStatus);
      decisionMap.set(cleanId, d);
    }
  }

  const columns: Record<DecisionStatus, any[]> = {
    suggested: [],
    in_review: [],
    approved: [],
    edited: [],
    dispatched: [],
    completed: [],
    rejected: [],
  };

  for (const rec of priorityRecs) {
    const cleanRecId = rec.customer_id.trim().toUpperCase();
    const cust = customersById.get(cleanRecId);
    if (!cust) continue;

    const latestDecision = decisionMap.get(cleanRecId);

    // Determina o status: se houver decisão gravada, usa ela. Senão, se human_review for true, vai para in_review; caso contrário, suggested.
    const status: DecisionStatus =
      statusMap.get(cleanRecId) || (rec.human_review ? 'in_review' : 'suggested');

    // Se houver decisão registrada com edição humana (edited: true), preserva a mensagem editada no F5 (B6)
    const effectiveMessage =
      latestDecision?.edited && latestDecision.final_message
        ? latestDecision.final_message
        : rec.message;

    const card = {
      customer_id: rec.customer_id,
      tier: cust.tier,
      persona: cust.persona,
      valor_em_risco: cust.valor_em_risco,
      clv_12m_previsto: cust.clv_12m_previsto,
      churn_prob: cust.churn_prob,
      action_id: rec.action_id,
      action_name: rec.action_name,
      channel: rec.channel,
      message: effectiveMessage,
      human_review: rec.human_review,
      status,
      has_citations: rec.citations.length > 0,
      updated_at: latestDecision?.timestamp || rec.recommended_at,
    };

    if (columns[status]) {
      columns[status].push(card);
    } else {
      columns.suggested.push(card);
    }
  }

  return {
    columns,
    total_cards: priorityRecs.length,
  };
}
