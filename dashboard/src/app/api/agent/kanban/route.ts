import { NextRequest, NextResponse } from 'next/server';
import { getKanbanBoard } from '@/lib/data/reader';

export async function GET(request: NextRequest) {
  try {
    const searchParams =
      request.nextUrl?.searchParams ??
      (request.url ? new URL(request.url).searchParams : null);
    const customerId = searchParams?.get('customer_id')?.trim().toUpperCase() || undefined;
    const kanban = await getKanbanBoard(customerId);
    return NextResponse.json(kanban);
  } catch (error: any) {
    console.error('Erro em /api/agent/kanban:', error);
    return NextResponse.json(
      { error: 'Falha ao montar Kanban do Agente', details: error.message },
      { status: 500 }
    );
  }
}
