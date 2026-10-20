import { NextRequest, NextResponse } from 'next/server';
import { getSortedCustomersByVar } from '@/lib/data/reader';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const orcamento = Number(body.orcamento ?? 80000.0);
    const custoAcao = Number(body.custo_acao ?? 45.0);
    const taxaResp = Number(body.taxa_resposta ?? 0.18);
    const efeitoAcao = Number(body.efeito_acao ?? 0.25);
    const margem = Number(body.margem ?? 0.22);

    const sorted = await getSortedCustomersByVar();

    const nAlvo = Math.min(sorted.length, Math.floor(orcamento / Math.max(1, custoAcao)));
    const targetSlice = sorted.slice(0, nAlvo);

    let evasoesEvitadas = 0;
    let receitaSalva = 0;

    for (const c of targetSlice) {
      const churnProb = Number(c.churn_prob || 0);
      const clv = Number(c.clv_12m_previsto || 0);
      const pEvitada = churnProb * efeitoAcao * taxaResp;
      evasoesEvitadas += pEvitada;
      receitaSalva += pEvitada * clv * margem;
    }

    const custoTotal = nAlvo * custoAcao;
    const deltaReceitaLiquida = receitaSalva - custoTotal;
    const roi = custoTotal > 0 ? deltaReceitaLiquida / custoTotal : 0;

    return NextResponse.json({
      orcamento,
      custo_acao: custoAcao,
      taxa_resposta: taxaResp,
      efeito_acao: efeitoAcao,
      margem,
      clientes_abordados: nAlvo,
      custo_total: Number(custoTotal.toFixed(2)),
      evasoes_evitadas: Number(evasoesEvitadas.toFixed(2)),
      receita_bruta_salva: Number(receitaSalva.toFixed(2)),
      delta_receita_liquida: Number(deltaReceitaLiquida.toFixed(2)),
      roi_pct: Number((roi * 100).toFixed(1)),
    });
  } catch (error: any) {
    console.error('Erro em /api/simulator/calculate:', error);
    return NextResponse.json(
      { error: 'Falha ao calcular simulação de impacto financeiro', details: error.message },
      { status: 500 }
    );
  }
}
