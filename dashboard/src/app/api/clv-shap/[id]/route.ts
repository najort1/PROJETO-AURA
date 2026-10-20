import { NextRequest, NextResponse } from 'next/server';
import { getClvShapById } from '@/lib/data/reader';
import { formatShapFactor } from '@/lib/data/shap-translations';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const customerId = id.toUpperCase();

    const record = await getClvShapById(customerId);

    if (!record) {
      return NextResponse.json(
        { error: `Fatores SHAP não encontrados para o cliente: ${customerId}` },
        { status: 404 }
      );
    }

    const factors = [
      formatShapFactor(record.top1_feature, record.top1_shap, record.top1_value),
      formatShapFactor(record.top2_feature, record.top2_shap, record.top2_value),
      formatShapFactor(record.top3_feature, record.top3_shap, record.top3_value),
    ];

    return NextResponse.json({
      customer_id: record.customer_id,
      shap_top3: factors,
      raw: record,
    });
  } catch (error: any) {
    console.error('Erro em /api/clv-shap/[id]:', error);
    return NextResponse.json(
      { error: 'Falha ao buscar SHAP do cliente', details: error.message },
      { status: 500 }
    );
  }
}
