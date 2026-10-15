# Análise Exploratória e Perfilamento do Dataset Airline_review.csv
**Projeto Aura 2.0 — Detecção de Atritos para Retenção de Clientes**  
**Responsável:** data-analyst  
**Data:** 14/10/2026  

---

## 1. Visão Geral e Dimensões do Arquivo
- **Caminho:** `data/raw/Airline_review.csv`
- **Tamanho do Arquivo:** 20.539.187 bytes (~19,59 MB / 20,54 MB decimal)
- **Total de Linhas:** 23.171 registros
- **Total de Colunas:** 20 variáveis
- **Duplicatas de Conteúdo:** 120 registros duplicados (desconsiderando a coluna `Unnamed: 0`)
- **Período Temporal das Avaliações:** 2002 a 2023 (pico concentrado entre 2018 e 2023)
- **Datas dos Voos (`Date Flown`):** ~2014 a 2023

---

## 2. Dicionário de Dados, Tipos Inferidos e Qualidade (Missing Values)

| Coluna | Tipo Inferido | Nulos (Absoluto) | Nulos (%) | Únicos | Descrição e Observações |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Unnamed: 0` | int64 | 0 | 0.00% | 23.171 | Índice sequencial da raspagem original. |
| `Airline Name` | string | 0 | 0.00% | 497 | Nome da companhia aérea. Teto de amostragem de até 100 reviews por empresa. |
| `Overall_Rating` | object / categórico | 0 | 0.00% | 10 | Notas de 1 a 9 e valor `'n'` (842 casos, 3,63% sem nota). **Nota 10 ausente por truncamento**. |
| `Review_Title` | string | 0 | 0.00% | 17.219 | Título da avaliação atribuído pelo passageiro. |
| `Review Date` | string / data | 0 | 0.00% | 4.557 | Data de postagem (formato: "DDth Month YYYY"). |
| `Verified` | bool | 0 | 0.00% | 2 | Confirmação de voo verificado (True: 52,73%, False: 47,27%). |
| `Review` | string / texto | 0 | 0.00% | 23.046 | Comentário aberto e detalhado do passageiro. |
| `Aircraft` | string | 16.042 | 69.23% | 1.048 | Modelo da aeronave utilizada (alta taxa de ausência). |
| `Type Of Traveller` | categórico | 3.738 | 16.13% | 4 | 'Solo Leisure', 'Couple Leisure', 'Family Leisure', 'Business'. |
| `Seat Type` | categórico | 1.096 | 4.73% | 4 | 'Economy Class', 'Business Class', 'Premium Economy', 'First Class'. |
| `Route` | string | 3.828 | 16.52% | 13.607 | Origem, conexões e destino informados. |
| `Date Flown` | string / data | 3.754 | 16.20% | 109 | Mês e ano da viagem realizada (ex: "November 2019"). |
| `Seat Comfort` | float64 | 4.155 | 17.93% | 6 | Escala numérica de 1.0 a 5.0 (contém 144 zeros como N/A). |
| `Cabin Staff Service`| float64 | 4.260 | 18.39% | 6 | Escala de 1.0 a 5.0 (contém 130 zeros como N/A). |
| `Food & Beverages` | float64 | 8.671 | 37.42% | 6 | Escala de 1.0 a 5.0 (contém 252 zeros como N/A). |
| `Ground Service` | float64 | 4.793 | 20.69% | 5 | Escala de 1.0 a 5.0 (51,55% dos valores válidos são nota 1.0). |
| `Inflight Entertainment`| float64 | 12.342 | 53.26% | 6 | Escala de 1.0 a 5.0 (alta taxa de ausência). |
| `Wifi & Connectivity`| float64 | 17.251 | 74.45% | 6 | Escala de 1.0 a 5.0 (alta taxa de ausência). |
| `Value For Money` | float64 | 1.066 | 4.60% | 6 | Escala de 1.0 a 5.0 (45,85% dos válidos são nota 1.0). |
| `Recommended` | categórico | 0 | 0.00% | 2 | Recomendação binária: `'no'` (66,31%) vs `'yes'` (33,69%). |

---

## 3. Presença de Companhias Aéreas e Contexto Brasileiro
1. **Estrutura Amostral:**
   - 497 companhias aéreas globais.
   - O processo de raspagem aplicou um teto de 100 avaliações por companhia aérea: 155 operadoras têm exatamente 100 avaliações (incluindo gigantes globais como Emirates, Delta, British Airways, Air France, e as latinas LATAM e TAM).
2. **Presença da Azul e Companhias Brasileiras:**
   - **`Azul Linhas Aéreas` NÃO está presente no cadastro de companhias** (`Airline Name` = 0).
   - **`GOL Linhas Aéreas` NÃO está presente** (`Airline Name` = 0).
   - **`Voepass / Passaredo` NÃO está presente** (`Airline Name` = 0).
   - As únicas companhias de aviação comercial brasileira/sul-americana com presença como operadoras catalogadas são:
     - `TAM Airlines`: 100 avaliações.
     - `LATAM Airlines`: 100 avaliações.
     - `Avianca`: 100 avaliações.
3. **Menção Qualitativa à 'Azul':**
   - Há **exatamente 1 menção** à palavra "Azul" em todo o dataset (linha 19.676).
   - Contexto: Uma avaliação de nota 1 para a **TAM Airlines** na rota Curitiba (CWB) -> São Paulo (GRU).
   - O cliente relata extremo descontentamento com o suporte da fusão TAM/LAN e conclui:
     > *"No question every new booking in Brasil will be with Azul, which is easy, comfortable, user friendly and is the jetBlue of Brasil."*
   - Essa evidência isolada valida que a marca Azul já possuía forte apelo de qualidade e simplicidade operacional no mercado doméstico frente à TAM/LATAM.
4. **Rotas e Aeroportos Brasileiros:**
   - Foram identificadas **175 avaliações** com rotas no Brasil (mencionando GRU, GIG, CWB, SSA, REC, BSB, POA, São Paulo, Rio de Janeiro, etc.).
   - Principais operadoras dessas rotas: TAM Airlines (39), LATAM Airlines (26), Avianca (16), Copa Airlines (15), TAAG Angola (9), Aerolineas Argentinas (8), TAP Portugal (6), Alitalia (6).

---

## 4. Análise de Distribuição dos Ratings e Descoberta Crítica de Integridade

### 4.1. Distribuição Geral
- **Recomendação (`Recommended`):**
  - **`no`**: 15.364 (66,31%)
  - **`yes`**: 7.807 (33,69%)
  - Viés típico de plataformas espontâneas de review (Skytrax), onde clientes que vivenciaram atrito severo têm maior motivação para registrar reclamações.
- **Notas Brutas (`Overall_Rating`):**
  - Nota 1: 11.595 (50,04%)
  - Nota 2: 2.296 (9,91%)
  - Nota 3: 1.356 (5,85%)
  - Nota 4: 859 (3,71%)
  - Nota 5: 830 (3,58%)
  - Nota 6: 675 (2,91%)
  - Nota 7: 1.193 (5,15%)
  - Nota 8: 1.757 (7,58%)
  - Nota 9: 1.768 (7,63%)
  - Nota 'n' (ausente): 842 (3,63%)
  - Nota média bruta ingênua: 3,14 / 9.

### 4.2. Descoberta Crítica: Truncamento de Notas 10 para 1
- **Investigação da Anomalia:** Observou-se que não existia nenhuma nota 10 no dataset e que, no grupo `Overall_Rating == '1'`, havia **2.268 registros com `Recommended == 'yes'`**.
- **Comportamento das Sub-Notas desse grupo:**
  - `Value For Money`: média de 4,68 / 5,0
  - `Cabin Staff Service`: média de 4,86 / 5,0
  - `Seat Comfort`: média de 4,56 / 5,0
  - Títulos associados: *"Flight was very comfortable"*, *"nice and comfortable flights"*, *"Clean and fresh aircraft"*, etc.
- **Diagnóstico:** O crawler/raspador de dados extraiu apenas o primeiro dígito textual do score (ex: `rating[:1]` ou regex `\d`), transformando todas as avaliações com nota **10** em **1**.
- **Impacto Analítico:**
  - Notas 1 reais: **9.327** avaliações (40,25% do dataset).
  - Notas 10 reais (mascaradas como 1): **2.268** avaliações (9,79% do dataset).
  - **Média real ajustada:** Eleva-se de 3,14 para **4,05 / 10**.

---

## 5. Mapeamento de Atritos e Drivers de Detração (Foco no Projeto Aura)

### 5.1. Correlação dos Sub-Serviços com a Recomendação do Cliente
| Atributo | Correlação com `Recommended` | Correlação com `Overall_Rating` | % Avaliado como Nota 1.0 |
| :--- | :--- | :--- | :--- |
| **Value For Money** | **0,837** | 0,602 | 45,85% |
| **Ground Service** | **0,801** | 0,558 | 51,55% |
| **Cabin Staff Service** | **0,716** | 0,506 | 31,57% |
| **Seat Comfort** | **0,708** | 0,471 | 33,32% |
| **Food & Beverages** | **0,707** | 0,422 | 36,43% |
| **Wifi & Connectivity** | **0,656** | 0,353 | 68,60% |
| **Inflight Entertainment**| **0,529** | 0,298 | 44,74% |

*Insight:* O serviço de solo (`Ground Service`) e a percepção de custo-benefício (`Value For Money`) são os maiores determinantes da retenção ou rejeição do cliente. O entretenimento a bordo e o Wi-Fi têm papel secundário comparados à integridade operacional do voo e do solo.

### 5.2. Prevalência de Queixas em Avaliações Negativas (Notas 1 a 3 Reais)
- **Atrasos e Cancelamentos:** Presentes em **52,11%** das avaliações negativas vs 27,55% das positivas (+24,55 p.p. de gap).
- **Reembolso, Taxas e Cobranças Extras:** Presentes em **47,14%** das negativas vs 27,68% das positivas (+19,46 p.p.).
- **Atendimento Hostil / Descaso da Equipe:** Presente em **15,89%** das negativas vs 2,59% das positivas (+13,30 p.p. — incidência 6 vezes maior).
- **Check-in, Filas e Portão de Embarque:** 75,49% das negativas mencionam fricções de embarque/fila.
- **Extravio e Problemas com Bagagem:** Presente em 29,19% das negativas.

---

## 6. Conclusões e Recomendações Estratégicas para o Projeto Aura 2.0
1. **Papel do Dataset no Projeto:**
   - Este arquivo funciona perfeitamente como um **benchmark global de taxonomia de atrito** (churn signals) e um corpus rico em língua inglesa para treinar e calibrar modelos de análise de sentimento e classificação de dores do passageiro.
2. **Limitação para Métricas Específicas da Azul:**
   - O dataset **NÃO reflete as métricas operacionais domésticas da Azul Linhas Aéreas** (ausente como operadora) nem do mercado brasileiro (apenas 175 voos identificados).
   - Conclusão: Para o Projeto Aura 2.0 gerar inteligência competitiva e operacional sobre a Azul, **é obrigatório integrar este benchmark com os dados oficiais da ANAC** (já disponíveis em `data/curated/anac/` e `data/raw/anac/`) e fontes de reclamação do consumidor brasileiro (Reclame Aqui / Consumidor.gov).
3. **Tratamento de Dados na Camada Curated:**
   - É mandatório corrigir a variável `Overall_Rating` nos pipelines de engenharia de dados (ex: `data/curated/benchmarks/airline_reviews.parquet`), ajustando os 2.268 registros truncados para a nota 10 correta, evitando que algoritmos de machine learning aprendam relações espúrias entre sentimentos extremamente positivos e a nota 1.
