import { NextRequest, NextResponse } from 'next/server';
import {
  getCustomerById,
  getRecommendationByCustomerId,
  getClvShapById,
  getTimelineByCustomerId,
} from '@/lib/data/reader';
import { formatShapFactor } from '@/lib/data/shap-translations';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const customerId = id.toUpperCase();

    const [customer, recommendation, shapRecord, timeline] = await Promise.all([
      getCustomerById(customerId),
      getRecommendationByCustomerId(customerId),
      getClvShapById(customerId),
      getTimelineByCustomerId(customerId),
    ]);

    if (!customer) {
      return NextResponse.json(
        { error: `Cliente não encontrado: ${customerId}` },
        { status: 404 }
      );
    }

    const shapFactors = shapRecord
      ? [
          formatShapFactor(shapRecord.top1_feature, shapRecord.top1_shap, shapRecord.top1_value),
          formatShapFactor(shapRecord.top2_feature, shapRecord.top2_shap, shapRecord.top2_value),
          formatShapFactor(shapRecord.top3_feature, shapRecord.top3_shap, shapRecord.top3_value),
        ]
      : [];

    return NextResponse.json({
      customer,
      recommendation,
      shap_factors: shapFactors,
      timeline, // já filtrado com o guardrail data <= 2025-08-31
    });
  } catch (error: any) {
    console.error('Erro em /api/customers/[id]:', error);
    return NextResponse.json(
      { error: 'Falha ao buscar perfil do cliente', details: error.message },
      { status: 500 }
    );
  }
}
