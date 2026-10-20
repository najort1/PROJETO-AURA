import assert from 'node:assert/strict';
import { GET as getPortfolioSummary } from '../src/app/api/portfolio/summary/route.ts';
import { GET as getPortfolioCharts } from '../src/app/api/portfolio/charts/route.ts';
import { GET as getPersonas } from '../src/app/api/personas/route.ts';
import { GET as getCustomers } from '../src/app/api/customers/route.ts';
import { GET as getCustomerById } from '../src/app/api/customers/[id]/route.ts';
import { GET as getTimeline } from '../src/app/api/customer-timeline/route.ts';
import { GET as getAgentRecs } from '../src/app/api/agent/recommendations/route.ts';
import { GET as getAgentRecById } from '../src/app/api/agent/recommendations/[id]/route.ts';
import { GET as getKanban } from '../src/app/api/agent/kanban/route.ts';
import { GET as getClvShapById } from '../src/app/api/clv-shap/[id]/route.ts';
import { GET as getFriction } from '../src/app/api/friction/route.ts';
import { GET as getFairness } from '../src/app/api/fairness/route.ts';
import { GET as getDecisions, POST as postDecisions } from '../src/app/api/decisions/route.ts';
import { POST as postSimulate } from '../src/app/api/simulator/calculate/route.ts';
import { GET as getHealth } from '../src/app/api/health/route.ts';

function createMockRequest(url, method = 'GET', body = null) {
  return {
    url,
    method,
    json: async () => body,
  };
}

async function runRouteTests() {
  console.log('🚀 Iniciando testes de integração de todos os API Route Handlers...');

  // 1. Health
  console.log('\n--- Teste: GET /api/health ---');
  const resHealth = await getHealth();
  const dataHealth = await resHealth.json();
  assert.equal(dataHealth.status, 'healthy');
  console.log('✅ /api/health OK');

  // 2. Portfolio Summary
  console.log('\n--- Teste: GET /api/portfolio/summary ---');
  const resSummary = await getPortfolioSummary();
  const dataSummary = await resSummary.json();
  assert.equal(dataSummary.total_customers, 50000);
  assert.equal(dataSummary.clv_total, 39554463.12);
  assert.equal(dataSummary.alto_valor_count, 5005);
  console.log('✅ /api/portfolio/summary OK');

  // 3. Portfolio Charts
  console.log('\n--- Teste: GET /api/portfolio/charts ---');
  const resCharts = await getPortfolioCharts();
  const dataCharts = await resCharts.json();
  assert.ok(dataCharts.histogram.length > 0);
  assert.ok(dataCharts.lorenz_curve.length > 50);
  assert.equal(dataCharts.persona_var.length, 6);
  console.log('✅ /api/portfolio/charts OK');

  // 4. Personas
  console.log('\n--- Teste: GET /api/personas ---');
  const resPersonas = await getPersonas();
  const dataPersonas = await resPersonas.json();
  assert.equal(dataPersonas.length, 6);
  console.log('✅ /api/personas OK');

  // 5. Customers (Busca paginada, ordenação e filtros)
  console.log('\n--- Teste: GET /api/customers?page=1&page_size=10&tier=diamante&sort_by=clv_12m_previsto&sort_order=desc ---');
  const reqCust = createMockRequest('http://localhost:3000/api/customers?page=1&page_size=10&tier=diamante&sort_by=clv_12m_previsto&sort_order=desc');
  const resCust = await getCustomers(reqCust);
  const dataCust = await resCust.json();
  assert.equal(dataCust.page, 1);
  assert.equal(dataCust.page_size, 10);
  assert.equal(dataCust.data.length, 10);
  assert.ok(dataCust.data.every(c => c.tier.toLowerCase() === 'diamante'));
  assert.ok(dataCust.data[0].clv_12m_previsto >= dataCust.data[1].clv_12m_previsto);
  console.log(`✅ /api/customers OK (Total encontrados para filtro: ${dataCust.total})`);

  // 6. Customer 360 [ID]
  console.log('\n--- Teste: GET /api/customers/C038454 ---');
  const resCustId = await getCustomerById(createMockRequest('http://localhost:3000/api/customers/C038454'), {
    params: Promise.resolve({ id: 'C038454' }),
  });
  const dataCustId = await resCustId.json();
  assert.equal(dataCustId.customer.customer_id, 'C038454');
  assert.ok(dataCustId.shap_factors.length === 3, 'Top 3 fatores SHAP');
  assert.ok(dataCustId.timeline.length > 0, 'Timeline do cliente');
  assert.ok(dataCustId.timeline.every(ev => ev.data <= '2025-08-31'), 'Guardrail temporal verificado');
  console.log('✅ /api/customers/[id] OK (Fatores SHAP traduzidos e Timeline)');

  // 7. Timeline
  console.log('\n--- Teste: GET /api/customer-timeline?customer_id=C038454 ---');
  const resTimeline = await getTimeline(createMockRequest('http://localhost:3000/api/customer-timeline?customer_id=C038454'));
  const dataTimeline = await resTimeline.json();
  assert.equal(dataTimeline.temporal_cutoff, '2025-08-31');
  assert.ok(dataTimeline.data.every(ev => ev.customer_id === 'C038454'));
  console.log('✅ /api/customer-timeline OK');

  // 8. Recomendações
  console.log('\n--- Teste: GET /api/agent/recommendations/C000005 ---');
  const resRec = await getAgentRecById(createMockRequest('http://localhost:3000/api/agent/recommendations/C000005'), {
    params: Promise.resolve({ id: 'C000005' }),
  });
  const dataRec = await resRec.json();
  assert.equal(dataRec.customer_id, 'C000005');
  assert.ok(dataRec.has_citations);
  assert.ok(dataRec.citations.length > 0);
  console.log('✅ /api/agent/recommendations/[id] OK (Citações regulatórias)');

  // 9. Kanban Board
  console.log('\n--- Teste: GET /api/agent/kanban ---');
  const resKanban = await getKanban(createMockRequest('http://localhost:3000/api/agent/kanban'));
  const dataKanban = await resKanban.json();
  assert.ok(dataKanban.total_cards > 0);
  console.log('✅ /api/agent/kanban OK');

  // 10. CLV SHAP [ID]
  console.log('\n--- Teste: GET /api/clv-shap/C038454 ---');
  const resShap = await getClvShapById(createMockRequest('http://localhost:3000/api/clv-shap/C038454'), {
    params: Promise.resolve({ id: 'C038454' }),
  });
  const dataShap = await resShap.json();
  assert.equal(dataShap.customer_id, 'C038454');
  assert.equal(dataShap.shap_top3.length, 3);
  console.log('✅ /api/clv-shap/[id] OK');

  // 11. Friction
  console.log('\n--- Teste: GET /api/friction ---');
  const resFriction = await getFriction();
  const dataFriction = await resFriction.json();
  assert.equal(dataFriction.count, 49);
  assert.ok(dataFriction.methodology_declaration.includes('CORPUS SINTÉTICO'));
  console.log('✅ /api/friction OK');

  // 12. Fairness (IA Responsável)
  console.log('\n--- Teste: GET /api/fairness ---');
  const resFairness = await getFairness();
  const dataFairness = await resFairness.json();
  assert.equal(dataFairness.count, 16);
  assert.equal(dataFairness.compliance_summary.non_compliant_groups, 5);
  console.log('✅ /api/fairness OK');

  // 13. Simulator Calculate (Cenário Base da Spec)
  console.log('\n--- Teste: POST /api/simulator/calculate (Cenário Base) ---');
  const reqSim = createMockRequest('http://localhost:3000/api/simulator/calculate', 'POST', {
    orcamento: 80000.0,
    custo_acao: 45.0,
    taxa_resposta: 0.18,
    efeito_acao: 0.25,
    margem: 0.22,
  });
  const resSim = await postSimulate(reqSim);
  const dataSim = await resSim.json();
  assert.equal(dataSim.clientes_abordados, 1777, '1.777 clientes abordados no cenário base');
  assert.equal(dataSim.custo_total, 79965.0, 'Custo total R$ 79.965,00');
  assert.ok(Math.abs(dataSim.evasoes_evitadas - 26.0) < 1.0, 'Evasões evitadas em torno de 26');
  console.log(`✅ /api/simulator/calculate OK: ${dataSim.clientes_abordados} clientes, R$ ${dataSim.delta_receita_liquida} delta líq, ROI ${dataSim.roi_pct}%`);

  // 14. Decisions (GET e POST)
  console.log('\n--- Teste: POST /api/decisions e GET /api/decisions ---');
  const reqDec = createMockRequest('http://localhost:3000/api/decisions', 'POST', {
    customer_id: 'C019283',
    action_id: 'ACT-CONTATO',
    action_name: 'contato_proativo',
    status: 'in_review',
    operator: 'auditor_senior',
    original_message: 'Oferta padrão de retenção.',
    final_message: 'Oferta personalizada com bonificação de 5.000 pontos.',
    notes: 'Ajuste de bônus pelo analista sênior',
  });
  const resPostDec = await postDecisions(reqDec);
  assert.equal(resPostDec.status, 201);
  const dataPostDec = await resPostDec.json();
  assert.ok(dataPostDec.record.hash_signature);

  const resGetDec = await getDecisions(createMockRequest('http://localhost:3000/api/decisions?customer_id=C019283'));
  const dataGetDec = await resGetDec.json();
  assert.ok(dataGetDec.data.length >= 1);
  assert.equal(dataGetDec.data[0].customer_id, 'C019283');
  console.log('✅ POST e GET /api/decisions OK (Dual-write e consulta com hash)');

  console.log('\n🎉 TODOS OS 14 ENDPOINTS DE API VALIDARAM COM 100% DE SUCESSO!\n');
}

runRouteTests().catch((err) => {
  console.error('❌ Falha nos testes de rotas:', err);
  process.exit(1);
});
