# Roteiro de Demonstração em 3 Minutos — Projeto Aura 2.0

> **Objetivo:** Contar a história ponta a ponta do Aura 2.0 em exatamente 3 minutos:  
> **Carteira → Segmentos → Cliente 360 → Explicabilidade SHAP → Agente com Citações → Atritos → Simulação de ROI → Governança LGPD.**  
> **Aviso obrigatório presente em todas as telas:** *"DADOS SINTÉTICOS — demonstração"*.

---

## Cronômetro da Demonstração (0:00 a 3:00)

| Tempo | Tela / Módulo | Foco da Ação | Mensagem Central |
|---|---|---|---|
| **0:00 – 0:30** | **01 · Visão da Carteira** | KPIs gerais + Pareto / Gini | Paradoxo da lealdade: Valor em Risco (CLV × Churn) |
| **0:30 – 0:55** | **02 · Personas** | Cards dos 6 arquétipos | Segmentação orientada a valor e playbooks específicos |
| **0:55 – 1:30** | **03 · Cliente 360** | Seletor + SHAP + Linha do tempo | Explicabilidade local: por que este cliente corre risco |
| **1:30 – 2:05** | **04 · Agente de Retenção** | Recomendação + Citação + Aprovação | RAG no regulamento (zero alucinação) + HITL funcional |
| **2:05 – 2:25** | **05 · Mapa de Atritos** | Barras de intensidade + Tendência temporal | Sentimento por aspecto alimenta o pipeline |
| **2:25 – 2:45** | **06 · Simulador de Impacto** | Sliders interativos + Cenários | ΔReceita Líquida e ROI sobre a carteira real |
| **2:45 – 3:00** | **07 · IA Responsável** | Four-Fifths Rule + LGPD Art. 20 | Equidade auditada, dados 100% sintéticos e conformidade |

---

## Roteiro Ponto a Ponto (Tela → Ação → Fala)

### 1. Visão da Carteira (0:00 – 0:30)
* **Tela:** `01 · Visão da Carteira` (`http://localhost:8501/carteira`)
* **Ação visual:**
  1. Apontar o banner permanente no topo: *"DADOS SINTÉTICOS — demonstração"*.
  2. Destacar os KPI Cards: **Valor em Risco Total**, **CLV 12M Total**, **Clientes de Alto Valor**.
  3. Rolar suavemente para a Curva de Lorenz/Pareto mostrando a concentração da receita (Gini).
* **Fala do Apresentador:**
  > *"Olá a todos. Este é o Aura 2.0, o pipeline reproduzível de inteligência de clientes e retenção do Azul Fidelidade.
  > Todas as métricas que veremos operam sobre uma base 100% sintética calibrada com microdados públicos da ANAC.
  > Começamos pela Visão da Carteira. O problema central que resolvemos é o paradoxo da lealdade: não retemos apenas quem tem alta probabilidade de sair, mas quem tem **Valor em Risco**, ou seja, o produto do CLV previsto pela probabilidade de churn.
  > Na curva de Pareto à direita, vemos que os 20% superiores da base concentram mais de 65% do valor total da carteira. Proteger esses clientes é a prioridade número um."*

---

### 2. Personas e Playbook (0:30 – 0:55)
* **Tela:** `02 · Personas` (`http://localhost:8501/personas`)
* **Ação visual:**
  1. Clicar no menu lateral em `02 · Personas`.
  2. Mostrar os cartões das personas com suas respectivas cores de identidade:
     - *Executivo Recorrente* (azul-deep `#033774`)
     - *Lazer Premium* (magenta `#E832A5`)
     - *Maximizador de Milhas* (azul-action `#0874B5`)
     - *Regional Dependente* (navy `#0B3558`)
  3. Apontar a linha de ação recomendada e atritos dominantes em cada card.
* **Fala do Apresentador:**
  > *"Em vez de clusters genéricos, o Aura classifica os clientes em 4 personas principais e 2 secundárias.
  > Por exemplo, o Executivo Recorrente tem alto CLV e voa em rotas corporativas troncais, mas sofre com atritos de pontualidade; sua ação é o contato proativo.
  > Já o Maximizador de Milhas acumula pesado via cartões e é sensível a atritos de resgate; para ele, o playbook prevê condições de cotas fixas de pontos.
  > Cada persona possui custos unitários parametrizados e regras determinísticas de elegibilidade."*

---

### 3. Cliente 360 e Explicabilidade SHAP (0:55 – 1:30)
* **Tela:** `03 · Cliente 360` (`http://localhost:8501/cliente-360`)
* **Ação visual:**
  1. Abrir o seletor de clientes ordenado por *Maior Valor em Risco*.
  2. Selecionar o primeiro cliente (ex.: cliente Diamante ou Safira com alto risco).
  3. Apontar o badge de categoria com a cor oficial do Azul Design System.
  4. Mostrar as métricas de CLV Previsto, P(Churn) e ScoreAV.
  5. Rolar para o gráfico de barras horizontais de **Explicabilidade SHAP** e a **Linha do Tempo**.
* **Fala do Apresentador:**
  > *"Ao descermos para o nível individual no Cliente 360, selecionamos este cliente Diamante que possui mais de R$ 5.000 em Valor em Risco e probabilidade de churn de 72%.
  > Mas nós não operamos como uma caixa-preta.
  > O gráfico SHAP à esquerda decompõe exatamente o que levou o modelo a prever esse risco: queda de frequência de voos nos últimos 90 dias e um atrito severo registrado em resgate de milhas.
  > Na linha do tempo à direita, correlacionamos o histórico de voos operados e os eventos de fricção do cliente."*

---

### 4. Agente Especialista e Humano no Circuito (1:30 – 2:05)
* **Tela:** `04 · Agente de Retenção` (`http://localhost:8501/agente`)
* **Ação visual:**
  1. Clicar em `04 · Agente de Retenção` (o cliente selecionado permanece sincronizado via `session_state`).
  2. Apontar a **Flag de Revisão Humana** destacada em amarelo quando aplicável.
  3. Mostrar o cartão de citação formal do regulamento com `fact_id` e status de verificação.
  4. Clicar no botão **Editar Mensagem**, ajustar um trecho do texto e clicar em **Salvar Alterações e Aprovar**.
  5. Apontar a mensagem de sucesso e a nova linha inserida na tabela de histórico auditável (`decisions.jsonl`).
* **Fala do Apresentador:**
  > *"Aqui vemos o Agente de Retenção em ação.
  > A regra de ouro do Aura: o agente **não alucina benefícios**. Ele só oferece ações elegíveis sustentadas pelo regulamento oficial do Azul Fidelidade.
  > Notem o bloco de citação: ele traz o fact_id oficial e a cláusula vigente.
  > Além disso, por se tratar de um cliente de altíssimo valor, a flag de Human-in-the-Loop bloqueou o disparo autônomo.
  > Como operador, posso revisar a mensagem redigida, clicar em 'Editar', refinar a abordagem e aprovar.
  > A decisão é imediatamente gravada no arquivo imutável decisions.jsonl para auditoria de compliance."*

---

### 5. Mapa de Atritos e Sentimento (2:05 – 2:25)
* **Tela:** `05 · Mapa de Atritos` (`http://localhost:8501/atritos`)
* **Ação visual:**
  1. Acessar `05 · Mapa de Atritos`.
  2. Apontar o gráfico de intensidade por aspecto (atraso, bagagem, resgate, app).
  3. Mostrar o gráfico de linhas com a tendência temporal semestre a semestre.
  4. Apontar a nota declarando o corpus 100% sintético para respeito aos termos de uso de sites públicos.
* **Fala do Apresentador:**
  > *"O diferencial do Aura é que o sentimento das avaliações não fica isolado num dashboard. Ele retroalimenta todo o sistema.
  > Neste mapa, acompanhamos a taxa de insatisfação por aspecto ao longo dos últimos semestres.
  > Identificamos que a fricção em 'resgate de milhas' é crônica, o que explica os altos valores de SHAP que vimos no cliente anterior e direciona as campanhas de facilitação de emissão."*

---

### 6. Simulador de Impacto Interativo (2:25 – 2:45)
* **Tela:** `06 · Simulador de Impacto` (`http://localhost:8501/simulador`)
* **Ação visual:**
  1. Navegar para `06 · Simulador de Impacto`.
  2. Clicar no chip do cenário **Base (Recomendado)** e em seguida no **Otimista**.
  3. Mover o slider de **Orçamento Total** (ex.: R$ 80.000 para R$ 120.000) e o de **Efeito da Ação**.
  4. Mostrar a atualização instantânea dos KPIs: **ΔReceita Líquida Estimada**, **Clientes Abordados**, **Evasões Evitadas** e o gráfico de cascata financeira (Waterfall).
* **Fala do Apresentador:**
  > *"Na tela de simulação, respondemos à pergunta executiva: 'Qual é o retorno sobre o investimento?'
  > Aplicamos em tempo real a fórmula de impacto financeiro sobre a carteira ordenada por Valor em Risco.
  > No cenário Base, com um orçamento de R$ 80 mil e 18% de taxa de resposta, projetamos preservar mais de R$ 240 mil em receita líquida, com um ROI estimado superior a 200%.
  > Todas as premissas estão explicitadas com a ressalva metodológica de que se trata de uma estimativa a ser validada em piloto A/B."*

---

### 7. IA Responsável, Governança e LGPD (2:45 – 3:00)
* **Tela:** `07 · IA Responsável` (`http://localhost:8501/ia-responsavel`)
* **Ação visual:**
  1. Acessar `07 · IA Responsável`.
  2. Apontar a linha de referência da **Four-Fifths Rule (limiar 0,80)** no gráfico de barras demográficas.
  3. Alternar a dimensão para *Gênero* ou *Região* e mostrar os grupos **abaixo** do limiar (no conjunto de fixtures: faixa 18-29 com razão ≈ 0,41; Nordeste ≈ 0,61; Norte ≈ 0,56; Sul ≈ 0,61).
  4. Destacar as salvaguardas do Artigo 20 da LGPD (direito à explicação e humano no circuito).
* **Fala do Apresentador:**
  > *"Para encerrar, IA responsável não é uma página de texto; é código e auditoria em tempo real.
  > Auditamos a disparidade de seleção de alto valor com a regra dos 4/5 (limiar 0,80) — e o painel está mostrando grupos FORA de conformidade: a faixa 18-29 aparece com razão de aproximadamente 0,41 frente ao grupo de referência, e as regiões Norte e Nordeste também abaixo do limiar.
  > Esse é exatamente o papel do painel: detectar e sinalizar, não esconder. Nenhum atributo sensível entrou nas variáveis dos modelos — a disparidade emerge de correlações socioeconômicas dos dados de treino, e qualquer disparo de campanha exige plano de mitigação documentado antes do piloto.
  > E garantimos o Artigo 20 da LGPD com explicabilidade SHAP e supervisão humana em cada oferta.
  > Este é o Projeto Aura 2.0: da milha ao momento de cuidado, com rigor analítico, design institucional Azul e código 100% reproduzível. Muito obrigado."*

> **⚠️ Regra de honestidade para o apresentador:** NUNCA afirme que "todos os grupos estão em conformidade" — verifique os números reais exibidos no painel no momento da apresentação (fixtures ou dados regenerados por `tasks.py all`) e enuncie o que eles mostrarem, inclusive as violações. Os valores citados acima correspondem ao estado atual dos fixtures; re-confira antes de apresentar.

---

## Checklist Pré-Apresentação para o Apresentador

- [ ] Executar o app via `python tasks.py app` e confirmar que a porta 8501 está ativa.
- [ ] Verificar se os dados de fixtures foram carregados sem erros.
- [ ] Testar a edição de mensagem na tela do Agente para garantir fluidez na interação.
- [ ] Conferir se o navegador está com zoom em 100% e resolução adequada (1920x1080 recomendado).
- [ ] Manter o cronômetro visível para respeitar estritamente o limite de 3 minutos.
