import { NextResponse } from 'next/server';
import { getFairnessMetrics } from '@/lib/data/reader';

export async function GET() {
  try {
    const metrics = await getFairnessMetrics();

    // Contagem de conformidade
    let compliantCount = 0;
    let nonCompliantCount = 0;
    let excludedFromDenomCount = 0;

    for (const m of metrics) {
      if (m.group_value === 'Não informado') {
        excludedFromDenomCount++;
      } else if (m.four_fifths_compliant) {
        compliantCount++;
      } else {
        nonCompliantCount++;
      }
    }

    return NextResponse.json({
      data: metrics,
      count: metrics.length,
      compliance_summary: {
        compliant_groups: compliantCount,
        non_compliant_groups: nonCompliantCount,
        excluded_groups: excludedFromDenomCount,
        rule_threshold: 0.8,
        disparity_rule: 'EEOC Four-Fifths Rule (29 CFR § 1607.4) / Art. 20 LGPD',
      },
    });
  } catch (error: any) {
    console.error('Erro em /api/fairness:', error);
    return NextResponse.json(
      { error: 'Falha ao buscar métricas de IA Responsável', details: error.message },
      { status: 500 }
    );
  }
}
