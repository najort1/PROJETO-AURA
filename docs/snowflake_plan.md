# Plano de transição para dados reais (Snowflake)

> Princípio do projeto: **contrato de dados idêntico** — trocar sintético por real é
> troca de fonte, não reescrita (plano mestre, WS11/§2).

## 1. O que já está pronto e NÃO muda

| Camada | Artefato | Papel na transição |
|---|---|---|
| Contratos | `schemas/*.yaml` | Idênticos — validam sintético hoje, real amanhã |
| Transformações | `dbt/` (SQL portável) | Só troca o adapter (dbt-duckdb → dbt-snowflake) |
| Modelos | `ml/` (CLV, churn, segmentação) | Iguais — leem `data/analytics` com mesmas colunas |
| Agente | `agent/` (RAG + elegibilidade) | Igual — contratos de entrada/saída preservados |
| Painel | `app/` | Igual — leitura é por `data/analytics` |
| Dicionário | `python tasks.py dictionary` | Regenera dos contratos |

## 2. Passos da transição (dados reais)

1. **Provisionamento**: criar database/schema Snowflake (ex.: `AURA_RAW`, `AURA_CURATED`, `AURA_ANALYTICS`).
2. **Estruturas de carga**: executar `sql/snowflake/ddl.sql` — file format parquet, stages, tabelas externas/`COPY INTO` (o script segue os mesmos nomes de tabela dos contratos).
3. **Carga bruta**: carregar os eventos reais pelas stages com `sql/snowflake/carga.sql` — raw permanece imutável com manifesto (mesma prática de `data/manifests/`).
4. **Curadoria**: mapear as fontes reais para os MESMOS contratos da camada curated (a coluna `source` de cada schema YAML documenta a origem esperada). Campos ausentes = bloqueio explícito (fail loud), nunca preenchimento silencioso.
5. **dbt para Snowflake**: instalar `dbt-snowflake`, apontar `profiles.yml` para o target `snowflake` (mesmos modelos, mesma ordem DAG).
6. **Reexecutar o pipeline**: `python tasks.py all` — features, modelos, scores, agente e app recalculam sobre a fonte real.
7. **Validação**: contratos (`schemas.load.validate_or_raise`) + testes de vazamento temporal + auditoria de viés com dados reais (ritos do RIPD, seção 4 de `docs/ripd.md`).
8. **Piloto A/B** conforme `docs/impact_simulation.md` (grupo de controle, humano no circuito).

## 3. O que muda de fato

- Fontes dbt (`sources`) apontam para tabelas Snowflake em vez de parquet local.
- `ml/impact` recalibra premissas com efeitos reais do piloto.
- Nomes/IDs de clientes viram chaves do CRM — pseudonimizados na camada analítica.
- O RAG pode ingerir o regulamento vigente oficial (troca do snapshot provisional por
  captura manual registrada; ver `config/program_rules.yaml` replacement_protocol).

## 4. Campos mínimos esperados (resumo por tabela)

| Contrato | Campos mínimos do dado real |
|---|---|
| `synthetic_customers` → clientes reais | id pseudonimizado, tier, região (opcional para auditoria), data de entrada |
| `synthetic_flights` → eventos de voo | id, data, rota (origem/destino OACI), tarifa paga, atraso |
| `synthetic_transactions` → transações | id, data, valor, tipo (passagem/ancillary), pontos debitados |
| `synthetic_loyalty_events` → eventos do programa | id, data, tipo (acúmulo/resgate/tier), pontos, qualificação |
| `synthetic_interactions` → contatos | id, data, canal, categoria do contato/atrito |

> Detalhe completo de tipos/nullabilidade: ver cada contrato em `schemas/` e o
> dicionário gerado em `docs/data_dictionary/`.
