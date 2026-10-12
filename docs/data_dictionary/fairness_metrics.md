# `fairness_metrics`

> **Descrição:** Métricas de disparidade de seleção e taxas de risco por atributo demográfico sensível (Auditoria Four-Fifths)  
> **Granularidade:** um registro por grupo demográfico em cada dimensão sensível  
> **Produzida por:** ml.fairness.audit  
> **Consumidores:** app.views.07_ia_responsavel, docs.responsible_ai

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `sensitive_attribute` | string | não | Atributo demográfico protegido auditado (faixa_etaria, genero, regiao) | - | data/curated/synthetic/customers.parquet | 🔴 sim | `faixa_etaria` |
| `group_value` | string | não | Valor do segmento/subgrupo demográfico | - | data/curated/synthetic/customers.parquet | 🔴 sim | `18-29` |
| `group_size` | int | não | Contagem de indivíduos pertencentes a este subgrupo | clientes | ml/fairness/audit.py | não | `9000` |
| `alto_valor_count` | int | não | Quantidade de membros do subgrupo classificados como Alto Valor | clientes | ml/fairness/audit.py | não | `450` |
| `selection_rate` | float | não | Taxa de seleção como Alto Valor no subgrupo (alto_valor_count / group_size) | ratio | ml/fairness/audit.py | não | `0.05` |
| `avg_predicted_churn` | float | não | Média da probabilidade prevista de evasão (churn) no subgrupo | probabilidade | ml/fairness/audit.py | não | `0.42` |
| `selection_ratio_vs_max` | float | não | Razão entre a taxa de seleção do grupo e a taxa máxima observada na dimensão (Disparate Impact Ratio) | ratio | ml/fairness/audit.py | não | `0.41` |
| `four_fifths_compliant` | bool | não | Indicador de conformidade com a regra dos quatro quintos (selection_ratio_vs_max >= 0.80) | - | ml/fairness/audit.py | não | `False` |

## Checagens de contrato

- **não nulo:** `sensitive_attribute`
- **não nulo:** `group_value`
- **não nulo:** `group_size`
- **não nulo:** `alto_valor_count`
- **não nulo:** `selection_rate`
- **não nulo:** `avg_predicted_churn`
- **não nulo:** `selection_ratio_vs_max`
- **não nulo:** `four_fifths_compliant`
