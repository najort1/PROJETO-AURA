# `personas_summary`

> **Descrição:** Resumo quantitativo, atributos comportamentais e recomendações do playbook por persona  
> **Granularidade:** uma linha por persona catalogada  
> **Produzida por:** ml.segmentation.personas  
> **Consumidores:** app.views.01_carteira, app.views.02_personas

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `persona` | string | não | Identificador canônico da persona | - | ml/segmentation/personas.py | não | `executivo_recorrente` |
| `nome_display` | string | não | Nome de exibição amigável para a interface | - | ml/segmentation/personas.py | não | `Executivo Recorrente` |
| `cor` | string | não | Cor hexadecimal temática da persona no design system | - | ml/segmentation/personas.py | não | `#033774` |
| `clientes_count` | int | não | Total de membros atribuídos a esta persona | clientes | ml/segmentation/personas.py | não | `8500` |
| `share_pct` | float | não | Fração percentual da carteira representada pela persona (0.0 a 1.0) | ratio | ml/segmentation/personas.py | não | `0.17` |
| `clv_medio` | float | não | CLV 12m médio dos membros da persona (BRL) | BRL | ml/segmentation/personas.py | não | `8500.0` |
| `churn_medio` | float | não | Probabilidade média de churn predita dos membros da persona | probabilidade | ml/segmentation/personas.py | não | `0.38` |
| `valor_em_risco_total` | float | não | Soma do valor em risco (CLV × P(churn)) para a persona (BRL) | BRL | ml/segmentation/personas.py | não | `27500000.0` |
| `atritos_dominantes` | string | não | Atritos mais frequentes reportados pelos clientes da persona | - | ml/segmentation/personas.py | não | `atraso, atendimento` |
| `acao_recomendada` | string | não | Ação de retenção principal recomendada do playbook | - | ml/segmentation/personas.py | não | `Contato Proativo de Relacionamento (ACT-CONTATO)` |
| `descricao` | string | não | Descrição qualitativa do perfil comportamental da persona | - | ml/segmentation/personas.py | não | `Alta frequência corporativa em rotas troncais...` |
| `ticket_medio` | float | não | Gasto médio estimado por viagem dos clientes da persona (BRL) | BRL | ml/segmentation/personas.py | não | `650.0` |

## Checagens de contrato

- **unicidade:** `persona`
- **não nulo:** `persona`
- **não nulo:** `nome_display`
- **não nulo:** `cor`
- **não nulo:** `clientes_count`
- **não nulo:** `share_pct`
- **não nulo:** `clv_medio`
- **não nulo:** `churn_medio`
- **não nulo:** `valor_em_risco_total`
- **não nulo:** `atritos_dominantes`
- **não nulo:** `acao_recomendada`
- **não nulo:** `descricao`
- **não nulo:** `ticket_medio`
