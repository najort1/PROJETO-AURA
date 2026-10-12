# Contratos de dados (schemas/)

Cada arquivo `*.yaml` aqui é o **contrato** de uma tabela do projeto: fonte única
de verdade para nome, tipo, semântica, origem e sensibilidade das colunas.

- O **dicionário de dados** (`docs/data_dictionary/`) é **gerado** daqui por
  `python tasks.py dictionary` — nunca editado à mão.
- A **validação** (CI + pipeline) roda por `schemas.validate_table` — contrato
  violado quebra o pipeline (fail loud).
- Testes SQL arbitrários (ex.: anti-vazamento temporal) vivem em `checks.custom`.

## Formato do contrato

```yaml
table: features_customer          # nome canônico (arquivo parquet correspondente)
description: Features por cliente na coorte de análise
granularity: um cliente
produced_by: dbt (features)
consumers: [ml.clv, ml.churn, ml.segmentation, app]
columns:
  - name: customer_id
    dtype: string                # string|int|float|bool|date|datetime|category
    nullable: false
    description: Identificador único do cliente sintético
    unit: null                   # unidade de medida, quando aplicável
    source: data/curated/synthetic/customers.parquet
    sensitive: false             # true => dado sensível (LGPD); auditoria de uso obrigatória
    example: "C000001"
  - name: flights_last_12m
    dtype: int
    nullable: false
    description: Voos pagos nos 12 meses anteriores ao cutoff
    unit: voos
    source: dbt: features
    sensitive: false
    example: 14
checks:
  unique: [customer_id]
  non_null: [customer_id, flights_last_12m]
  allowed_values: {}              # opcional: {coluna: [valores]}
  custom:
    - name: no_future_information
      expr: "MAX(last_flight_date) <= DATE '2025-08-31'"
      message: "Feature contém informação posterior ao cutoff temporal (vazamento)"
```

## Regras

1. **Contrato antes do código**: a frente produtora escreve o contrato e o
   consumidor valida contra ele antes de integrar.
2. `sensitive: true` proíbe uso como feature de modelo (LGPD/fairness).
3. Toda coluna deve ter `description` e `source` — o dicionário é auditável.
4. Mudança de contrato = edição do YAML + commit (mudanças são rastreáveis).
5. Tabelas avaliadas no ground truth latente (ex.: `ground_truth`) carregam
   `consumers: [evaluation_only]` e são lidas somente pelos avaliadores.
