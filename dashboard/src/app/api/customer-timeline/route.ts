import { NextRequest, NextResponse } from 'next/server';
import { getCustomerTimeline } from '@/lib/data/reader';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const customerId = searchParams.get('customer_id')?.trim().toUpperCase();

    // getCustomerTimeline aplica estritamente o guardrail data <= '2025-08-31'
    const events = await getCustomerTimeline(customerId);

    return NextResponse.json({
      data: events,
      count: events.length,
      temporal_cutoff: '2025-08-31',
    });
  } catch (error: any) {
    console.error('Erro em /api/customer-timeline:', error);
    return NextResponse.json(
      { error: 'Falha ao buscar timeline do cliente', details: error.message },
      { status: 500 }
    );
  }
}
