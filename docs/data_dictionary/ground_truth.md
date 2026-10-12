# `ground_truth`

> **Descrição:** Verdade latente individual e parâmetros geradores verdadeiros (estritamente segregada para avaliação e auditoria)  
> **Granularidade:** um registro por cliente sintético  
> **Produzida por:** synthetic.generate  
> **Consumidores:** evaluation_only

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | synthetic.generate | não | `C000001` |
| `latent_archetype` | string | não | Família latente real geradora do cliente (usada para cálculo de ARI de recuperação de personas) | - | synthetic.generate (config/generator.yaml) | não | `executivo_recorrente` |
| `clv_real_12m` | float | não | Receita líquida total efetivamente realizada pelo cliente na janela alvo de 12 meses (2025-09-01 a 2026-08-31) | BRL | synthetic.generate | não | `4250.8` |
| `churn_observed_12m` | int | não | Indicador binário de inatividade observada (> 2x intervalo individual e >= 180 dias sem transação no período alvo) | binario | synthetic.generate (config/settings.yaml: modeling) | não | `0` |
| `latent_churn_event_12m` | int | não | Indicador estocástico latente de desistência do programa disparado pelo processo de hazard | binario | synthetic.generate | não | `0` |
| `latent_base_hazard` | float | não | Taxa anual basal de hazard de churn atribuída ao arquétipo do cliente | taxa_anual | synthetic.generate | não | `0.09` |
| `latent_annual_frequency` | float | não | Frequência esperada latente de voos por ano calibrada com efeito aleatório | voos_por_ano | synthetic.generate | não | `22.5` |
| `latent_price_sensitivity` | float | não | Elasticidade-preço individual latente do cliente | elasticidade | synthetic.generate | não | `-0.35` |
| `latent_redemption_propensity` | float | não | Propensão individual de queima/resgate de pontos acumulados | propensao_0_a_1 | synthetic.generate | não | `0.22` |
| `latent_freq_effect` | float | não | Efeito aleatório individual de frequência epsilon_freq ~ N(0, sigma) | desvio_padrao | synthetic.generate | não | `0.12` |
| `latent_spend_effect` | float | não | Efeito aleatório individual de gasto monetário epsilon_spend ~ N(0, sigma) | desvio_padrao | synthetic.generate | não | `0.08` |
| `latent_churn_effect` | float | não | Efeito aleatório individual de hazard de churn epsilon_churn ~ N(0, sigma) | desvio_padrao | synthetic.generate | não | `-0.05` |
| `total_frictions_lifetime` | int | não | Contagem total de episódios de atrito vivenciados pelo cliente ao longo de toda a simulação | contagem | synthetic.generate | não | `3` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `latent_archetype`
- **não nulo:** `clv_real_12m`
- **não nulo:** `churn_observed_12m`
- **não nulo:** `latent_churn_event_12m`
- **não nulo:** `latent_base_hazard`
- **não nulo:** `latent_annual_frequency`
- **não nulo:** `latent_price_sensitivity`
- **não nulo:** `latent_redemption_propensity`
- **não nulo:** `latent_freq_effect`
- **não nulo:** `latent_spend_effect`
- **não nulo:** `latent_churn_effect`
- **não nulo:** `total_frictions_lifetime`
