import { NextResponse } from 'next/server';
import { getFrictionMap } from '@/lib/data/reader';

export async function GET() {
  try {
    const rawList = await getFrictionMap();

    // Consolida pesos calibrados por aspecto
    const aspectWeights: Record<string, number> = {
      atraso: 0.1965,
      atendimento: 0.1770,
      bagagem: 0.1666,
      resgate_milhas: 0.1660,
      app_checkin: 0.1411,
      preco: 0.1026,
      conforto: 0.0502,
    };

    // Agrega totais por aspecto
    const summaryByAspect: Record<
      string,
      { total_mentions: number; total_negative: number; avg_negative_rate: number; weight: number }
    > = {};

    for (const r of rawList) {
      if (!summaryByAspect[r.aspect]) {
        summaryByAspect[r.aspect] = {
          total_mentions: 0,
          total_negative: 0,
          avg_negative_rate: 0,
          weight: aspectWeights[r.aspect] || r.aspect_weight || 0,
        };
      }
      summaryByAspect[r.aspect].total_mentions += r.mention_count;
      summaryByAspect[r.aspect].total_negative += r.negative_count;
    }

    for (const [aspect, data] of Object.entries(summaryByAspect)) {
      data.avg_negative_rate =
        data.total_mentions > 0
          ? Number((data.total_negative / data.total_mentions).toFixed(4))
          : 0;
    }

    return NextResponse.json({
      data: rawList,
      count: rawList.length,
      aspect_weights: aspectWeights,
      summary_by_aspect: summaryByAspect,
      methodology_declaration:
        'DECLARAÇÃO METODOLÓGICA — CORPUS SINTÉTICO (LGPD / TERMOS DE USO): As avaliações e menções analisadas foram geradas sinteticamente com calibração semântica e rotulagem por aspecto em PT-BR. Nenhum dado pessoal, perfil ou avaliação extraída sem autorização de plataformas terceiras é armazenado neste repositório.',
    });
  } catch (error: any) {
    console.error('Erro em /api/friction:', error);
    return NextResponse.json(
      { error: 'Falha ao buscar mapa de atritos', details: error.message },
      { status: 500 }
    );
  }
}
