import type { ShapFactorTranslated } from '../../types/analytics.ts';

export const SHAP_FEATURE_LABELS: Record<string, string> = {
  tier_encoded: 'Nível / Categoria (Tier)',
  ticket_medio_12m: 'Ticket Médio por Voo',
  pontos_qualificaveis_12m: 'Pontos Qualificáveis Acumulados',
  recency_days: 'Recência de Voo (Dias sem Voar)',
  avg_advance_booking_days: 'Antecedência de Compra de Passagens',
  frequency_trend: 'Tendência de Frequência de Voos',
  total_atritos_12m: 'Histórico de Atritos Operacionais',
  gastos_12m_brl: 'Gasto Total em Voos (12M)',
  frequencia_voos: 'Frequência Anual de Voos',
  saldo_pontos: 'Saldo de Pontos Acumulado',
  atrito_recente: 'Registro de Atrito Recente',
  cancelamentos_12m: 'Cancelamentos Sofridos (12M)',
  atrasos_12m: 'Atrasos Superiores a 30min',
  share_voos_tronco: 'Proporção de Voos em Rotas Principais',
};

export function translateShapFeature(rawFeature: string): string {
  if (SHAP_FEATURE_LABELS[rawFeature]) {
    return SHAP_FEATURE_LABELS[rawFeature];
  }
  // Normalização amigável de fallback
  return rawFeature
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatShapFactor(
  feature: string,
  shapValue: number,
  featureValue: number | string
): ShapFactorTranslated {
  return {
    raw_feature: feature,
    human_label: translateShapFeature(feature),
    shap_value: shapValue,
    feature_value: featureValue,
    impact_direction: shapValue >= 0 ? 'positive' : 'negative',
  };
}
