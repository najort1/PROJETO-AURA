export type GlossaryTermKey =
  | 'clv'
  | 'var'
  | 'churn'
  | 'score_av'
  | 'shap'
  | 'personas'
  | 'regra_4_5'
  | 'hitl'
  | 'art_20_lgpd'
  | 'nba'
  | 'gini'
  | 'lorenz';

export interface GlossaryTerm {
  key: GlossaryTermKey;
  title: string;
  category: string;
  shortDefinition: string;
  details: string;
  formula?: string;
  link?: string;
}

export const GLOSSARY: Record<GlossaryTermKey, GlossaryTerm> = {
  clv: {
    key: 'clv',
    title: 'Customer Lifetime Value (CLV 12M)',
    category: 'Métricas Financeiras',
    shortDefinition:
      'Estimativa do valor financeiro líquido que o cliente gerará para a Azul nos próximos 12 meses.',
    details:
      'Calculado a partir de modelos preditivos calibrados que combinam histórico de gastos, frequência de voos, acúmulo de pontos qualificáveis e propensão a compras auxiliares.',
    formula: 'CLV_12M = Σ (Receita_t - Custo_t) / (1 + d)^t',
    link: '/carteira',
  },
  var: {
    key: 'var',
    title: 'Valor em Risco (VaR Total)',
    category: 'Gestão de Risco',
    shortDefinition:
      'Montante financeiro de receita em risco de perda caso o cliente efetive a evasão do programa.',
    details:
      'Produto direto entre o CLV previsto para os próximos 12 meses e a probabilidade estimada de evasão (Churn). Mede a exposição monetária da carteira e prioriza a alocação de orçamento de retenção.',
    formula: 'VaR_i = CLV_12M_i × Prob_Churn_i',
    link: '/carteira',
  },
  churn: {
    key: 'churn',
    title: 'Probabilidade de Evasão (Churn)',
    category: 'Modelagem Preditiva',
    shortDefinition:
      'Probabilidade calibrada de um cliente encerrar ou reduzir drasticamente suas atividades no programa nos próximos 12 meses.',
    details:
      'Predito através de algoritmo LightGBM com hiperparâmetros calibrados e validação temporal estrita, avaliando recência de voos, queda no acúmulo de pontos e registros de atritos operacionais.',
    formula: 'P(Churn = 1 | X) = 1 / (1 + e^-z)',
    link: '/cliente-360',
  },
  score_av: {
    key: 'score_av',
    title: 'Score de Alto Valor (ScoreAV)',
    category: 'Segmentação & Priorização',
    shortDefinition:
      'Indicador unificado de relevância estratégica do cliente combinando receita histórica, tier e potencial futuro.',
    details:
      'Clientes com ScoreAV acima do percentil 90 (P90) são classificados automaticamente no Segmento de Alto Valor, recebendo tratamento prioritário e salvaguardas adicionais na esteira de decisões.',
    formula: 'ScoreAV = w_1 × Gasto_Norm + w_2 × Tier_Rank + w_3 × CLV_Norm',
    link: '/cliente-360',
  },
  shap: {
    key: 'shap',
    title: 'Explicabilidade SHAP (SHapley Additive exPlanations)',
    category: 'IA Explicável (XAI)',
    shortDefinition:
      'Método baseado na teoria dos jogos cooperativos que decompõe a contribuição individual de cada variável na predição final do modelo.',
    details:
      'Permite auditar por que um cliente específico recebeu determinado valor de CLV ou risco de churn, identificando os 3 principais fatores de alavancagem positiva ou negativa de forma transparente.',
    formula: 'f(x) = E[f(x)] + Σ φ_i(x)',
    link: '/cliente-360',
  },
  personas: {
    key: 'personas',
    title: 'Personas e Segmentação Comportamental',
    category: 'Comportamento & CRM',
    shortDefinition:
      'Agrupamento analítico em 6 arquétipos com base em padrões de viagem, sensibilidade a preço e engajamento com o programa.',
    details:
      'Segmenta os 50.000 clientes em: Executivo Recorrente, Lazer Premium, Maximizador de Milhas, Regional Dependente, Eventual Ascendente e Eventual Promocional, orientando playbooks de intervenção customizados.',
    link: '/personas',
  },
  regra_4_5: {
    key: 'regra_4_5',
    title: 'Regra dos Quatro Quintos (Four-Fifths Rule)',
    category: 'IA Responsável & Ética',
    shortDefinition:
      'Diretriz regulatória da EEOC (29 CFR § 1607.4) para aferir impacto adverso desproporcional em grupos protegidos.',
    details:
      'Exige que a taxa de seleção de qualquer grupo demográfico sensível (gênero, faixa etária, região) seja de no mínimo 80% (4/5) da taxa do grupo de maior seleção. Razões abaixo de 0,80 disparam alerta de disparidade para mitigação.',
    formula: 'Selection Ratio = Taxa_Seleção(Grupo) / Taxa_Seleção(Grupo_Referência) ≥ 0,80',
    link: '/ia-responsavel',
  },
  hitl: {
    key: 'hitl',
    title: 'Human-in-the-Loop (Revisão Humana Mandatória)',
    category: 'Governança & Compliance',
    shortDefinition:
      'Protocolo operacional em que intervenções automatizadas críticas requerem validação e assinatura explícita de um analista humano antes do disparo.',
    details:
      'Obrigatório para clientes de Alto Valor (ScoreAV P90), propostas com custo elevado ou em situações de atrito crítico, garantindo conformidade com o Artigo 20 da LGPD e prevenindo disparos indevidos.',
    link: '/agente',
  },
  art_20_lgpd: {
    key: 'art_20_lgpd',
    title: 'Artigo 20 da LGPD (Decisões Automatizadas)',
    category: 'Governança & Compliance',
    shortDefinition:
      'Dispositivo legal (Lei nº 13.709/2018) que assegura ao titular o direito de solicitar revisão e explicação de decisões tomadas unicamente com base em tratamento automatizado.',
    details:
      'Implementado no Aura através da trilha imutável append-only (decisions.jsonl), explicabilidade local com SHAP waterfall e obrigatoriedade de revisão humana em perfis de risco.',
    link: '/ia-responsavel',
  },
  nba: {
    key: 'nba',
    title: 'Next Best Action (Melhor Ação Recomendada)',
    category: 'Agente & Retenção',
    shortDefinition:
      'Recomendação prescritiva otimizada pelo agente de IA indicando o melhor canal, oferta e momento para intervenção com o cliente.',
    details:
      'Cada ação gerada possui ID rastreável, probabilidade de aceitação calculada, canal ótimo (WhatsApp, e-mail, push, telefone), cálculo de custo unitário e verificação factual ancorada nas regras do programa (RAG Fact-Checking).',
    link: '/agente',
  },
  gini: {
    key: 'gini',
    title: 'Coeficiente de Gini (Concentração de Receita)',
    category: 'Métricas Financeiras & Desigualdade',
    shortDefinition:
      'Medida estatística de assimetria e concentração da receita de CLV entre os clientes da carteira (varia de 0 a 1).',
    details:
      'Um índice de 0 representa perfeita igualdade distributiva (cada cliente contribui identicamente para o CLV), enquanto 1 indica concentração máxima em um único cliente. Calculado numericamente pela área entre a reta de 45° e a Curva de Lorenz via regra do trapézio.',
    formula: 'Gini = 1 - 2 × ∫_0^1 L(p) dp = 1 - 2 × Área(Lorenz)',
    link: '/carteira',
  },
  lorenz: {
    key: 'lorenz',
    title: 'Curva de Lorenz (Curva de Pareto da Carteira)',
    category: 'Distribuição & Concentração',
    shortDefinition:
      'Representação gráfica da fração acumulada de receita de CLV em função do percentil acumulado de clientes.',
    details:
      'Ordena os clientes do menor ao maior CLV para evidenciar a assimetria da carteira. Permite visualizar diretamente o princípio de Pareto (onde o Top 20% mais valioso concentra a vasta maioria do valor gerado).',
    formula: 'L(p) = (∫_0^p Q(t) dt) / (∫_0^1 Q(t) dt)',
    link: '/carteira',
  },
};

export function getGlossaryTerm(key: GlossaryTermKey): GlossaryTerm | undefined {
  return GLOSSARY[key];
}
