import { NextRequest, NextResponse } from 'next/server';
import { getCustomersScores, getSortedCustomersByVar } from '@/lib/data/reader';
import { CustomerScore } from '@/types/analytics';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10));
    const pageSize = Math.min(500, Math.max(1, parseInt(searchParams.get('page_size') || '50', 10)));
    const search = (searchParams.get('search') || '').trim().toUpperCase();
    const tier = (searchParams.get('tier') || '').trim().toLowerCase();
    const persona = (searchParams.get('persona') || '').trim();
    const altoValor = searchParams.get('alto_valor');
    const sortBy = (searchParams.get('sort_by') || 'valor_em_risco') as keyof CustomerScore;
    const sortOrder = searchParams.get('sort_order') === 'asc' ? 'asc' : 'desc';

    const isDefaultSort = sortBy === 'valor_em_risco' && sortOrder === 'desc';

    let list = isDefaultSort
      ? await getSortedCustomersByVar()
      : await getCustomersScores();

    // Filtros
    if (search) {
      list = list.filter(
        (c) =>
          c.customer_id.toUpperCase().includes(search) ||
          (c.rota_favorita && c.rota_favorita.toUpperCase().includes(search))
      );
    }
    if (tier) {
      if (tier === 'unique' || tier === 'diamante unique') {
        list = list.filter((c) => c.tier.toLowerCase() === 'diamante' && c.alto_valor);
      } else {
        list = list.filter((c) => c.tier.toLowerCase() === tier);
      }
    }
    if (persona) {
      list = list.filter((c) => c.persona === persona);
    }
    if (altoValor !== null && altoValor !== undefined && altoValor !== '') {
      const isAltoValor = altoValor.toLowerCase() === 'true';
      list = list.filter((c) => c.alto_valor === isAltoValor);
    }

    // Ordenação dinâmica apenas quando diferente do default pré-ordenado em cache
    if (!isDefaultSort) {
      const sampleVal = list.length > 0 ? list[0][sortBy] : undefined;
      const isNumeric = typeof sampleVal === 'number';

      list = [...list].sort((a, b) => {
        const valA = a[sortBy] ?? 0;
        const valB = b[sortBy] ?? 0;
        if (isNumeric) {
          return sortOrder === 'asc'
            ? (valA as number) - (valB as number)
            : (valB as number) - (valA as number);
        }
        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortOrder === 'asc' ? valA - valB : valB - valA;
        }
        const strA = String(valA);
        const strB = String(valB);
        if (strA < strB) return sortOrder === 'asc' ? -1 : 1;
        if (strA > strB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
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
    console.error('Erro em /api/customers:', error);
    return NextResponse.json(
      { error: 'Falha ao buscar clientes', details: error.message },
      { status: 500 }
    );
  }
}
