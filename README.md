# Aura 2.0 — da milha ao momento de cuidado

Pipeline **reproduzível por código** de inteligência de clientes e retenção para o
Azul Fidelidade, construído sobre uma **base sintética calibrada com fontes públicas
brasileiras** (microdados ANAC locais + fatos verificados do programa via pesquisa).

> ⚠️ **Dados sintéticos — leia antes de interpretar números.**
> Nenhum dado pessoal real é usado. Métricas sobre a base sintética **validam o
> pipeline de ponta a ponta**; não são prova de desempenho no mundo real.
> Premissas, desvios e limitações estão declaradas em [docs/limitations.md](docs/limitations.md)
> e no [mapa de calibração](config/calibration_map.yaml).

```
Fontes públicas ─► Base sintética ─► Features ─► CLV + Churn (SHAP) ─► Score de Alto Valor
                        ▲                                                    │
 Avaliações (aspecto) ─► Sentimento (atritos) ─────────────────────────────┤
                                                                            ▼
                    Segmentação/Personas ─► Agente (RAG + elegibilidade) ─► Mensagem + justificativa
                                                                            │
                                                     Painel Streamlit + simulação de impacto
```

## Início rápido

Requisitos: Python 3.11+ (Windows/Linux/macOS). GNU Make é opcional — sem ele,
use `python tasks.py <alvo>` com os mesmos nomes de alvo.

```bash
# 1) ambiente
python -m venv .venv
# Windows:  .venv\Scripts\activate     |     Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

# 2) dados brutos ANAC (3,2 GB de parquet) na pasta data/raw/anac/
#    (veja "Fontes" abaixo — fornecidos fora do repositório)

# 3) pipeline completo, do zero aos artefatos analíticos + testes
python tasks.py all        # equivalente a: make all

# 4) painel
python tasks.py app        # abre o Streamlit em http://localhost:8501
```

## Alvos

| Alvo | O que faz |
|---|---|
| `ingest` | Registra fontes brutas (manifesto com sha256/licença) e gera agregados ANAC calibrados |
| `synth` | Base sintética (arquétipos latentes, ground truth segregado) + relatório de fidelidade |
| `features` | dbt: curated → analytics (features com cutoff temporal explícito) |
| `train` | CLV (BG/NBD+Gamma-Gamma baseline vs LightGBM) e churn (logística vs LightGBM) |
| `score` | Score de Alto Valor (0,6·CLV + 0,2·RFM + 0,2·potencial), Pareto, sensibilidade, personas |
| `sentiment` | Corpus PT-BR sintético rotulado por aspecto + 2 abordagens + mapa de atritos |
| `rag` | Indexa a base de conhecimento versionada (regras Azul Fidelidade) |
| `agent-eval` | Avaliação do agente: groundedness, guardrails, adversarial |
| `agent-precompute` | Pré-computa recomendações offline (modo demo sem LLM externo) |
| `fairness` | Auditoria de viés (faixa etária, gênero, região) |
| `impact` | Simulação de impacto (cenários + sensibilidade) |
| `dictionary` | Gera `docs/data_dictionary/` a partir dos contratos em `schemas/` |
| `app` | Painel Streamlit |
| `test` / `lint` | pytest / ruff |

## Estrutura

```
├── tasks.py / Makefile      # runner multiplataforma (mesmos alvos)
├── config/                  # settings, regras do programa (versionadas), calibração,
│                            # premissas do gerador, playbook de ações
├── ingestion/               # manifesto + curadoria ANAC (DuckDB)
├── synthetic/               # gerador com processo latente + relatório de fidelidade
├── dbt/                     # modelos SQL curated → analytics (DuckDB ↔ Snowflake)
├── schemas/                 # contratos de dados (fonte do dicionário gerado)
├── ml/                      # clv/ churn/ segmentation/ sentiment/ fairness/ impact/
├── agent/                   # rag/ guardrails/ eval/ compositor offline + eligibilidade determinística
├── app/                     # painel Streamlit (7 telas, tema Azul, modo offline)
├── sql/snowflake/           # DDL + COPY INTO + plano de transição p/ dados reais
├── tests/                   # unit + integração + anti-vazamento + adversarial
├── docs/                    # relatórios, model cards, auditoria, demo, dicionário gerado
└── data/{raw,curated,analytics}  # camadas: bruta (imutável+manifesto), tratada, analítica
```

## Camadas de dados e contratos

- **Bruta** (`data/raw/`): fontes como recebidas, imutáveis, com manifesto
  (URL, data, método, sha256, licença) em `data/manifests/`.
- **Tratada** (`data/curated/`): públicos limpos/tipados + base sintética
  (clientes, voos, transações, interações, ground truth).
- **Analítica** (`data/analytics/`): a ÚNICA camada consumida por modelos e app.
- Cada tabela tem contrato em `schemas/` validado no pipeline e em CI; o
  dicionário é gerado dos contratos (`python tasks.py dictionary`).

## Decisões técnicas (resumo)

| Decisão | Justificativa |
|---|---|
| DuckDB + Parquet local | Processa os 3,2 GB de microdados ANAC sem servidor; SQL analítico |
| dbt-duckdb (SQL portável) | Transformações curated→analytics versionadas e portáveis para Snowflake |
| BG/NBD + Gamma-Gamma implementados em numpy/scipy | Pacote `lifetimes` sem manutenção; fórmulas clássicas com testes próprios |
| SHAP via LightGBM `pred_contrib` | TreeSHAP exato nativo, sem dependência pesada |
| RAG local (TF-IDF/BM25 + cosine) sobre fatos versionados | Reprodutível offline; citações com id/vigência/status de verificação |
| Agente offline por padrão + LLM pluggável (OpenAI-compatible) | Demo nunca quebra por falta de credencial; modo LLM é opcional |
| Corpus de avaliações sintético rotulado | Coleta real bloqueada por termos de uso; limitação declarada |

## Fontes e licenças

- **ANAC — microdados** (tarifas, estatísticas de voos, movimentação, aeródromos,
  aeronaves): dados abertos governamentais; verificação de colunas/licença em
  [docs/source_verification.md](docs/source_verification.md).
- **Azul Fidelidade (regras do programa)**: snapshot versionado compilado por
  pesquisa (12/10/2026) com status de verificação por fato em
  [config/program_rules.yaml](config/program_rules.yaml); captura direta do site
  oficial é bloqueada (HTTP 403).

## Dados reais (Snowflake)

Contratos idênticos: trocar sintético por real é troca de fonte, não reescrita.
Ver `sql/snowflake/` (DDL, COPY INTO) e o plano de transição em
[docs/snowflake_plan.md](docs/snowflake_plan.md).
