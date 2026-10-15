import assert from 'node:assert/strict';

const BASE_URL = 'http://localhost:3008';

async function testEndpoint(name, path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, options);
  assert.ok(res.ok, `Falha em ${name}: status ${res.status} ${res.statusText}`);
  const json = await res.json();
  console.log(`✅ [${res.status}] ${name} (${path})`);
  return json;
}

async function main() {
  console.log('🌐 Executando testes HTTP reais contra http://localhost:3008...\n');

  // 1. Health
  const health = await testEndpoint('Health Check', '/api/health');
  assert.equal(health.status, 'healthy');

  // 2. Portfolio Summary
  const summary = await testEndpoint('Portfolio Summary', '/api/portfolio/summary');
  assert.equal(summary.total_customers, 50000);
  assert.equal(summary.clv_total, 39554463.12);
  assert.equal(summary.alto_valor_count, 5005);
  assert.equal(summary.custo_medio_acao, 45.0);

  // 3. Portfolio Charts
  const charts = await testEndpoint('Portfolio Charts', '/api/portfolio/charts');
  assert.ok(charts.histogram.length > 0);
  assert.ok(charts.lorenz_curve.length > 50);
  assert.equal(charts.persona_var.length, 6);

  // 4. Personas
  const personas = await testEndpoint('Personas Summary', '/api/personas');
  assert.equal(personas.length, 6);

  // 5. Customers List (Paginada com filtros e ordenação)
  const custPage1 = await testEndpoint(
    'Customers List (Top VaR)',
    '/api/customers?page=1&page_size=5&sort_by=valor_em_risco&sort_order=desc'
  );
  assert.equal(custPage1.data.length, 5);
  assert.equal(custPage1.data[0].customer_id, 'C038454'); // Top 1 VaR
  assert.equal(custPage1.data[0].valor_em_risco, 3109.29);

  // 6. Customer 360 [ID]
  const cust360 = await testEndpoint('Customer 360 (C038454)', '/api/customers/C038454');
  assert.equal(cust360.customer.customer_id, 'C038454');
  assert.equal(cust360.shap_factors.length, 3);
  assert.ok(cust360.timeline.length > 0);
  assert.ok(cust360.timeline.every(ev => ev.data <= '2025-08-31'));

  // 7. Customer Timeline
  const timeline = await testEndpoint('Customer Timeline', '/api/customer-timeline?customer_id=C038454');
  assert.equal(timeline.temporal_cutoff, '2025-08-31');
  assert.ok(timeline.data.length > 0);

  // 8. Agent Recommendations
  const agentRec = await testEndpoint('Agent Recommendations', '/api/agent/recommendations/C000005');
  assert.equal(agentRec.customer_id, 'C000005');
  assert.ok(agentRec.citations.length > 0);

  // 9. Agent Kanban
  const kanban = await testEndpoint('Agent Kanban Board', '/api/agent/kanban');
  assert.ok(kanban.total_cards > 0);

  // 10. CLV SHAP
  const shap = await testEndpoint('CLV SHAP Waterfall Factors', '/api/clv-shap/C038454');
  assert.equal(shap.customer_id, 'C038454');
  assert.equal(shap.shap_top3.length, 3);

  // 11. Friction
  const friction = await testEndpoint('Friction Map', '/api/friction');
  assert.equal(friction.count, 49);
  assert.ok(friction.methodology_declaration.includes('CORPUS SINTÉTICO'));

  // 12. Fairness
  const fairness = await testEndpoint('Fairness Metrics', '/api/fairness');
  assert.equal(fairness.count, 16);
  assert.equal(fairness.compliance_summary.non_compliant_groups, 5);

  // 13. Simulator Calculate
  const sim = await testEndpoint('Simulator Calculate (Base Scenario)', '/api/simulator/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      orcamento: 80000.0,
      custo_acao: 45.0,
      taxa_resposta: 0.18,
      efeito_acao: 0.25,
      margem: 0.22,
    }),
  });
  assert.equal(sim.clientes_abordados, 1777);
  assert.equal(sim.custo_total, 79965.0);

  // 14. Decisions (POST e GET com dual-write)
  const decPost = await testEndpoint('Record Decision (POST)', '/api/decisions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      customer_id: 'C038454',
      action_id: 'ACT-ATRATRIBUI-ATRASO',
      action_name: 'reencaminhamento_atraso',
      status: 'approved',
      operator: 'operador_qa_live',
      original_message: 'Mensagem de teste original via HTTP.',
      final_message: 'Mensagem de teste homologada via HTTP com dual-write.',
      notes: 'Teste live end-to-end',
    }),
  });
  assert.ok(decPost.record.hash_signature);

  const decGet = await testEndpoint('Get Decisions History (GET)', '/api/decisions?customer_id=C038454');
  assert.ok(decGet.data.length >= 1);
  assert.equal(decGet.data[0].customer_id, 'C038454');

  console.log('\n🎯 SUCESSO TOTAL: TODOS OS 14 ENDPOINTS HTTP RESPONDERAM COM STATUS 200/201 E PARIDADE DE DADOS!\n');
}

main().catch((err) => {
  console.error('❌ Falha nos testes live:', err);
  process.exit(1);
});
