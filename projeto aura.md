# Projeto Aura 2.0 — Plano Mestre (meta: nota 10 em todos os critérios)

> Versão: 2.0 · Substitui a proposta anterior (relatório estratégico "Da Milha ao Momento de Cuidado").
> Tese mantida: **da milha ao cuidado**. O que muda: de relatório conceitual para **MVP executável, medido e auditável**.

---

## 1. Visão e proposta de valor

**Problema.** Os clientes de maior valor sustentam a receita e são os menos satisfeitos e reconhecidos pelo programa de fidelidade. A Azul precisa identificá-los, entender o risco de perdê-los e agir de forma personalizada e explicável.

**Solução.** Um pipeline ponta a ponta, 100% reproduzível por código, sobre uma **base sintética calibrada com dados públicos brasileiros**:

```
Fontes públicas ─► Base sintética ─► Features ─► CLV + Churn (SHAP) ─► Score de Alto Valor
                         ▲                                                    │
 Avaliações públicas ─► Sentimento por aspecto (atritos) ─────────────────────┤
                                                                              ▼
                              Segmentação/Personas ─► Agente LLM (RAG no regulamento) ─► Mensagem + justificativa
                                                                              │
                                                              Painel Streamlit + simulação de impacto
```

**Diferenciais (inovação):**

1. **Valor em Risco** = CLV × P(evasão): prioriza quem vale a pena salvar, não só quem vai sair.
2. **Sentimento alimenta o resto do sistema**: atritos detectados nas avaliações (bagagem, atraso, app, resgate de milhas) calibram o gerador sintético e viram contexto para o agente.
3. **Explicabilidade ponta a ponta**: SHAP → motivo em linguagem natural → mensagem redigida → citação do artigo do regulamento que sustenta a oferta.
4. **Contrato de dados idêntico ao esperado no Snowflake**: trocar sintético por dado real é troca de fonte, não reescrita.
5. **(Camada 2) Uplift**: priorizar quem *responde* à ação, não só quem tem risco.

---

## 2. Matriz de critérios: o que é "10" e a evidência que vamos mostrar

### 2.1 Critérios específicos

| Critério | O que é nota 10 | Evidência entregável |
|---|---|---|
| **Rigor analítico na definição de alto valor** | Definição formal, baseada em CLV preditivo (não gasto acumulado), com RFM + potencial, limiar justificado e análise de sensibilidade | Notebook/relatório "Definição de Alto Valor", fórmula versionada, teste de sensibilidade dos pesos e do corte |
| **Qualidade técnica da IA** | Baselines vs. modelo final, validação temporal, métricas adequadas, calibração, SHAP global e local, agente com arquitetura clara e avaliado | Tabela de métricas, curvas de calibração/lift, model card, harness de avaliação do agente |
| **Criatividade e viabilidade da retenção** | Playbook persona × estado de risco com custo, regra de elegibilidade e KPI por ação; viável dentro do regulamento | Matriz de ações, simulação de ROI com premissas explícitas |
| **Qualidade e clareza do protótipo** | App que conta a história em 3 min: visão da carteira → cliente → explicação → mensagem | Streamlit rodando com `make app`, roteiro de demo |
| **Uso inteligente das fontes públicas e da base sintética** | Cada parâmetro do gerador rastreável a uma fonte pública; relatório de fidelidade sintético vs. público | Tabela de calibração (parâmetro → fonte → valor), relatório de validação do sintético |
| **IA responsável e LGPD** | Sem dado pessoal real; atributos sensíveis fora das features; auditoria de viés; recomendações transparentes; humano no circuito | Relatório de fairness, política de IA responsável, RIPD simplificado, logs de decisão do agente |
| **Potencial de impacto real** | Impacto estimado em receita e retenção com intervalo de confiança, plano de piloto e de transição para dados reais | Simulação de impacto, roadmap de piloto A/B, plano de "swap" para dados Azul |

### 2.2 Critérios gerais

| Critério | O que é nota 10 | Como garantimos |
|---|---|---|
| **Inovação** | Combinação inédita: Valor em Risco + sentimento → agente + explicabilidade ponta a ponta | Slide de diferenciais; comparação com o "estado da arte" de CRM de fidelidade |
| **Impacto** | Números defensáveis de receita e retenção, com sensibilidade | Simulação com cenários conservador/base/otimista |
| **Clareza da apresentação** | Narrativa problema → solução → prova → impacto → próximos passos | Pitch de 5 min + demo ao vivo + backup em vídeo |
| **Viabilidade** | Stack aderente ao Snowflake, custo estimado, riscos mapeados | DDL Snowflake, estimativa de custo do LLM, matriz de riscos |
| **Qualidade da solução** | Testes, CI, reprodutibilidade em um comando, documentação gerada do código | `make all` do zero ao painel; testes verdes; dicionário gerado do schema |

---

## 3. Premissas e honestidade metodológica (crítico para o rigor)

- **Modelos treinados em dados sintéticos aprendem o gerador.** Por isso:
  - Reportamos as métricas como **validação do pipeline**, nunca como acurácia no mundo real.
  - O gerador usa **processo latente com ruído** (heterogeneidade individual, eventos exógenos, dados faltantes) para evitar vazamento trivial.
  - O gerador e os modelos são desenvolvidos **separadamente**; a verdade latente (arquétipo, CLV "real", hazard de churn) fica numa tabela de *ground truth* usada **só para avaliação**.
  - Teste de recuperação: os clusters descobertos recuperam os arquétipos latentes? (ARI)
- **Fidelidade vs. verdade:** o sintético só é calibrado em **agregados públicos** (rota, tarifa, demanda); comportamento individual é premissa declarada e parametrizada.
- **Pontos a verificar no início** (não assumir): tiers e regras vigentes do Azul Fidelidade (o relatório anterior cita "Master"; confirmar nomenclatura atual no regulamento), disponibilidade e licença de cada fonte, termos de uso das fontes de avaliações.
- Microdados da ANAC são agregados: calibram o mercado, não o cliente individual.
- Fontes bloqueadas para automação exigem snapshot manual versionado.
- Nenhum valor numérico de fonte pública entra no gerador sem registro no `calibration_map`.

---

## 4. Arquitetura de dados (data lake em camadas, Snowflake-friendly)

| Camada | Pasta | Conteúdo | Formato |
|---|---|---|---|
| **Bruta** (raw) | `data/raw/` | Fontes públicas como baixadas, imutáveis, com manifesto (URL, data, hash, licença) | CSV/JSON/Parquet original |
| **Tratada** (curated) | `data/curated/` | Dados públicos limpos e tipados; base sintética gerada (clientes, voos, transações, interações) | Parquet particionado |
| **Analítica** (analytics) | `data/analytics/` | Tabelas consumidas por modelos e app: features, scores, segmentos, recomendações, sentimento | Parquet |

**Separações obrigatórias (explícitas no repositório):**
1. `ingestion/` ≠ 2. `synthetic/` ≠ 3. `analytics/` (modelos e app só leem a camada analítica).

**Stack proposta:**
- Python 3.11, **DuckDB** (local) + **dbt** (modelos SQL portáveis DuckDB ↔ Snowflake)
- Parquet como formato padrão; contratos de dados com **pandera** ou **Great Expectations**
- Orquestração simples e reproduzível: `Makefile` + **Prefect** ou **Dagster** (opcional)
- Snowflake: DDL `CREATE STAGE / FILE FORMAT / EXTERNAL TABLE` ou `COPY INTO` apontando para o Parquet (entregar scripts, mesmo sem executar)
- ML: scikit-learn, LightGBM/XGBoost, `lifetimes` (BG/NBD + Gamma-Gamma), SHAP, `fairlearn`
- NLP: modelo PT-BR (ex.: BERTimbau fine-tuned) e/ou LLM zero-shot, comparados
- Agente: LLM via API + RAG (embeddings + índice vetorial local, ex.: FAISS/Chroma)
- App: Streamlit
- Qualidade: pytest, ruff, pre-commit, GitHub Actions

**Dicionário de dados:** gerado automaticamente a partir de arquivos de schema YAML (nome, tipo, descrição, unidade, fonte, sensível?, exemplo) e publicado em `docs/data_dictionary/`. Uma única fonte de verdade: o schema.

---

## 5. Estrutura do repositório

```
aura/
├── Makefile                  # make all | ingest | synth | features | train | agent | app | test
├── pyproject.toml
├── config/                   # parâmetros do gerador, pesos, seeds (tudo versionado)
├── ingestion/                # download + manifesto das fontes públicas
├── synthetic/                # gerador, calibração, validação de fidelidade
├── dbt/                      # modelos curated → analytics (portável p/ Snowflake)
├── schemas/                  # YAML dos contratos de dados (fonte do dicionário)
├── ml/
│   ├── clv/  churn/  segmentation/  sentiment/  fairness/
├── agent/
│   ├── rag/  prompts/  guardrails/  eval/
├── app/                      # Streamlit
├── sql/snowflake/            # DDL e carga
├── tests/
├── docs/                     # model cards, política de IA responsável, RIPD, dicionário gerado
└── notebooks/                # exploração e figuras do pitch
```

---

## 6. Frentes de trabalho (workstreams)

> Cada frente tem **entregáveis**, **critério de pronto (DoD)** e **teste de sucesso**.

### WS0 · Fundação
- Repositório, ambiente reproduzível, CI, convenções, seeds globais.
- **DoD:** `make all` roda do zero em máquina limpa; CI verde.

## WS1 (substitui) · Ingestão de fontes públicas (camada bruta)

### Fontes indicadas pela Azul e seu papel

| Fonte | Uso | Calibra | Verificação em 08/10/2026 |
|---|---|---|---|
| ANAC · Microdados de tarifas aéreas comercializadas (CSV) | Distribuição de tarifa efetivamente vendida por rota, mês e ano | Ticket médio e dispersão por rota; sazonalidade de preço | ⚠️ Não verificada (CAPTCHA). Confirmar colunas, período, licença |
| ANAC · Estatísticas e histórico de voos | Passageiros pagos, rotas, origem/destino, atrasos, cancelamentos | Volume por rota/mês; taxa de atraso e cancelamento (insumo de atrito) | ⚠️ Não verificada (CAPTCHA) |
| ANAC · Portal de Dados Abertos | Catálogo e dicionários oficiais dos conjuntos acima | Definição de campos; licença | ⚠️ Não verificada (CAPTCHA) |
| Azul RI · Resultados trimestrais (releases, apresentações, demonstrações, transcrições; disponível até 2T26) | Totais de referência: membros e faturamento do Azul Fidelidade, yield, load factor | Escala da base sintética; receita por membro | ✅ Página acessível. ⏳ Números a extrair dos PDFs |
| Azul RI · Planilha de Fundamentos | Séries históricas operacionais e financeiras | Tendências para calibração | ⚠️ Arquivo não listado na página; usar o link da home do RI |
| Página pública do Azul Fidelidade | Níveis, acúmulo, benefícios, resgate | Regras do gerador, motor de elegibilidade e base de conhecimento do agente (RAG) | ⚠️ Bloqueada (bot). Captura manual |
| Avaliações públicas (Reclame Aqui, lojas de apps, redes sociais) | Proxy de satisfação e sinais de evasão | Pesos de atrito por aspecto; contexto do agente | ⏳ Termos de uso e forma de coleta a verificar |

### Regras de ingestão
- Estrutura: `data/raw/<fonte>/<AAAA-MM-DD>/`, imutável.
- Todo arquivo tem entrada em `manifest.json`: `source_url`, `retrieved_at`, `method` (auto | manual), `retrieved_by`, `sha256`, `licence_note`, `schema_observed`.
- Modo manual: arquivos baixados pelo navegador entram em `data/raw/_manual/` e são registrados por script (`make register-manual`). O pipeline lê só o snapshot.
- Janela de dados: definir após verificar o que a ANAC disponibiliza (meta provisória: 24 a 36 meses).
- Páginas de regras do programa: salvar HTML ou PDF com data; o RAG indexa a versão congelada.
- Avaliações: guardar apenas texto, nota e data, sem identificação do autor. Só coletar se os termos da fonte permitirem; caso contrário, usar amostra mínima curada manualmente, com a limitação declarada.

### Tarefa zero (antes de WS2)
- [ ] Abrir as 3 páginas da ANAC no navegador e registrar: colunas, período, volume, licença, periodicidade.
- [ ] Baixar e extrair do release 2T26 e dos anteriores: membros do Azul Fidelidade, faturamento do programa, yield, load factor.
- [ ] Capturar a página e o regulamento do Azul Fidelidade e **confirmar os nomes e regras dos níveis**.
- [ ] Decidir a fonte de avaliações e conferir os termos de uso.
- **DoD:** `docs/source_verification.md` preenchido para as 7 fontes.


## WS2 (acrescentar) · Mapa de calibração (`calibration_map`)

| Parâmetro do gerador | Fonte | Valor | Status |
|---|---|---|---|
| Volume de passageiros por rota e mês | ANAC · estatísticas | a extrair | ⏳ |
| Sazonalidade por rota | ANAC · estatísticas | a extrair | ⏳ |
| Distribuição de tarifa por rota e mês | ANAC · microdados de tarifas | a extrair | ⏳ |
| Taxa de atraso e cancelamento por rota/aeroporto | ANAC · histórico de voos | a extrair | ⏳ |
| Tamanho da base de membros (escala) | Azul RI · releases | a extrair | ⏳ |
| Receita do programa por membro | Azul RI · releases | a extrair | ⏳ |
| Níveis, acúmulo, expiração, resgate | Azul Fidelidade · regulamento | a capturar | ⏳ |
| Peso de cada atrito (bagagem, atraso, app, resgate) | Avaliações públicas | a medir | ⏳ |

Tudo que não vier de fonte pública (frequência individual, sensibilidade a preço, propensão a churn) é **premissa declarada**, parametrizada em `config/`.


### WS3 · Curadoria, features e camada analítica
- dbt: `curated → analytics`; features RFM, tendência de frequência, volatilidade, mix de rota/classe, share de resgate, tempo desde último contato, contagem de atritos.
- **Cuidado anti-vazamento:** *cutoff* temporal explícito; features só com informação anterior ao corte; teste automatizado que falha se uma feature usa dado futuro.
- **DoD:** contratos de dados validados em CI; dicionário gerado; DDL Snowflake equivalente.

### WS4 · Modelos de CLV e risco de evasão (com explicabilidade)

**CLV**
- Baseline estatístico: **BG/NBD + Gamma-Gamma** (horizonte 12 meses).
- Modelo ML: gradient boosting sobre features para CLV 12m.
- Comparação por: WAPE/MAE, correlação de postos (Spearman), **lift por decil**, curva de Gini/Lorenz de captura de valor.

**Churn**
- Definição operacional de evasão documentada (ex.: ausência de voo/atividade por X dias, ajustada à frequência típica do cliente — evitar rótulo único para frequentadores e eventuais).
- Baseline: regressão logística; modelo final: LightGBM; opcional: análise de sobrevivência (Cox/hazard).
- Métricas: ROC-AUC, **PR-AUC**, **Brier**, curva de calibração, lift/captura nos top 10%, custo-benefício por limiar.
- Validação **temporal** (treino em janelas passadas, teste em futuras), sem *split* aleatório.

**Explicabilidade**
- SHAP global (importância e dependência) e local (por cliente → "top 3 motivos").
- Contrafactuais simples ("se frequência voltasse a X, risco cairia Y").
- **Model card** por modelo (uso pretendido, dados, métricas, limitações, vieses).
- **Meta de rigor:** modelo final supera baseline com intervalo de confiança (bootstrap) e calibração aceitável.

### WS5 · Score de alto valor, segmentação e personas

**Score de Alto Valor (proposta de formalização)**
```
ScoreAV = 0,60 · pct(CLV_12m previsto)
        + 0,20 · pct(RFM composto)            # recência, frequência, monetário
        + 0,20 · pct(Potencial futuro)         # crescimento previsto, headroom de share of wallet
Alto valor = ScoreAV no topo X% (X definido por análise de Pareto e de concentração de receita)

Valor em Risco = CLV_12m × P(evasão_12m)       # prioridade de retenção
```
- Pesos e corte com **análise de sensibilidade** (estabilidade do ranking e do conjunto "alto valor").

**Segmentação orientada por dados**
- Candidatos: K-Means, GMM, clustering hierárquico sobre embedding de features; escolha de K por silhouette, estabilidade (bootstrap/ARI) e interpretabilidade.
- **4 personas principais** (nomes dados *depois* do clustering, não antes) + 1 opcional. Hipóteses a verificar:

| Persona | Perfil esperado | Necessidade central |
|---|---|---|
| Executivo recorrente | Alta frequência, rotas troncais, antecedência curta, corporativo | Pontualidade, flexibilidade, reconhecimento |
| Lazer premium / planejador | Baixa frequência, alto ticket, sazonal, antecedência longa | Inspiração, valor da viagem, pacotes |
| Maximizador de milhas | Acúmulo via cartão/parceiros, sensível a resgate | Facilidade e disponibilidade de resgate |
| Regional dependente | Voa em rotas onde a Azul tem pouca ou nenhuma concorrência | Conectividade, confiança, frequência de oferta |
| *(opcional)* Ascendente | Crescimento rápido, potencial de migração de tier | Caminho claro para o próximo nível |

- Cada persona: perfil quantitativo, CLV médio, risco médio, atritos dominantes (do sentimento), ação recomendada.

### WS6 · Análise de sentimento sobre avaliações públicas
- Coleta **respeitando termos de uso**, somente texto (sem identificação de autor), amostra documentada.
- Pipeline: limpeza PT-BR → classificação de sentimento → **análise por aspecto** (atraso, bagagem, atendimento, app/check-in, resgate de milhas, preço, conforto) → agregação por tema e por período.
- Comparar ao menos 2 abordagens (ex.: modelo BERT PT-BR vs. LLM zero-shot) contra um **conjunto rotulado manualmente** (≥300 avaliações, 2 anotadores, **kappa** reportado).
- Métricas: macro-F1, matriz de confusão por aspecto.
- **Saídas:** mapa de atritos (aspecto × intensidade × tendência) → (a) calibra o gerador sintético, (b) vira contexto do agente, (c) aparece no painel.
- **DoD:** macro-F1 e kappa reportados; limitações do viés de seleção das avaliações declaradas.

### WS7 · Agente LLM de recomendação e redação
**Arquitetura**
```
Cliente (features + scores + SHAP + persona + atritos)
        │
        ▼
 [Retriever RAG] ── regulamento Azul Fidelidade (chunks com artigo/versão)
        │
        ▼
 [Motor de elegibilidade] ── regras determinísticas (tier, saldo, validade, orçamento)
        │
        ▼
 [LLM] → escolhe a Próxima Melhor Ação dentre as elegíveis + redige mensagem
        │
        ▼
 [Guardrails] → checa: oferta existe no regulamento? tom? sem dado sensível? sem promessa indevida?
        │
        ▼
 Saída estruturada (JSON): ação, justificativa, citações, mensagem, canal, nível de confiança, flag de revisão humana
```
- **Regra de ouro:** o LLM **não inventa benefícios**; só pode oferecer o que o motor de elegibilidade e o regulamento (RAG) sustentam. Citação obrigatória.
- Saída estruturada validada por schema (pydantic); *fallback* seguro quando a confiança é baixa; revisão humana para casos sensíveis.
- Transparência: cada recomendação mostra "por que este cliente / por que esta ação" (SHAP + atritos + regra).

**Avaliação do agente (diferencial de qualidade)**
- Conjunto de teste de ≥50 clientes cobrindo todas as personas e casos de borda.
- Métricas: **groundedness** (% de afirmações sustentadas pelo regulamento), **violação de política = 0**, aderência ao formato, adequação persona–ação (rubrica humana), qualidade da redação (rubrica + LLM-as-judge calibrado com humano), custo e latência por cliente.
- Testes adversariais: pedir oferta inexistente, cliente de tier errado, prompt injection em campo de texto.

### WS8 · Protótipo funcional (Streamlit)
Telas:
1. **Visão da carteira:** distribuição de CLV, concentração (Pareto), Valor em Risco total.
2. **Personas:** perfil, tamanho, CLV, risco, atritos, ação recomendada.
3. **Cliente 360:** scores, **explicação SHAP**, atritos, linha do tempo.
4. **Agente:** recomendação, mensagem redigida, citações do regulamento, botão "aprovar/editar".
5. **Mapa de atritos (sentimento):** aspectos × tendência.
6. **Simulador de impacto:** parâmetros ajustáveis (orçamento, taxa de resposta, custo por ação).
7. **IA responsável:** métricas de viés e transparência.
- **DoD:** `make app` abre sem configuração manual; roteiro de demo de 3 minutos testado; modo offline com resultados pré-computados (plano B se a API do LLM falhar).

### WS9 · Impacto e pitch
**Simulação de impacto (com premissas explícitas)**
```
ΔReceita = Σ_clientes alvo [ P(evasão evitada | ação) × CLV_12m × margem ] − custo das ações
```
- Cenários conservador/base/otimista; análise de sensibilidade (taxa de resposta, efeito da ação, custo).
- **Efeito da ação** é premissa declarada, ancorada em benchmarks citados (e, na camada 2, em simulação de uplift sobre o sintético).
- Roadmap de **piloto A/B** com dados reais: grupo de controle, métrica primária (retenção 12m de alto valor), tamanho de amostra, duração.
- Estimativa de custo do agente (tokens × clientes) e de infraestrutura.

**Pitch (5 min):** 1) paradoxo da lealdade; 2) como identificamos valor (CLV, não gasto); 3) demo: cliente em risco → explicação → mensagem; 4) impacto estimado; 5) responsabilidade/LGPD; 6) como plugar nos dados reais da Azul.

### WS10 · IA responsável e LGPD
- **Dados:** 100% sintéticos; nenhum dado pessoal real; avaliações públicas sem identificação do autor; manifestos de fonte e licença.
- **Viés:** atributos sensíveis excluídos das features; **auditoria** (fairlearn) de taxas de seleção "alto valor", de risco previsto e de ofertas recomendadas por faixa etária, gênero e região; limiares de disparidade definidos (ex.: razão de seleção) e corretivos documentados.
- **Transparência:** model cards, justificativas por recomendação, citação do regulamento.
- **LGPD aplicada ao futuro uso real:** base legal por finalidade, minimização, direito a explicação e **revisão de decisões automatizadas** (art. 20), opt-out de comunicações, retenção, humano no circuito, RIPD/DPIA simplificado em `docs/`.
- **Decisão de projeto:** rever a proposta anterior de enriquecer pessoas físicas com CPF e redes sociais. No MVP isso sai; vira "extensão futura condicionada a base legal e consentimento".

---

## 7. Playbook de retenção (persona × estado → ação)

| Persona | Risco alto + valor alto | Risco baixo + potencial | Atrito dominante → ação |
|---|---|---|---|
| Executivo recorrente | Contato proativo de relacionamento + gesto de reconhecimento | Upgrade/benefício de tier, antecipação de status | Atraso → comunicação proativa + alternativa de voo |
| Lazer premium | Oferta da rota favorita + bônus de pontos em data sazonal | Pacote/experiência no destino preferido | Preço → janela de tarifa e bônus |
| Maximizador de milhas | Bônus de pontos / facilidade de resgate | Missão de acúmulo com parceiro | Resgate difícil → oferta de resgate alternativo |
| Regional dependente | Garantia de conectividade, comunicação de confiança | Benefício por frequência | Disponibilidade de oferta → aviso antecipado e prioridade |

Toda ação tem: **custo unitário, elegibilidade (regulamento), KPI, orçamento máximo por cliente e por campanha**.

---

## 8. Metas de qualidade (propostas, a calibrar após o baseline)

| Frente | Métrica | Meta |
|---|---|---|
| CLV | Lift decil 1 vs. média; WAPE | Lift ≥ 3×; supera baseline BG/NBD |
| Churn | PR-AUC, Brier, calibração | Supera logística com IC 95%; calibração sem desvio relevante |
| Segmentação | Silhouette, estabilidade (ARI), recuperação de arquétipos | ARI de bootstrap ≥ 0,8; personas interpretáveis |
| Sentimento | Macro-F1 vs. rótulo humano, kappa | Macro-F1 ≥ 0,75; kappa ≥ 0,7 |
| Agente | Groundedness, violações, formato | ≥ 95%; 0 violações; 100% JSON válido |
| Sintético | Fidelidade vs. público | Dentro das tolerâncias definidas em todas as dimensões |
| Fairness | Disparidade entre grupos | Dentro do limiar declarado, ou corretivo documentado |
| Engenharia | Reprodutibilidade, testes | `make all` do zero; CI verde; cobertura nas partes críticas |

---

## 9. Cronograma (blocos relativos; ajustar ao prazo real)

| Bloco | Foco | Entregas-chave |
|---|---|---|
| **B0** | Fundação + WS1 | Repo, CI, ingestão com manifestos |
| **B1** | WS2 + WS3 | Base sintética + relatório de fidelidade; camadas + dicionário |
| **B2** | WS4 + WS6 (paralelo) | Baselines CLV/churn; coleta e rotulagem de avaliações |
| **B3** | WS4 final + WS5 + WS6 final | Modelos finais com SHAP; score, personas; sentimento avaliado |
| **B4** | WS7 | RAG + elegibilidade + agente + avaliação |
| **B5** | WS8 + WS10 | App integrado; auditoria de viés; model cards |
| **B6** | WS9 + ensaio | Simulação de impacto, pitch, ensaio, vídeo de backup |

**Caminho crítico:** WS2 → WS3 → WS4 → WS5 → WS7 → WS8. WS6 corre em paralelo e realimenta WS2 e WS7.
**Regra:** congelar escopo no início de B5; só polimento depois.

---

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Sintético "fácil demais" (modelos perfeitos, pouco crível) | Ruído, heterogeneidade, hazard com múltiplos fatores, validação temporal, honestidade nas métricas |
| Fontes públicas indisponíveis ou com licença restrita | Manifesto de licença, fontes alternativas, amostras mínimas |
| Avaliações com termos de uso restritivos | Preferir bases já públicas/abertas ou amostra mínima e documentada |
| LLM alucinando benefícios | Elegibilidade determinística + RAG com citação + guardrails + testes adversariais |
| Falha de API/rede na demo | Modo offline com resultados pré-computados + vídeo de backup |
| Escopo excessivo | Camada 1 obrigatória congelada; camada 2 (uplift) só se sobrar tempo |
| Viés na segmentação | Auditoria desde B3, não só no final |
| ANAC e página do programa bloqueiam coleta automática | Modo snapshot manual com manifesto; verificação na tarefa zero |
| Regras do programa mudam depois da captura | Versão e data em cada citação do agente; reindexação por `make rag` |
| Termos de uso das plataformas de avaliação restringem coleta | Verificar antes; fallback para amostra curada manualmente |
| Dados da ANAC com defasagem ou lacunas por rota | Calibrar por rota de maior volume e declarar cobertura |


---

## 11. Escopo em camadas

- **Camada 1 (obrigatória, define o 10):** WS0–WS10 como descritos, exceto uplift.
- **Camada 2 (diferencial):** uplift modeling; otimização de orçamento por programação linear; avaliação do agente com mais cenários; tema de "programa como API para agentes" no roadmap.

---

## 12. Checklist final de entrega (gate de 10/10)

- [ ] `make all` reproduz tudo do zero, em máquina limpa
- [ ] Camadas bruta/tratada/analítica em Parquet, separadas por código e por pasta
- [ ] Dicionário de dados gerado dos schemas; contratos validados em CI
- [ ] Relatório de fidelidade do sintético com mapa parâmetro → fonte
- [ ] CLV e churn com baseline, métricas, calibração, SHAP e model card
- [ ] Definição formal de alto valor + análise de sensibilidade
- [ ] 4 personas com perfil quantitativo e playbook de ação
- [ ] Sentimento com conjunto rotulado, macro-F1 e kappa
- [ ] Agente com RAG, elegibilidade, guardrails e relatório de avaliação
- [ ] Protótipo com roteiro de demo e modo offline
- [ ] Auditoria de viés, política de IA responsável, RIPD simplificado
- [ ] Simulação de impacto com cenários e plano de piloto
- [ ] Scripts Snowflake (DDL/carga) e plano de troca para dados reais
- [ ] Pitch de 5 min ensaiado + vídeo de backup
- [ ] Correções do relatório anterior aplicadas (ex.: inconsistência de percentuais de adesão entre gerações; nomenclatura de tiers verificada)
- [ ] `docs/source_verification.md` com as 7 fontes
- [ ] `calibration_map` 100% preenchido, sem valores sem fonte
- [ ] Snapshots manuais registrados com hash e data
---

## 13. Decisões em aberto (responder para fechar o cronograma)

1. **Prazo e tamanho do time:** ___ dias · ___ pessoas
2. **LLM do agente:** (a) API de LLM comercial · (b) modelo open-source local · (c) ambos, com comparação
3. **Orquestração:** (a) apenas Makefile · (b) Prefect/Dagster
4. **Sentimento:** (a) BERT PT-BR fine-tuned · (b) LLM zero-shot · (c) comparar os dois
5. **Camada 2 (uplift):** (a) incluir · (b) só se houver folga · (c) fora