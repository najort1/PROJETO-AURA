import { NextResponse } from 'next/server';
import { getPortfolioCharts } from '@/lib/data/reader';

export async function GET() {
  try {
    const charts = await getPortfolioCharts();
    return NextResponse.json(charts);
  } catch (error: any) {
    console.error('Erro em /api/portfolio/charts:', error);
    return NextResponse.json(
      { error: 'Falha ao gerar gráficos da carteira', details: error.message },
      { status: 500 }
    );
  }
}
