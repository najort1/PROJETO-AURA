# Roteiro de Demonstração em 3 Minutos — Projeto Aura 2.0

> **Objetivo:** Contar a história ponta a ponta do Aura 2.0 em exatamente 3 minutos:  
> **Carteira → Segmentos → Cliente 360 → Explicabilidade SHAP → Agente com Citações → Atritos → Simulação de ROI → Governança LGPD.**  
> **Aviso obrigatório presente em todas as telas:** *"DADOS SINTÉTICOS · BASE ANALÍTICA v3"*.

---

## Cronômetro da Demonstração (0:00 a 3:00)

| Tempo | Tela / Módulo | Foco da Ação | Mensagem Central |
|---|---|---|---|
| **0:00 – 0:30** | **01 · Visão da Carteira** | KPIs gerais (50k) + Pareto / Gini | Paradoxo da lealdade: Valor em Risco (CLV × Churn) |
| **0:30 – 0:55** | **02 · Personas** | Cards dos 6 arquétipos reais | Segmentação orientada a valor e playbooks específicos |
| **0:55 – 1:30** | **03 · Cliente 360** | Seletor + SHAP + Linha do tempo | Explicabilidade local: por que este cliente corre risco |
| **1:30 – 2:05** | **04 · Agente de Retenção** | Recomendação + Citação + Aprovação | RAG no regulamento (zero alucinação) + HITL funcional |
| **2:05 – 2:25** | **05 · Mapa de Atritos** | Barras de intensidade + Tendência temporal | Sentimento por aspecto alimenta o pipeline |
| **2:25 – 2:45** | **06 · Simulador de Impacto** | Sliders interativos + Cenários | Recálculo dinâmico sobre a carteira real sob premissas |
| **2:45 – 3:00** | **07 · IA Responsável** | Four-Fifths Rule + LGPD Art. 20 | Equidade auditada (9/14 conformes), dados 100% sintéticos |

---

## Roteiro Ponto a Ponto (Tela → Ação → Fala)

### 1. Visão da Carteira (0:00 – 0:30)
* **Tela:** `01 · Visão da Carteira` (`http://localhost:8501/carteira`)
* **Ação visual:**
  1. Apontar o banner permanente no topo: *"DADOS SINTÉTICOS · BASE ANALÍTICA v3"*.
  2. Destacar os KPI Cards da base real:
     - **Tamanho da Carteira:** 50.000 clientes
     - **CLV 12M Total Previsto:** R$ 39.554.463,12 (média: R$ 791,09/cliente)
     - **Valor em Risco Total:** R$ 8.305.496,50 (21,0% do CLV total da carteira)
     - **Segmento Alto Valor:** 10,01% (5.005 clientes prioritários)
  3. Rolar suavemente para a Curva de Lorenz/Pareto mostrando a concentração da receita (Gini = 0,55, com top 20% concentrando ~64,2% do CLV).
* **Fala do Apresentador:**
  > *"Olá a todos. Este é o Aura 2.0, o pipeline reproduzível de inteligência de clientes e retenção do Azul Fidelidade.
  > Todas as métricas que veremos operam sobre uma base de 50.000 clientes 100% sintéticos calibrada com microdados públicos da ANAC.
  > Começamos pela Visão da Carteira. O problema central que resolvemos é o paradoxo da lealdade: não retemos apenas quem tem alta probabilidade de sair, mas quem tem **Valor em Risco**, ou seja, o produto do CLV previsto pela probabilidade de churn.
  > Em nossa carteira de 50 mil membros, temos R$ 39,55 milhões de CLV previsto e R$ 8,30 milhões em risco imediato de perda.
  > Na curva de Pareto à direita, vemos que os 20% superiores da base concentram mais de 64% do valor total da carteira. Proteger esses clientes é a prioridade número um."*

---

### 2. Personas e Playbook (0:30 – 0:55)
* **Tela:** `02 · Personas` (`http://localhost:8501/personas`)
* **Ação visual:**
  1. Clicar no menu lateral em `02 · Personas`.
  2. Mostrar os cartões das 6 personas reais com suas respectivas participações de mercado:
     - *Eventual Promocional* (48,42% · 24.210 membros · CLV médio R$ 209,11 · Churn 73,6%)
     - *Regional Dependente* (19,53% · 9.763 membros · CLV médio R$ 888,16 · Churn 33,0%)
     - *Eventual Ascendente* (10,24% · 5.121 membros · CLV médio R$ 2.155,46 · Churn 18,2%)
     - *Maximizador de Milhas* (9,90% · 4.949 membros · CLV médio R$ 477,32 · Churn 22,0%)
     - *Lazer Premium* (9,29% · 4.645 membros · CLV médio R$ 831,52 · Churn 29,8%)
     - *Executivo Recorrente* (2,62% · 1.312 membros · CLV médio R$ 6.522,82 · Churn 2,6%)
  3. Apontar a linha de ação recomendada e atritos dominantes em cada card.
* **Fala do Apresentador:**
  > *"Em vez de clusters genéricos, o Aura classifica a carteira em 6 personas comportamentais reais.
  > A base volumosa concentra-se no Eventual Promocional, com 48,4% dos clientes e churn elevado de 73,6%.
  > No outro extremo, o Executivo Recorrente representa apenas 2,62% da base, mas ostenta o maior CLV médio (R$ 6.522) e voa com frequência em rotas troncais.
  > Para o Regional Dependente (19,53%), a dependência de conexões regionais torna o atrito de pontualidade crítico.
  > Cada persona possui playbooks específicos de retenção e regras determinísticas de elegibilidade."*

---

### 3. Cliente 360 e Explicabilidade SHAP (0:55 – 1:30)
* **Tela:** `03 · Cliente 360` (`http://localhost:8501/cliente-360`)
* **Ação visual:**
  1. Abrir o seletor de clientes ordenado por *Maior Valor em Risco*.
  2. Selecionar o cliente número 1 em risco da carteira real: **C038454** (Topázio · Eventual Ascendente).
  3. Apontar o badge de categoria Topázio e a tag ★ ALTO VALOR.
  4. Mostrar as métricas individuais: CLV 12M de R$ 3.868,54, P(Churn) de 76,4% e Valor em Risco de R$ 2.955,56.
  5. Rolar para o gráfico de barras horizontais de **Explicabilidade SHAP do CLV** e a **Linha do Tempo de Relacionamento**.
* **Fala do Apresentador:**
  > *"Ao descermos para o nível individual no Cliente 360, inspecionamos o cliente C038454, o maior Valor em Risco da carteira real: R$ 2.955,56 em risco com CLV de R$ 3.868,54 e probabilidade de churn de 76,4%.
  > Mas nós não operamos como uma caixa-preta.
  > O gráfico SHAP à esquerda decompõe exatamente o que levou o modelo a prever esse valor de vida: o nível Topázio agrega +R$ 3.333, o ticket médio elevado por voo agrega +R$ 512 e os pontos qualificáveis agregam +R$ 346.
  > Na linha do tempo à direita, vemos o histórico real sem qualquer vazamento pós-cutoff: 4 eventos registrados até maio de 2025, incluindo um voo com atraso operacional de 23 minutos em 07/04/2025 que gerou atrito registrado no app com NPS baixo."*

---

### 4. Agente Especialista e Humano no Circuito (1:30 – 2:05)
* **Tela:** `04 · Agente de Retenção` (`http://localhost:8501/agente`)
* **Ação visual:**
  1. Clicar em `04 · Agente de Retenção` (o cliente C038454 permanece selecionado no `session_state`).
  2. Mostrar a ação recomendada: `ACT-ATRATRIBUI-ATRASO` (`reencaminhamento_atraso`) via canal WhatsApp.
  3. Apontar a mensagem gerada: *'Sabemos que pontualidade é essencial para você e lamentamos eventuais atritos com atrasos em sua programação recente...'*.
  4. Para demonstrar citação regulatória formal, selecionar o cliente `C030743` (ação `ACT-ANTECIPACAO-NIVEL`), exibindo a citação auditável com `fact_id: AF-TIER-TOPAZIO` do regulamento oficial (snapshot `research-2026-10-12`).
  5. Clicar no botão **Editar Mensagem**, ajustar um trecho do texto e clicar em **💾 Salvar Alterações e Aprovar**.
  6. Apontar a confirmação de gravação auditável no arquivo `data/analytics/decisions.jsonl`.
* **Fala do Apresentador:**
  > *"Aqui vemos o Agente de Retenção em ação.
  > A regra de ouro do Aura: o agente **não alucina benefícios**. Ele só oferece ações elegíveis sustentadas pelo regulamento oficial do Azul Fidelidade.
  > Para o cliente C038454, o motor identificou o atrito de atraso recente e acionou a ação de reencaminhamento com pedido de desculpas via WhatsApp.
  > Em ofertas de benefício de programa — como vemos no cliente C030743 com antecipação de nível —, o agente anexa citações formais do regulamento oficial, com fact_id auditável e regras vigentes do snapshot homologado.
  > Como operador humano, posso revisar a mensagem, clicar em 'Editar', refinar a abordagem e aprovar.
  > A decisão é imediatamente gravada no arquivo imutável decisions.jsonl para estrita auditoria de governança."*

---

### 5. Mapa de Atritos e Sentimento (2:05 – 2:25)
* **Tela:** `05 · Mapa de Atritos` (`http://localhost:8501/atritos`)
* **Ação visual:**
  1. Acessar `05 · Mapa de Atritos`.
  2. Apontar as métricas gerais do arquivo `friction_map.parquet` (49 linhas cobrindo 7 semestres e 7 aspectos).
  3. Mostrar a tabela com os pesos calibrados dos aspectos no score de atrito:
     - Atraso de Voo: 0,1965 (19,65%)
     - Atendimento: 0,1770 (17,70%)
     - Bagagem / Extravio: 0,1666 (16,66%)
     - Resgate de Milhas: 0,1660 (16,60%)
     - App & Check-in: 0,1411 (14,11%)
     - Preço & Tarifas: 0,1026 (10,26%)
     - Conforto a Bordo: 0,0502 (5,02%)
  4. Apontar a nota declarando o corpus 100% sintético para respeito a LGPD e termos de uso de sites públicos.
* **Fala do Apresentador:**
  > *"O diferencial do Aura é que o sentimento das avaliações não fica isolado num dashboard. Ele retroalimenta o motor de elegibilidade e justificativa.
  > Nosso mapa de atritos monitora 49 combinações de aspectos e semestres.
  > Atraso de voo é o fator com maior peso relativo no modelo (19,65%), seguido por atendimento (17,70%) e bagagem (16,66%).
  > O corpus é 100% sintético, gerado com calibração semântica em PT-BR para total conformidade com a LGPD e termos de uso."*

---

### 6. Simulador de Impacto Interativo (2:25 – 2:45)
* **Tela:** `06 · Simulador de Impacto` (`http://localhost:8501/simulador`)
* **Ação visual:**
  1. Navegar para `06 · Simulador de Impacto`.
  2. Apontar o recálculo em tempo real sobre os 50.000 clientes reais ordenados por Valor em Risco.
  3. Clicar no chip do cenário **Base (Recomendado)**:
     - Orçamento: R$ 80.000 (custo de R$ 45,00/ação aborda 1.777 clientes prioritários, totalizando R$ 79.965,00 em custos).
     - Taxa de Resposta: 18% | Efeito da Ação: 25% | Margem: 22%.
     - Evasões evitadas: ~26,0 clientes.
     - Receita preservada bruta: R$ 8.518,12.
  4. Mover o slider de efeito ou orçamento e destacar como as premissas são transparentemente rotuladas.
* **Fala do Apresentador:**
  > *"Na tela de simulação, respondemos à pergunta executiva: 'Qual é a viabilidade financeira da estratégia de retenção?'
  > O algoritmo recalcula o retorno dinamicamente sobre a carteira de 50.000 clientes priorizados por Valor em Risco.
  > No cenário Base, com R$ 80 mil de orçamento e custo de R$ 45 por ação, cobrimos 1.777 clientes em risco crítico.
  > Sob premissas de 18% de resposta e 25% de efeito na evasão, estimamos salvar 26 clientes e R$ 8.518 em margem bruta.
  > Todas as premissas estão devidamente rotuladas na tela com a ressalva metodológica de que se trata de uma estimativa que deve ser calibrada em testes A/B com grupo de controle antes de qualquer expansão em escala."*

---

### 7. IA Responsável, Governança e LGPD (2:45 – 3:00)
* **Tela:** `07 · IA Responsável` (`http://localhost:8501/ia-responsavel`)
* **Ação visual:**
  1. Acessar `07 · IA Responsável`.
  2. Apontar a linha de referência da **Four-Fifths Rule (limiar 0,80)** no gráfico de barras demográficas.
  3. Alternar a dimensão para *Gênero* ou *Região* e mostrar os grupos **abaixo** do limiar    3. Alternar a dimensão para *Gênero* ou *Região* e mostrar os grupos **abaixo** do limiar (dados reais da base v3, auditoria executada: faixa 18-24 com razão 0,795; regiões Sul 0,557, Sudeste 0,642, Centro-Oeste 0,699 e Nordeste 0,724 — referência: região Norte com taxa 15,17%)..
  4. Destacar as salvaguardas do Artigo 20 da LGPD (direito à explicação e humano no circuito).
* **Fala do Apresentador:**
  > *"Para encerrar, IA responsável não é uma página de texto; é código e auditoria em tempo real.
  > Auditamos a disparidade de seleção de alto valor com a regra dos 4/5 (limiar 0,80) — e o painel está mostrando grupos FORA de conformidade: a faixa 18-24 aparece com razão de 0,795 frente à faixa 60+, e todas as regiões exceto o Norte ficam abaixo do limiar — a referência é a região Norte, com taxa de seleção de 15,17%, reflexo da malha regional concentrada. No geral, 9 dos 14 grupos demográficos informados estão conformes; os 5 fora do limiar estão sinalizados aqui, com plano de mitigação documentado.
  > Esse é exatamente o papel do painel: detectar e sinalizar, não esconder. Nenhum atributo sensível entrou nas variáveis dos modelos — a disparidade emerge de correlações socioeconômicas dos dados de treino, e qualquer disparo de campanha exige plano de mitigação documentado antes do piloto.
  > E garantimos o Artigo 20 da LGPD com explicabilidade SHAP e supervisão humana em cada oferta.
  > Este é o Projeto Aura 2.0: da milha ao momento de cuidado, com rigor analítico, design institucional Azul e código 100% reproduzível. Muito obrigado."*

> **⚠️ Regra de honestidade para o apresentador:** NUNCA afirme que "todos os grupos estão em conformidade" — verifique os números reais exibidos no painel no momento da apresentação (fixtures ou dados regenerados por `tasks.py all`) e enuncie o que eles mostrarem, inclusive as violações. Os valores citados acima correspondem à base sintética v3 real regenerada pelo pipeline (`data/analytics/fairness_metrics.parquet`); re-confira antes de apresentar. Clientes sem atributo demográfico declarado aparecem como grupo "não informado" — nunca imputados com valor factual.

---

## Checklist Pré-Apresentação para o Apresentador

- [ ] Executar o app via `python tasks.py app` e confirmar que a porta 8501 está ativa.
- [ ] Verificar se os dados de fixtures foram carregados sem erros.
- [ ] Testar a edição de mensagem na tela do Agente para garantir fluidez na interação.
- [ ] Conferir se o navegador está com zoom em 100% e resolução adequada (1920x1080 recomendado).
- [ ] Manter o cronômetro visível para respeitar estritamente o limite de 3 minutos.
