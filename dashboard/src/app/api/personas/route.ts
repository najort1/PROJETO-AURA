import { NextResponse } from 'next/server';
import { getPersonasSummary } from '@/lib/data/reader';

export async function GET() {
  try {
    const personas = await getPersonasSummary();
    return NextResponse.json(personas);
  } catch (error: any) {
    console.error('Erro em /api/personas:', error);
    return NextResponse.json(
      { error: 'Falha ao obter sumário das personas', details: error.message },
      { status: 500 }
    );
  }
}
