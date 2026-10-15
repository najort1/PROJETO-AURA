import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

// Testa imports das funções da camada de dados
import {
  getCustomersScores,
  getPersonasSummary,
  getCustomerTimeline,
  getAgentRecommendations,
  getClvShap,
  getFrictionMap,
  getFairnessMetrics,
  getPortfolioSummary,
  getPortfolioCharts,
  getKanbanBoard,
} from '../src/lib/data/reader.ts';

import {
  recordDecision,
  getRecordedDecisions,
} from '../src/lib/data/decisions.ts';

import { translateShapFeature } from '../src/lib/data/shap-translations.ts';

async function runTests() {
  console.log('🚀 Iniciando bateria de testes de integração da Camada de Dados...');

  // 1. Teste de Customers Scores
  console.log('\n--- 1. Teste: Ingestão de customers_scores (50.000 clientes) ---');
  const customers = await getCustomersScores();
  assert.equal(customers.length, 50000, 'A base de clientes deve conter exatamente 50.000 registros');
  const firstCustomer = customers[0];
  assert.ok(firstCustomer.customer_id, 'Cliente deve possuir customer_id');
  assert.ok(['azul', 'topazio', 'safira', 'diamante', 'unique'].includes(firstCustomer.tier), 'Tier válido');
  assert.equal(typeof firstCustomer.clv_12m_previsto, 'number', 'clv_12m_previsto deve ser number');
  assert.equal(typeof firstCustomer.churn_prob, 'number', 'churn_prob deve ser number');
  console.log('✅ Ingestão de 50.000 clientes validada com sucesso.');

  // 2. Teste de Personas Summary
  console.log('\n--- 2. Teste: Ingestão das 6 Personas ---');
  const personas = await getPersonasSummary();
  assert.equal(personas.length, 6, 'Devem existir exatamente 6 personas comportamentais');
  const personaCounts = Object.fromEntries(personas.map(p => [p.persona, p.clientes_count]));
  assert.equal(personaCounts['executivo_recorrente'], 1310, 'Executivo Recorrente: 1.310');
  assert.equal(personaCounts['lazer_premium'], 4647, 'Lazer Premium: 4.647');
  assert.equal(personaCounts['maximizador_milhas'], 4948, 'Maximizador de Milhas: 4.948');
  assert.equal(personaCounts['regional_dependente'], 9766, 'Regional Dependente: 9.766');
  assert.equal(personaCounts['eventual_ascendente'], 5122, 'Eventual Ascendente: 5.122');
  assert.equal(personaCounts['eventual_promocional'], 24207, 'Eventual Promocional: 24.207');
  console.log('✅ Contagens exatas das 6 personas validadas com sucesso.');

  // 3. Teste de Timeline e Guardrail Temporal
  console.log('\n--- 3. Teste: Timeline e Guardrail Temporal (<= 2025-08-31) ---');
  const timelineAll = await getCustomerTimeline();
  assert.ok(timelineAll.length > 0, 'Timeline deve conter registros');
  const leaks = timelineAll.filter(ev => ev.data > '2025-08-31');
  assert.equal(leaks.length, 0, 'ZERO eventos após 2025-08-31 (Anti-Data Leakage confirmado)');
  const timelineC038454 = await getCustomerTimeline('C038454');
  assert.ok(timelineC038454.length > 0, 'C038454 deve ter eventos na timeline');
  console.log(`✅ Guardrail temporal verificado: ${timelineAll.length} eventos no histórico, 0 após o corte.`);

  // 4. Teste de KPIs da Carteira e Lorenz / Gini
  console.log('\n--- 4. Teste: KPIs de Portfolio e Lorenz/Gini ---');
  const summary = await getPortfolioSummary();
  assert.equal(summary.total_customers, 50000, 'Total de clientes');
  assert.equal(summary.clv_total, 39554463.12, 'CLV Total R$ 39.554.463,12');
  assert.equal(summary.alto_valor_count, 5005, 'Alto Valor Count: 5.005');
  assert.equal(summary.alto_valor_pct, 0.1001, 'Alto Valor Pct: 10,01%');
  assert.equal(summary.custo_medio_acao, 45.0, 'Custo Médio da Ação [Premissa]');
  console.log(`✅ KPIs validados: CLV Total R$ ${summary.clv_total.toLocaleString('pt-BR')}, VaR Total R$ ${summary.var_total.toLocaleString('pt-BR')}, Gini ${summary.gini}.`);

  const charts = await getPortfolioCharts();
  assert.ok(charts.histogram.length > 0, 'Histograma gerado');
  assert.ok(charts.lorenz_curve.length > 50, 'Curva de Lorenz gerada');
  assert.equal(charts.persona_var.length, 6, 'VaR por Persona gerado para as 6 personas');
  console.log('✅ Séries gráficas calculadas com sucesso.');

  // 5. Teste de Explicabilidade SHAP e Tradução Humanizada
  console.log('\n--- 5. Teste: Explicabilidade SHAP ---');
  const shapList = await getClvShap();
  assert.equal(shapList.length, 50000, '50.000 registros SHAP');
  const shapC038454 = shapList.find(s => s.customer_id === 'C038454');
  assert.ok(shapC038454, 'C038454 encontrado em clv_shap');
  assert.equal(translateShapFeature('tier_encoded'), 'Nível / Categoria (Tier)');
  assert.equal(translateShapFeature('ticket_medio_12m'), 'Ticket Médio por Voo');
  assert.equal(translateShapFeature('pontos_qualificaveis_12m'), 'Pontos Qualificáveis Acumulados');
  console.log('✅ Fatores SHAP e traduções humanizadas validadas.');

  // 6. Teste de Recomendações e Citações RAG
  console.log('\n--- 6. Teste: Recomendações do Agente e Citações ---');
  const recs = await getAgentRecommendations();
  assert.equal(recs.length, 50000, '50.000 recomendações geradas');
  const recC000005 = recs.find(r => r.customer_id === 'C000005');
  assert.ok(recC000005, 'C000005 encontrado');
  assert.ok(recC000005.citations.length > 0, 'C000005 possui citações');
  assert.ok(recC000005.citations[0].fact_id, 'Citação possui fact_id');
  console.log('✅ Recomendações e citações do regulamento auditadas.');

  // 7. Teste de Friction Map e Pesos Calibrados
  console.log('\n--- 7. Teste: Mapa de Atritos (49 registros) ---');
  const friction = await getFrictionMap();
  assert.equal(friction.length, 49, '7 aspectos x 7 semestres = 49 registros');
  console.log('✅ Mapa de atritos validado.');

  // 8. Teste de Fairness Metrics (16 grupos)
  console.log('\n--- 8. Teste: IA Responsável / Regra 4/5 (16 grupos) ---');
  const fairness = await getFairnessMetrics();
  assert.equal(fairness.length, 16, '16 grupos demográficos');
  const nonCompliant = fairness.filter(f => !f.four_fifths_compliant && f.group_value !== 'Não informado');
  assert.equal(nonCompliant.length, 5, 'Exatamente 5 grupos não conformes');
  console.log('✅ Auditoria de disparidade 4/5 validada.');

  // 9. Teste de Gravação e Persistência de Decisões (Dual-Write & Fail Loud)
  console.log('\n--- 9. Teste: Persistência Atômica de Decisões (decisions.jsonl) ---');
  const testCustomer = 'C038454';
  const testAction = 'ACT-TEST-PERSISTENCE';
  const testOriginalMsg = 'Mensagem original sugerida pelo agente.';
  const testFinalMsg = 'Mensagem editada e homologada pelo operador humano.';

  const decisionResult = await recordDecision({
    customer_id: testCustomer,
    action_id: testAction,
    action_name: 'teste_integracao',
    status: 'approved',
    operator: 'engenheiro_dados_test',
    original_message: testOriginalMsg,
    final_message: testFinalMsg,
    edited: true,
    notes: 'Validação de dual-write atômico da task-2',
  });

  assert.equal(decisionResult.customer_id, testCustomer);
  assert.equal(decisionResult.status, 'approved');
  assert.equal(decisionResult.edited, true);
  assert.ok(decisionResult.timestamp, 'Timestamp ISO preenchido');
  assert.ok(decisionResult.hash_signature, 'Assinatura SHA-256 gerada para integridade imutável');

  // Leitura do arquivo decisions.jsonl
  const history = await getRecordedDecisions(testCustomer);
  assert.ok(history.decisions.length >= 1, 'Decisão gravada deve constar no histórico');
  const lastRecorded = history.decisions[0];
  assert.equal(lastRecorded.customer_id, testCustomer);
  assert.equal(lastRecorded.action_id, testAction);
  assert.equal(lastRecorded.final_message, testFinalMsg);
  console.log(`✅ Decisão registrada com hash SHA-256: ${lastRecorded.hash_signature.slice(0, 16)}...`);

  // 10. Teste do Kanban Board
  console.log('\n--- 10. Teste: Kanban Board Agente CRM ---');
  const kanban = await getKanbanBoard();
  assert.ok(kanban.total_cards > 0, 'Total de cards no Kanban');
  assert.ok(Array.isArray(kanban.columns.suggested), 'Coluna suggested existe');
  assert.ok(Array.isArray(kanban.columns.in_review), 'Coluna in_review existe');
  assert.ok(Array.isArray(kanban.columns.approved), 'Coluna approved existe');
  console.log(`✅ Kanban montado com ${kanban.total_cards} cards distribuídos.`);

  console.log('\n🎉 TODOS OS 10 TESTES DE INTEGRAÇÃO PASSARAM COM 100% DE SUCESSO!\n');
}

runTests().catch((err) => {
  console.error('❌ Falha nos testes:', err);
  process.exit(1);
});
