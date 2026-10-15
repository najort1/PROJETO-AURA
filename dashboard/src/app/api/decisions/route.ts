import { NextRequest, NextResponse } from 'next/server';
import { recordDecision, getRecordedDecisions } from '@/lib/data/decisions';
import { DecisionRecordSchema } from '@/types/actions';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const customerId = searchParams.get('customer_id')?.trim().toUpperCase();

    const { decisions, corrupted_lines } = await getRecordedDecisions(customerId);

    return NextResponse.json({
      data: decisions,
      total: decisions.length,
      corrupted_lines_detected: corrupted_lines,
    });
  } catch (error: any) {
    console.error('Erro em GET /api/decisions:', error);
    return NextResponse.json(
      { error: 'Falha ao recuperar histórico de decisões', details: error.message },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validação preliminar do payload
    const parsed = DecisionRecordSchema.safeParse({
      ...body,
      customer_id: body.customer_id?.trim().toUpperCase(),
    });

    if (!parsed.success) {
      return NextResponse.json(
        {
          error: 'Payload inválido para gravação de decisão',
          issues: parsed.error.issues,
        },
        { status: 400 }
      );
    }

    // Gravação com protocolo atômico dual-write em data/analytics/decisions.jsonl
    const record = await recordDecision(parsed.data);

    return NextResponse.json(
      {
        message: 'Decisão persistida com sucesso e registrada na trilha auditável',
        record,
      },
      { status: 201 }
    );
  } catch (error: any) {
    console.error('Erro em POST /api/decisions:', error);
    return NextResponse.json(
      {
        error: 'Erro crítico na persistência da decisão (Rollback efetuado)',
        details: error.message,
      },
      { status: 500 }
    );
  }
}
