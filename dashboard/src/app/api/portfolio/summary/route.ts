import { NextResponse } from 'next/server';
import { getPortfolioSummary } from '@/lib/data/reader';

export async function GET() {
  try {
    const summary = await getPortfolioSummary();
    return NextResponse.json(summary, {
      headers: {
        'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error: any) {
    console.error('Erro em /api/portfolio/summary:', error);
    return NextResponse.json(
      { error: 'Falha ao calcular sumário da carteira', details: error.message },
      { status: 500 }
    );
  }
}
