import { NextRequest, NextResponse } from 'next/server';
import { recordDecision, getRecordedDecisions } from '@/lib/data/decisions';
import { DecisionRecordSchema } from '@/types/actions';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const customerId = searchParams.get('customer_id')?.trim().toUpperCase();

    // Retrocompatibilidade estrita: sem `limit` explícito, retorna a lista COMPLETA
    // (comportamento anterior à paginação). `offset` isolado permanece aplicável.
    // Quando `limit` é informado, valida inteiro não-negativo e limita a 1000.
    const rawLimit = searchParams.get('limit');
    const rawOffset = searchParams.get('offset');

    let limit: number | null = null;
    if (rawLimit !== null && rawLimit !== '') {
      const parsedLimit = parseInt(rawLimit, 10);
      if (isNaN(parsedLimit) || parsedLimit < 0) {
        return NextResponse.json(
          { error: 'Parâmetro limit inválido: deve ser um inteiro não-negativo' },
          { status: 400 }
        );
      }
      limit = Math.min(1000, parsedLimit);
    }

    let offset = 0;
    if (rawOffset !== null && rawOffset !== '') {
      const parsedOffset = parseInt(rawOffset, 10);
      if (isNaN(parsedOffset) || parsedOffset < 0) {
        return NextResponse.json(
          { error: 'Parâmetro offset inválido: deve ser um inteiro não-negativo' },
          { status: 400 }
        );
      }
      offset = parsedOffset;
    }

    const { decisions, corrupted_lines } = await getRecordedDecisions(customerId);
    const total = decisions.length;
    const paginated =
      limit === null ? decisions.slice(offset) : decisions.slice(offset, offset + limit);

    return NextResponse.json({
      data: paginated,
      total,
      limit,
      offset,
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

    // Tratamento e sanitização retrocompatível do operador nominal (P0-2)
    const rawOperator =
      typeof body.operator === 'string' && body.operator.trim().length > 0
        ? body.operator.trim()
        : undefined;

    // Validação preliminar do payload
    const parsed = DecisionRecordSchema.safeParse({
      ...body,
      customer_id: body.customer_id?.trim().toUpperCase(),
      ...(rawOperator !== undefined ? { operator: rawOperator } : {}),
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
