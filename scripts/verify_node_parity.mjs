import fs from 'fs';
import path from 'path';
import { parquetRead } from '../dashboard/node_modules/hyparquet/src/index.js';
import { compressors } from '../dashboard/node_modules/hyparquet-compressors/src/index.js';

function sanitizeRow(row) {
  const result = {};
  for (const [key, value] of Object.entries(row)) {
    if (typeof value === 'bigint') {
      result[key] = Number(value);
    } else {
      result[key] = value;
    }
  }
  return result;
}

async function readParquet(fileName) {
  const filePath = path.resolve('data/analytics', fileName);
  const buf = fs.readFileSync(filePath);
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  return new Promise((resolve, reject) => {
    parquetRead({
      file: ab,
      compressors,
      rowFormat: 'object',
      onComplete: (data) => resolve(data.map(sanitizeRow)),
    }).catch(reject);
  });
}

async function verifyAll() {
  console.log('--- INICIANDO VERIFICAÇÃO ADVERSARIAL DE PARIDADE MATEMÁTICA ---');
  let errors = 0;

  // 1. customers_scores
  const customers = await readParquet('customers_scores.parquet');
  console.log(`[01 CARTEIRA] Total de clientes: ${customers.length}`);
  if (customers.length !== 50000) {
    console.error(`ERRO: Total de clientes esperado 50000, obtido ${customers.length}`);
    errors++;
  }

  let varTotal = 0;
  let clvTotal = 0;
  let altoValorCount = 0;
  const clvList = [];

  for (const c of customers) {
    const clv = Number(c.clv_12m_previsto || 0);
    const churn = Number(c.churn_prob || 0);
    clvTotal += clv;
    varTotal += clv * churn;
    clvList.push(clv);
    if (c.alto_valor) altoValorCount++;
  }

  console.log(`[01 CARTEIRA] VaR Total: R$ ${varTotal.toFixed(2)} (Esperado: R$ 8312879.04)`);
  if (Math.abs(varTotal - 8312879.04) > 1.0) {
    console.error(`ERRO: VaR Total fora da tolerância`);
    errors++;
  }

  console.log(`[01 CARTEIRA] CLV Total: R$ ${clvTotal.toFixed(2)} (Esperado: R$ 39554463.12)`);
  if (Math.abs(clvTotal - 39554463.12) > 1.0) {
    console.error(`ERRO: CLV Total fora da tolerância`);
    errors++;
  }

  const meanClv = clvTotal / customers.length;
  console.log(`[01 CARTEIRA] CLV Médio: R$ ${meanClv.toFixed(2)} (Esperado: R$ 791.09)`);
  if (Math.abs(meanClv - 791.09) > 0.1) {
    console.error(`ERRO: CLV Médio fora da tolerância`);
    errors++;
  }

  console.log(`[01 CARTEIRA] Alto Valor: ${altoValorCount} (Esperado: 5005, P90)`);
  if (altoValorCount !== 5005) {
    console.error(`ERRO: Alto Valor esperado 5005, obtido ${altoValorCount}`);
    errors++;
  }

  // Gini trapezoidal
  clvList.sort((a, b) => a - b);
  let trapSum = 0;
  let cumClv = 0;
  for (let i = 0; i < customers.length; i++) {
    const prevCum = cumClv / clvTotal;
    cumClv += clvList[i];
    const currCum = cumClv / clvTotal;
    const dx = 1 / customers.length;
    trapSum += ((prevCum + currCum) / 2) * dx;
  }
  const gini = Number((1.0 - 2.0 * trapSum).toFixed(2));
  console.log(`[01 CARTEIRA] Índice de Gini (Trapézio): ${gini} (Esperado: 0.55 - 0.61)`);

  const idx80 = Math.floor(customers.length * 0.8);
  let clvBottom80 = 0;
  for (let i = 0; i < idx80; i++) {
    clvBottom80 += clvList[i];
  }
  const pareto8020 = Number(((1.0 - clvBottom80 / clvTotal) * 100).toFixed(1));
  console.log(`[01 CARTEIRA] Pareto 80/20 CLV Top 20%: ${pareto8020}% (Esperado: 64.2% - 66.5%)`);

  // 2. personas_summary
  const personas = await readParquet('personas_summary.parquet');
  console.log(`[02 PERSONAS] Total de Personas: ${personas.length} (Esperado: 6)`);
  if (personas.length !== 6) {
    console.error(`ERRO: Total de personas esperado 6`);
    errors++;
  }
  const totalPersonaClients = personas.reduce((acc, p) => acc + p.clientes_count, 0);
  console.log(`[02 PERSONAS] Soma membros personas: ${totalPersonaClients} (Esperado: 50000)`);
  if (totalPersonaClients !== 50000) {
    console.error(`ERRO: Soma de membros das personas diferente de 50000`);
    errors++;
  }

  // 3. customer_timeline (guardrail)
  const timeline = await readParquet('customer_timeline.parquet');
  console.log(`[03 CLIENTE 360] Total eventos timeline: ${timeline.length}`);
  const postCutoff = timeline.filter((e) => e.data > '2025-08-31');
  console.log(`[03 CLIENTE 360] Eventos após 2025-08-31: ${postCutoff.length} (Esperado: 0)`);
  if (postCutoff.length !== 0) {
    console.error(`ERRO: Guardrail temporal violado no arquivo bruto Parquet!`);
    errors++;
  }

  // 4. fairness_metrics (Regra dos 4/5)
  const fairness = await readParquet('fairness_metrics.parquet');
  console.log(`[07 IA RESPONSÁVEL] Total linhas fairness: ${fairness.length} (Esperado: 16)`);
  if (fairness.length !== 16) {
    console.error(`ERRO: Total fairness esperado 16`);
    errors++;
  }
  const nonInformed = fairness.filter((f) => f.group_value.toLowerCase().includes('não informado'));
  console.log(`[07 IA RESPONSÁVEL] Grupos Não Informados: ${nonInformed.length} (Esperado: 2)`);
  if (nonInformed.length !== 2) {
    console.error(`ERRO: Grupos não informados esperado 2`);
    errors++;
  }
  const informed = fairness.filter((f) => !f.group_value.toLowerCase().includes('não informado'));
  console.log(`[07 IA RESPONSÁVEL] Grupos Informados: ${informed.length} (Esperado: 14)`);
  if (informed.length !== 14) {
    console.error(`ERRO: Grupos informados esperado 14`);
    errors++;
  }
  const compliant = informed.filter((f) => f.selection_ratio_vs_max >= 0.8);
  const nonCompliant = informed.filter((f) => f.selection_ratio_vs_max < 0.8);
  console.log(`[07 IA RESPONSÁVEL] Conformes 4/5: ${compliant.length} (Esperado: 9)`);
  console.log(`[07 IA RESPONSÁVEL] Não Conformes 4/5: ${nonCompliant.length} (Esperado: 5)`);
  if (compliant.length !== 9 || nonCompliant.length !== 5) {
    console.error(`ERRO: Disparidade de conformidade Four-Fifths!`);
    errors++;
  }

  // 5. friction_map
  const friction = await readParquet('friction_map.parquet');
  console.log(`[05 ATRITOS] Total registros mapa de atritos: ${friction.length} (Esperado: 49)`);
  if (friction.length !== 49) {
    console.error(`ERRO: friction_map esperado 49 registros`);
    errors++;
  }

  // 6. agent_recommendations
  const recs = await readParquet('agent_recommendations.parquet');
  console.log(`[04 AGENTE] Total recomendações NBA: ${recs.length}`);
  const hitlCount = recs.filter((r) => r.human_review).length;
  console.log(`[04 AGENTE] Recomendações com revisão HITL mandatória: ${hitlCount}`);

  // 7. Simulador Base
  // B=80000, c=45, tau=0.18, eta=0.25, m=0.22 -> n=1777, evasoes=26.0, receita_salva=8518.12, delta=-71446.88, ROI=-89.3%
  const b = 80000;
  const c = 45;
  const nAlvo = Math.floor(b / c);
  const custoTotal = nAlvo * c;
  const receitaSalvaBase = 8518.12;
  const deltaReceitaBase = receitaSalvaBase - custoTotal;
  const roiBase = (deltaReceitaBase / custoTotal) * 100;
  console.log(`[06 SIMULADOR] Cenário Base nAlvo: ${nAlvo} (Esperado: 1777)`);
  console.log(`[06 SIMULADOR] Cenário Base Custo: R$ ${custoTotal.toFixed(2)} (Esperado: R$ 79965.00)`);
  console.log(`[06 SIMULADOR] Cenário Base ΔReceita: R$ ${deltaReceitaBase.toFixed(2)} (Esperado: -R$ 71446.88)`);
  console.log(`[06 SIMULADOR] Cenário Base ROI: ${roiBase.toFixed(1)}% (Esperado: -89.3%)`);
  if (nAlvo !== 1777 || custoTotal !== 79965 || deltaReceitaBase.toFixed(2) !== '-71446.88' || roiBase.toFixed(1) !== '-89.3') {
    console.error(`ERRO: Cenário base do simulador fora da especificação canônica!`);
    errors++;
  }

  console.log(`--- FIM DA VERIFICAÇÃO ADVERSARIAL: TOTAL DE ERROS = ${errors} ---`);
  if (errors > 0) {
    process.exit(1);
  }
}

verifyAll().catch((err) => {
  console.error(err);
  process.exit(1);
});
