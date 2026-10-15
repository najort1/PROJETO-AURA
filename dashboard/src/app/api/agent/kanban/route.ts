import { NextResponse } from 'next/server';
import { getKanbanBoard } from '@/lib/data/reader';

export async function GET() {
  try {
    const kanban = await getKanbanBoard();
    return NextResponse.json(kanban);
  } catch (error: any) {
    console.error('Erro em /api/agent/kanban:', error);
    return NextResponse.json(
      { error: 'Falha ao montar Kanban do Agente', details: error.message },
      { status: 500 }
    );
  }
}
