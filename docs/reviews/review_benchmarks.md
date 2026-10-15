# Revisão Adversarial Independente — Módulo de Benchmarks da Aviação (Segunda Rodada / Re-Review)

**Data:** 14 de Outubro de 2026  
**Avaliador:** Revisor Adversarial Independente (`mega-brain`)  
**Frente Avaliada:** Ingestão, Curadoria e Agregação de Benchmarks do Setor Aéreo  
**Arquivos Inspecionados:**
- `ingestion/benchmarks.py`
- `tasks.py`
- `tests/test_benchmarks.py`
- `data/manifests/benchmarks.json`
- `.gitignore`
- `data/curated/benchmarks/loyalty_aggregated.parquet`
- `data/curated/benchmarks/passenger_satisfaction.parquet`
- `data/curated/benchmarks/airline_reviews.parquet`
- `data/curated/benchmarks/benchmark_summary.json`

---

## 1. Resumo Executivo e Veredito

Na primeira rodada de revisão, este Revisor emitiu parecer **REPROVADO** com 18 achados (DEF-01 a DEF-18), destacando vícios estatísticos e metodológicos graves (como o *Immortal Time Bias* na relação entre resgates e churn, e a dupla contagem física de atrasos de voo), além de violações de hermeticidade nos testes e falta de manifesto de integridade.

Nesta segunda rodada de revisão adversarial (Re-Review), o código-fonte, a suíte de testes e os dados curados reais foram re-auditados exaustivamente de ponta a ponta.

**Veredito Final:** **APROVADO**

Todas as 18 não-conformidades foram rigorosamente sanadas. Não foram detectadas regressões funcionais, violações de hermeticidade ou efeitos colaterais na arquitetura geral do Projeto Aura 2.0. A suíte completa de testes (201/201 testes) roda verde e o linter (`ruff check .`) passa sem qualquer apontamento.

---

## 2. Auditoria Detalhada dos 18 Defeitos (DEF-01 a DEF-18)

| Defeito | Classificação | Descrição do Problema Original | Status Pós-Auditoria | Evidência / Verificação |
|---|---|---|---|---|
| **DEF-01** | CRÍTICO | **Immortal Time Bias / Viés de Sobrevivência:** Correlação de resgate vs churn comparava clientes de 24 meses com churners precoces sem coorte fixa nem normalização mensal. | **RESOLVIDO** | Coorte ativa em 2017-01 isolada (10.512 membros, 656 churns). Normalização estrita por `redemptions_per_active_month`. A correlação ingênua (-0.1767) foi corrigida para +0.0236, eliminando a ilusão de causalidade protetora. Metodologia descrita no JSON. |
| **DEF-02** | CRÍTICO | **Dupla Contagem de Atraso:** Soma `departure + arrival = total_delay` somava fisicamente duas vezes o mesmo atraso operacional. | **RESOLVIDO** | `total_delay_minutes` completamente extirpado. Adicionada a métrica aeronáutica canônica `en_route_delay_delta = arrival - departure`. |
| **DEF-03** | IMPORTANTE | **Divisor Fixo de 24 Meses:** Divisão cega por 24 subestimava médias de pontos para ingressantes tardios ou churners. | **RESOLVIDO** | Implementado `active_months_in_window` dinâmico (limites 1 a 24 meses) baseado na exposição efetiva na janela 2017-2018, sem erro de off-by-one. |
| **DEF-04** | IMPORTANTE | **Integração no Pipeline:** `benchmarks` não constava no `TARGETS` nem no `PIPELINE` de `tasks.py`. | **RESOLVIDO** | `tasks.py` atualizado com target `benchmarks` mapeado para `python -m ingestion.benchmarks` e incluído no `PIPELINE` logo após `ingest`. |
| **DEF-05** | IMPORTANTE | **Violação de Hermeticidade de Testes:** Testes causavam mutação direta em `data/curated/benchmarks/`. | **RESOLVIDO** | CLI e funções suportam `--output-dir`. Testes unitários apontam para `tmp_path`. Verificação de mtimes comprovou zero mutação nos dados de produção durante o pytest. |
| **DEF-06** | IMPORTANTE | **Rigor e Testes Sintéticos:** Testes anteriores faziam apenas checagens superficiais de existência de arquivos. | **RESOLVIDO** | Implementados testes sintéticos determinísticos dedicados para `burn_rate` (5 casos), imputação de atrasos e isolamento de coorte temporal (5 perfis). |
| **DEF-07** | MENOR | **Coluna residual `unnamed_0`:** CSV do Kaggle trazia index cru não descartado. | **RESOLVIDO** | Descarte explícito de qualquer coluna iniciada com `unnamed` pré e pós normalização. Zero colunas desse tipo no parquet curado. |
| **DEF-08** | IMPORTANTE | **Imputação Cega de Atraso de Chegada:** 393 nulos eram preenchidos sem rastreabilidade de linhagem. | **RESOLVIDO** | Flag booleana `arrival_delay_imputed` gerada antes da imputação. Exatamente 393 registros marcados como True. |
| **DEF-09** | MENOR | **Duplicatas em Flight Activity:** Linhas repetidas inflavam somatórios de voos. | **RESOLVIDO** | Deduplicação explícita em nível de linha (`drop_duplicates()`) removendo 1.864 linhas idênticas antes da agregação por cliente. |
| **DEF-10** | MENOR | **Casos de Borda de `burn_rate`:** Divisão por zero causava `inf` ou tratava queima de saldo anterior como 0.0. | **RESOLVIDO** | `np.select` tratando: acum>0 -> ratio; acum==0 & red==0 -> 0.0; acum==0 & red>0 -> `np.nan`. Zero `inf`s nos dados. |
| **DEF-11** | IMPORTANTE | **Zeros Espúrios na Escala Skytrax:** Avaliações não preenchidas vinham como 0.0 (fora da escala 1 a 5). | **RESOLVIDO** | Zeros substituídos por `np.nan` nas 7 colunas de aspectos da Skytrax. Min e Max estritamente entre 1.0 e 5.0. |
| **DEF-12** | IMPORTANTE | **Governança e Proveniência de Dados:** Arquivos CSV brutos sem rastreamento formal de hash. | **RESOLVIDO** | Manifesto formal `data/manifests/benchmarks.json` gerado com SHA-256 e tamanhos em bytes dos 4 arquivos brutos. Arquivos brutos adicionados ao `.gitignore`. |
| **DEF-13** | MENOR | **Top Airlines sem Significância Amostral:** Companhias com 1 ou 2 reviews nota 10 dominavam o ranking. | **RESOLVIDO** | Filtro de representatividade amostral mínima (`review_count >= 50`) aplicado antes da ordenação da média de avaliações. |
| **DEF-14** | MENOR | **Inconsistência de Tipos em Atrasos:** Atraso de chegada permanecia `float64` pós-imputação. | **RESOLVIDO** | Conversão explícita para `int64` tanto em `arrival_delay_minutes`, `departure_delay_minutes` quanto em `en_route_delay_delta`. |
| **DEF-15** | MENOR | **Tipo Não Nativo em `recommended`:** Strings `'yes'` / `'no'` em vez de booleano. | **RESOLVIDO** | Conversão para tipo booleano nativo `bool` (`.eq('yes')`), sem valores nulos. |
| **DEF-16** | MENOR | **Sanitização de Aspas em Títulos:** `review_title` continha aspas duplas residuais de exportação. | **RESOLVIDO** | Higienização via `.str.strip(r'"\s')`. Zero títulos iniciando ou terminando com aspas no dataset final. |
| **DEF-17** | MENOR | **Transliteração Unicode em `to_snake_case`:** Regex deletava acentos sem normalização prévia. | **RESOLVIDO** | `unicodedata.normalize("NFKD", ...)` incorporado, convertendo acentos adequadamente (ex: "Pontuação" -> "pontuacao"). |
| **DEF-18** | MENOR | **Cálculo de `tenure_months` Não Inclusivo:** Clientes no mesmo mês de adesão/cancelamento resultavam em tenure 0. | **RESOLVIDO** | Cálculo inclusivo com `+ 1` mês. Todos os clientes possuem `tenure_months >= 1` (mínimo 1, máximo 81). |

---

## 3. Evidências Verificadas em Ambiente de Execução

### 3.1. Baseline de Testes e Linter
- **pytest:** 201 testes executados, 201 aprovados (0 falhas) em 29.00s.
  ```text
  tests/test_agent_eval_real.py: 5 passed
  tests/test_app_smoke.py: 17 passed
  tests/test_benchmarks.py: 10 passed
  tests/test_bgnbd.py: 6 passed
  tests/test_eligibility.py: 19 passed
  tests/test_fairness.py: 3 passed
  tests/test_features_antileakage.py: 4 passed
  tests/test_guardrails.py: 61 passed
  tests/test_impact.py: 9 passed
  tests/test_ingestion.py: 4 passed
  tests/test_integration.py: 15 passed
  tests/test_metrics.py: 10 passed
  tests/test_rag.py: 8 passed
  tests/test_segmentation.py: 8 passed
  tests/test_sentiment.py: 9 passed
  tests/test_synthetic.py: 13 passed
  ==================== 201 passed in 29.00s ====================
  ```
- **ruff:**
  ```text
  $ uv run ruff check .
  All checks passed!
  ```

### 3.2. Verificação de Hermeticidade
- Executado teste de monitoramento de timestamps de modificação (`os.path.getmtime`) nos arquivos de produção em `data/curated/benchmarks/` antes e depois da execução do pytest.
- **Resultado:** 0 arquivos mutados. Hermeticidade total comprovada.

### 3.3. Verificação de Integridade dos Hashes SHA-256
- Os 4 arquivos CSV declarados em `data/manifests/benchmarks.json` foram checados contra o disco:
  * `Customer Loyalty History.csv`: SHA-256 OK, 1.733.749 bytes OK.
  * `Customer Flight Activity.csv`: SHA-256 OK, 13.167.724 bytes OK.
  * `data.csv`: SHA-256 OK, 11.677.432 bytes OK.
  * `Airline_review.csv`: SHA-256 OK, 20.539.187 bytes OK.

---

## 4. Conclusão e Homologação

A re-implementação efetuada pelo Especialista de Implementação atende com rigor técnico aos mais elevados padrões de engenharia de dados e governança analítica do Projeto Aura 2.0. As correções metodológicas mitigaram vieses estatísticos críticos e conferiram integridade matemática e reprodutibilidade ao pipeline.

O módulo de benchmarks encontra-se pronto e homologado para compor a versão canônica do sistema.
