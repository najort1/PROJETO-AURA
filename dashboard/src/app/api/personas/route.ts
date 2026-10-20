import { NextResponse } from 'next/server';
import { getPersonasSummary } from '@/lib/data/reader';

export async function GET() {
  try {
    const personas = await getPersonasSummary();
    return NextResponse.json(personas, {
      headers: {
        'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error: any) {
    console.error('Erro em /api/personas:', error);
    return NextResponse.json(
      { error: 'Falha ao obter sumário das personas', details: error.message },
      { status: 500 }
    );
  }
}
