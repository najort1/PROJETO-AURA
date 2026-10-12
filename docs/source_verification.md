# Projeto Aura 2.0 — Verificação de Fontes Públicas e Trilha de Evidências (§WS1)

> **Data de verificação:** 12 de outubro de 2026  
> **Responsável:** Especialista em Ingestão e Governança de Dados (Workstream WS1)  
> **Status:** Verificado e consolidado para reprodução determinística  
> **Princípio orientador:** Honestidade metodológica e anti-alucinação — distinção rigorosa entre dados públicos medidos, fatos verificados por pesquisa, corpus sintético e premissas declaradas.

---

## 1. Matriz Consolidada de Verificação das 7 Fontes (§WS1)

| # | Fonte | O que valida no Projeto | Status | Evidência / URL / Limitação |
|---|---|---|---|---|---|
| **1** | **Microdados ANAC locais** (`voos_basica`, `movimentacao`, `aeroportos`) | Malha de rotas regulares, passageiros pagos, sazonalidade mensal, market share e taxa de atraso operacional | **Verificado (local)** | 723 arquivos locais (3,16 GB) em `data/raw/anac/` com hashes registrados em `data/manifests/anac.json`. Janelas: voos até 2026-08; movimentação até 2025-12. |
| **2** | **ANAC · Microdados de tarifas aéreas comercializadas** | Distribuição de tarifas efetivamente pagas por rota e dispersão de preço | **Bloqueado (externo)** | Portal de Dados Abertos da ANAC protegido por desafio de segurança (CAPTCHA / Cloudflare). **Fallback:** premissa calibrada em `config/generator.yaml` baseada em distância em km da rota. |
| **3** | **Azul S.A. — Relações com Investidores & SEC** | Escala da base de clientes (membros totais e membros ativos mensais / MAU) | **Verificado (pesquisa)** | 20.100.000 membros em 31/12/2025 (SEC Form 20-F arquivado em 2026); ~1.400.000 MAU (Apresentações RI 2025). Versionado em `config/program_rules.yaml` (`scale_facts`). |
| **4** | **Página Oficial e Regulamento Azul Fidelidade** | Níveis do programa, regras de qualificação, acúmulo por R$, validade de pontos, tetos de resgate e beneficiários | **Parcial / Provisional** | Captura direta do domínio `voeazul.com.br` bloqueada por WAF Akamai (HTTP 403 Forbidden). **Snapshot provisional:** compilado via pesquisa web estruturada em `config/program_rules.yaml`. |
| **5** | **Avaliações Públicas (Reclame Aqui / Google Play)** | Atritos percebidos por aspecto (atraso, bagagem, app, resgate, preço) e sentimento | **Decisão Declarada: Corpus Sintético** | Raspagem direta restrita por Termos de Uso das plataformas e LGPD (dados de terceiros). **Decisão:** geração de corpus sintético rotulado de 1.200 avaliações (`ml/sentiment`, WS6) para validação do pipeline. |
| **6** | **Licença dos Dados Abertos da ANAC** | Conformidade jurídica de reutilização e governança de dados | **Verificado (pesquisa)** | Portal da ANAC declara licença **Creative Commons Atribuição-SemDerivações 3.0 Não Adaptada (CC BY-ND 3.0)**. Fundamento: Decreto nº 8.777/2016 e Lei nº 12.527/2011. Uso restrito a agregados analíticos. |
| **7** | **Frota e Aeronaves ANAC (Registro Aeronáutico Brasileiro - RAB)** | Cadastro oficial de aeronaves civis brasileiras, operadores e capacidades | **Verificado (local)** | Arquivo `data/raw/anac/aeronaves/aeronaves_rab.parquet` (35.024 aeronaves registradas). |

---

## 2. Detalhamento e Trilha de Verificação por Fonte

### Fonte 1: Microdados ANAC Locais
- **Localização:** `data/raw/anac/` (imutável, 723 arquivos, 3.16 GB, hash SHA-256 de cada arquivo em `data/manifests/anac.json`).
- **Cobertura observada por conjunto:**
  - `voos_basica`: 319 arquivos mensais (`voos_basica_200001.parquet` a `voos_basica_202608.parquet`). Janela de 2000-01 a 2026-08.
  - `voos_combinada`: 319 arquivos mensais (`voos_combinada_200001.parquet` a `voos_combinada_202608.parquet`). Janela de 2000-01 a 2026-08.
  - `movimentacao`: 82 arquivos mensais (`movimentacao_201903.parquet` a `movimentacao_202512.parquet`). Janela de 2019-03 a 2025-12.
  - `aeroportos`: 1 arquivo (`aerodromos.parquet`), com 4.420 registros brutos e 4.394 aeródromos únicos.
  - `aeronaves`: 1 arquivo (`aeronaves_rab.parquet`), com 35.024 registros.
- **Janela de referência adotada pelo pipeline:** 36 meses, de setembro de 2023 a agosto de 2026 (`2023-09` a `2026-08`), conforme `config/settings.yaml`.
- **Classificadores investigados e validados:**
  - Mercado doméstico de passageiros regular: `cd_tipo_linha = 'N'` e `cd_di IN ('0', '4')` (`ds_grupo_di = 'REGULAR'`).
  - Total de passageiros pagos computados no período: 287.749.212 passageiros em 1.771 rotas.
  - Presença da Azul (`sg_empresa_icao = 'AZU'`): 85.600.440 passageiros em 1.097 rotas (market share de 29,75%).

### Fonte 2: Microdados de Tarifas Aéreas Comercializadas (ANAC)
- **Status da coleta:** Bloqueado por CAPTCHA nesta sessão.
- **Diagnóstico técnico:** Os endpoints e páginas de download de tarifas aéreas no Portal de Dados Abertos da ANAC exigem resolução interativa de CAPTCHA e validação de token do navegador, impedindo requisições automatizadas sem intervenção humana.
- **Protocolo de fallback:** A distribuição de preços não é inventada. Conforme documentado no [mapa de calibração](config/calibration_map.yaml), a precificação é parametrizada em `config/generator.yaml` (bloco `pricing`), derivando tarifas médias em função das distâncias reais em km das rotas operadas registradas em `voos_basica`, com dispersão estatística calibrada.

### Fonte 3: Azul S.A. — Relações com Investidores e SEC
- **Status:** Verificado por pesquisa em fontes corporativas oficiais.
- **Evidências auditadas:**
  1. **Base total de membros:** 20.100.000 clientes cadastrados no Azul Fidelidade em 31/12/2025.
     - *Fonte:* Arquivamento oficial na U.S. Securities and Exchange Commission (SEC), Form 20-F da Azul S.A. (exercício fiscal de 2025): [SEC EDGAR - Azul 2025](https://www.sec.gov/Archives/edgar/data/1432364/000162828026023423/azul-20251231.htm).
  2. **Membros ativos por mês (MAU):** ~1.400.000 membros com atividade mensal regular.
     - *Fonte:* Apresentações institucionais de Resultados do 4T25 e Relatório da Administração disponíveis no portal de RI da Azul: [Azul RI](https://ri.voeazul.com.br).
- **Incorporação:** Registrado formalmente em `config/program_rules.yaml` (`scale_facts`) e consumido em `config/calibration_map.yaml`.

### Fonte 4: Página Oficial e Regulamento do Azul Fidelidade
- **Status:** Bloqueio direto por WAF (HTTP 403 Forbidden); snapshot provisional estruturado via pesquisa.
- **Diagnóstico técnico:** A tentativa de coleta via HTTP direta sobre as URLs oficiais (`https://www.voeazul.com.br/br/pt/programa-fidelidade`) resulta em resposta HTTP 403 Forbidden emitida pela camada Akamai Edge Shield.
- **Mitigação adotada:** Snapshot provisional estruturado compilado em 12/10/2026 e versionado em `config/program_rules.yaml` (`snapshot_version: research-2026-10-12`). Regras documentadas:
  - 4 níveis ordinais: `Azul` (básico), `Topázio` (6.000 pts / 6 trechos), `Safira` (10.000 pts / 10 trechos), `Diamante` (20.000 pts / 20 trechos).
  - Nível de relacionamento exclusivo: `Azul One` (convite nominal anual).
  - Acúmulo por R$ em tarifa aérea: 1x (Azul), 2x (Topázio), 3x (Safira), 4x (Diamante).
  - Validade dos pontos: 2 anos (Azul), 3 anos (Topázio), 4 anos (Safira) e sem expiração (Diamante).
  - Tetos de resgate e beneficiários: 5 (Azul), 6 (Topázio), 8 (Safira), 10 (Diamante).
- **Fail-safe:** Regras que não puderam ser verificadas com 100% de certeza são preenchidas como `null`, instruindo o motor de elegibilidade a rejeitar a concessão automática (fail-safe) e solicitar revisão humana.

### Fonte 5: Avaliações Públicas e Menções de Atrito
- **Status:** Decisão metodológica declarada — corpus sintético rotulado por aspecto.
- **Justificativa jurídica e técnica:**
  1. As plataformas públicas de avaliação (Reclame Aqui, Google Play Store, TripAdvisor) possuem Termos de Serviço que vedam web scraping não autorizado e redistribuição de dados.
  2. A Lei Geral de Proteção de Dados Pessoais (LGPD, Lei nº 13.709/2018) proíbe a raspagem de identificadores e dados de terceiros sem base legal e governança documentada.
- **Decisão:** Conforme aprovado no plano mestre (§WS1 e §WS6), construiu-se um corpus sintético controlado de 1.200 avaliações rotuladas por aspecto em `ml/sentiment/`, permitindo validar o pipeline de classificação, cálculo de kappa inter-anotadores e geração do mapa de atritos (`schemas/friction_map.yaml`) sem violação de termos de uso nem exposição de privacidade.

### Fonte 6: Licença e Termos de Uso dos Dados Abertos da ANAC
- **Status:** Verificado por pesquisa em portais governamentais oficiais.
- **Evidências coletadas:**
  - O Portal de Dados Abertos da ANAC ([https://dados.gov.br](https://dados.gov.br) e [Portal ANAC](https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos)) informa formalmente a licença **Creative Commons Atribuição-SemDerivações 3.0 Não Adaptada (CC BY-ND 3.0)** para os conteúdos publicados.
  - A Política de Dados Abertos do Poder Executivo federal é regulamentada pelo **Decreto nº 8.777/2016** (alterado pelo Decreto nº 9.903/2019) e pela **Lei de Acesso à Informação (Lei nº 12.527/2011)**.
  - O uso dos microdados no Projeto Aura é restrito à **derivação de agregados estatísticos** e parametrização do gerador sintético, em estrita conformidade com a política pública de transparência ativa, com citação explícita da fonte governamental e sem redistribuição comercial dos microdados brutos.

### Fonte 7: Frota e Aeronaves ANAC (Registro Aeronáutico Brasileiro - RAB)
- **Status:** Verificado (local).
- **Evidências:**
  - Arquivo local: `data/raw/anac/aeronaves/aeronaves_rab.parquet`.
  - Contém 35.024 aeronaves com dados de marcas, modelos, fabricantes, capacidades de passageiros (`nr_passageiros_max`), assentos (`nr_assentos`) e operadores (`operadores`).
  - Utilizado como referência de catálogo de equipamentos da aviação brasileira.

---

## 3. Resumo de Governança para o Tech Lead

1. **Reprodutibilidade:** Toda a transformação sobre os microdados ANAC é 100% determinística via DuckDB em `ingestion/curate.py`.
2. **Imutabilidade da Camada Bruta:** A pasta `data/raw/` permanece intocada após o registro inicial; todas as saídas derivam exclusivamente para `data/curated/`.
3. **Contratos e Schemas:** As três tabelas curadas geradas possuem contratos YAML estritos em `schemas/` e passam por validação `validate_or_raise` a cada execução.
4. **Ausência de Alucinações:** Limitações de fontes (CAPTCHA em tarifas, ausência de identificador de aeroporto em `movimentacao` e ausência de cancelamentos em `voos_basica`) foram explicitamente auditadas e declaradas, sem criação artificial de dados.
