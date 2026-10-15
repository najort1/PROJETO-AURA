export type TierLevel = 'azul' | 'topazio' | 'safira' | 'diamante' | 'unique';

export interface CustomerScore {
  customer_id: string;
  tier: TierLevel;
  persona: string;
  clv_12m_previsto: number;
  churn_prob: number;
  valor_em_risco: number;
  score_av: number;
  alto_valor: boolean;
  risk_state: string;
  gastos_12m_brl: number;
  recencia_dias: number;
  frequencia_voos: number;
  trechos_12m: number;
  saldo_pontos: number;
  pontos_expirando_30d: number;
  pontos_qualificaveis_12m: number;
  meta_proximo_nivel_pct: number;
  faixa_etaria: string;
  genero: string;
  regiao: string;
  rota_favorita: string;
  atritos_dominantes: string;
  beneficio_nao_utilizado: string | null;
  shap_top3: string;
}

export interface PersonaSummary {
  persona: string;
  nome_display: string;
  cor: string;
  clientes_count: number;
  share_pct: number;
  clv_medio: number;
  churn_medio: number;
  valor_em_risco_total: number;
  atritos_dominantes: string;
  acao_recomendada: string;
  descricao: string;
  ticket_medio: number;
}

export interface CustomerTimelineEvent {
  customer_id: string;
  data: string;
  tipo: 'voo' | 'atrito' | 'resgate' | 'tier' | string;
  titulo: string;
  detalhe: string;
  impacto: 'positivo' | 'negativo' | 'neutro' | string;
}

export interface ClvShapRecord {
  customer_id: string;
  shap_top3_json: string;
  top1_feature: string;
  top1_shap: number;
  top1_value: number;
  top2_feature: string;
  top2_shap: number;
  top2_value: number;
  top3_feature: string;
  top3_shap: number;
  top3_value: number;
}

export interface ShapFactorTranslated {
  raw_feature: string;
  human_label: string;
  shap_value: number;
  feature_value: number | string;
  impact_direction: 'positive' | 'negative';
}

export interface FrictionRecord {
  friction_id: string;
  aspect: string;
  semester: string;
  mention_count: number;
  negative_count: number;
  neutral_count: number;
  positive_count: number;
  negative_rate: number;
  semester_intensity: number;
  mean_intensity: number;
  delta_previous: number | null;
  trend_direction: string;
  aspect_weight: number;
}

export interface FairnessMetric {
  sensitive_attribute: string;
  group_value: string;
  group_size: number;
  alto_valor_count: number;
  selection_rate: number;
  avg_predicted_churn: number;
  selection_ratio_vs_max: number;
  four_fifths_compliant: boolean;
}

export interface PortfolioSummary {
  total_customers: number;
  var_total: number;
  clv_total: number;
  alto_valor_count: number;
  alto_valor_pct: number;
  custo_medio_acao: number;
  gini: number;
  pareto_80_20_clv_pct: number;
  media_clv: number;
  mediana_clv: number;
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  label: string;
  count: number;
  is_p95: boolean;
}

export interface LorenzPoint {
  p: number; // Fração da população (0 a 1)
  l_p: number; // Fração acumulada do CLV (0 a 1)
}

export interface PersonaVarBarItem {
  persona: string;
  nome_display: string;
  cor: string;
  var_total: number;
  clv_total: number;
  clientes_count: number;
  churn_medio: number;
}

export interface PortfolioCharts {
  histogram: HistogramBin[];
  lorenz_curve: LorenzPoint[];
  persona_var: PersonaVarBarItem[];
  gini: number;
  p80_clv_share: number;
}

export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
