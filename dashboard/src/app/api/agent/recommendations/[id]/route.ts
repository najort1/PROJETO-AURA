import { NextRequest, NextResponse } from 'next/server';
import { getRecommendationByCustomerId } from '@/lib/data/reader';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const customerId = id.toUpperCase();

    const recommendation = await getRecommendationByCustomerId(customerId);

    if (!recommendation) {
      return NextResponse.json(
        { error: `Recomendação não encontrada para o cliente: ${customerId}` },
        { status: 404 }
      );
    }

    return NextResponse.json({
      ...recommendation,
      has_citations: recommendation.citations.length > 0,
    });
  } catch (error: any) {
    console.error('Erro em /api/agent/recommendations/[id]:', error);
    return NextResponse.json(
      { error: 'Falha ao buscar recomendação específica', details: error.message },
      { status: 500 }
    );
  }
}
