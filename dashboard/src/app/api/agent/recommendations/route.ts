import { NextRequest, NextResponse } from 'next/server';
import {
  getAgentRecommendations,
  getAgentRecommendationsByHumanReview,
} from '@/lib/data/reader';
import type { AgentRecommendation } from '@/types/actions';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const customerId = searchParams.get('customer_id')?.trim().toUpperCase();
    const actionId = searchParams.get('action_id')?.trim();
    const humanReview = searchParams.get('human_review');
    const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10));
    const pageSize = Math.min(500, Math.max(1, parseInt(searchParams.get('page_size') || '50', 10)));

    let list: AgentRecommendation[];

    if (humanReview !== null && humanReview !== undefined && humanReview !== '') {
      const isHr = humanReview.toLowerCase() === 'true';
      list = await getAgentRecommendationsByHumanReview(isHr);
    } else {
      list = await getAgentRecommendations();
    }

    if (customerId) {
      list = list.filter((r) => r.customer_id.toUpperCase().includes(customerId));
    }
    if (actionId) {
      list = list.filter((r) => r.action_id === actionId);
    }

    const total = list.length;
    const totalPages = Math.ceil(total / pageSize);
    const startIndex = (page - 1) * pageSize;
    const paginated = list.slice(startIndex, startIndex + pageSize);

    return NextResponse.json({
      data: paginated,
      total,
      page,
      page_size: pageSize,
      total_pages: totalPages,
    });
  } catch (error: any) {
    console.error('Erro em /api/agent/recommendations:', error);
    return NextResponse.json(
      { error: 'Falha ao buscar recomendações do agente', details: error.message },
      { status: 500 }
    );
  }
}
