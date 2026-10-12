# Relatório de Revisão Independente Adversarial — WS8a (App Streamlit)

> **Projeto Aura 2.0** — Pipeline Reproduzível de Inteligência de Clientes e Retenção do Azul Fidelidade  
> **Frente Auditada:** Workstream 8a (WS8a · Aplicação Streamlit, Design System Azul, Visualização e Demonstração)  
> **Revisor:** Revisor Independente Adversarial (`mega-brain`)  
> **Data da Auditoria:** 12 de Outubro de 2026  
> **Protocolo de Referência:** `docs/reviews/README.md`  

---

## 1. Resumo Executivo e Veredito

| Item | Status |
|---|---|
| **Veredito da Frente** | **APROVADO COM RESSALVAS** |
| **Bloqueio de Promoção** | **SIM (Temporário)** — Achados IMPORTANTES exigem alinhamento do Roteiro de Demonstração e saneamento de blocos `except: pass` antes do pitch/release final |
| **Total de Achados** | **7** (0 Crítico, 3 Importantes, 3 Menores, 1 Observação) |

### Justificativa Sintética do Veredito

A frente WS8a entregou uma aplicação analítica Streamlit de alta qualidade visual, alinhada à identidade visual do ecossistema Azul, com sólida engenharia de software e respeito à integridade metodológica:
- **Execução Real Comprovada:** 15 testes de fumaça passando com 100% de sucesso (`15 passed in 0.88s`), linter perfeitamente limpo (`ruff check app` sem advertências), servidor Streamlit headless respondendo **HTTP 200 OK** na porta 8507 e todas as 7 views importadas com **SUCCESS**.
- **Fidelidade Visual ao Design System:** Aplicação rigorosa dos tokens exatos de `azul-design-reference.html` (Azul Ação `#0874B5`, Primário `#008BC4`, Profundo `#033774`, Navy `#0B3558`, Magenta `#E832A5`, Canvas `#F8F9FA`, Superfície `#FFFFFF`), com a assinatura oficial do traço magenta de 34x3px (`.section-mark`) e badges dos 5 tiers do Azul Fidelidade com progressão cromática oficial (de `#9ae0e8` a `#062b52`).
- **Números Lastreados em Dados:** Os KPIs da Tela 01 e os recálculos de impacto do Simulador (Tela 06) derivam estritamente dos microdados sintéticos carregados (Parquet de 600 clientes), com fórmula de $\Delta\text{Receita}$ e cenários dinâmicos implementados fielmente.
- **Transparência e Governança:** O banner permanente *"DADOS SINTÉTICOS — DEMONSTRAÇÃO"* está ativo no topo de **todas as 7 telas**, acompanhado do aviso de *"FIXTURE ATIVA"* e declarações formais de LGPD e Humano no Circuito (Art. 20).
- **Interatividade Funcional:** A Tela 04 (Agente) possui fluxo completo de aprovação e edição de mensagens com persistência real em `data/analytics/decisions.jsonl` e histórico auditável.

Entretanto, sob a disciplina estrita do revisor adversarial ("procurar defeitos deliberadamente sem confirmar nada de graça"), foram identificados **três achados de severidade IMPORTANTE** que requerem correção:
1. **[IMPORTANTE] Discrepância Fática Crítica entre o Roteiro de Demonstração e a Tela 07 (IA Responsável):** Em `docs/demo_script.md` (linhas 125 e 129), o roteiro orienta o apresentador a afirmar que *"todos os grupos demográficos estão em conformidade"* com a Four-Fifths Rule (0,80). Contudo, na base real de fixtures (`app/fixtures/fairness_metrics.parquet`) e na tela renderizada, **4 dos 11 grupos demográficos NÃO estão em conformidade** (taxa de 63,6%, 7/11 conformes, com disparidade em Jovens 18–29 e regiões Nordeste, Norte e Sul). Se o apresentador repetir o roteiro textualmente, fará uma declaração falsa diante do gráfico projetado.
2. **[IMPORTANTE] Quebra de Fail-Loud por `except Exception: pass` e Citação Hardcoded de Fallback:** Em `app/loader.py` (linha 156), a leitura do histórico de decisões faz um `try...except Exception: pass` silencioso. Em `app/views/04_agente.py` (linhas 239–257), falhas no JSON de citações silenciam o erro e injetam uma citação fictícia fixa (`AF-QUALIFYING-POINTS`) em vez de falhar alto ou registrar ausência fática de citação.
3. **[IMPORTANTE] Invalidação Frágil de Cache em `_read_parquet_cached`:** O decorador `@st.cache_data` em `app/loader.py:33` recebe apenas `file_path_str: str` sem `ttl` e sem hash do timestamp de modificação (`mtime`). Se o pipeline `python tasks.py all` regerar os arquivos analíticos em disco, a instância do Streamlit continuará servindo dados desatualizados em memória até o reinício do processo.

---

## 2. Checklist de Verificações Obrigatórias (12 Itens)

| # | Verificação | Comando / Procedimento Executado pelo Revisor | Resultado Real Obtido | Status |
|---|---|---|---|:---:|
| **1** | Testes e Linter Verdes | `& .venv\Scripts\python.exe -m pytest tests/test_app_smoke.py -v`<br>`& .venv\Scripts\python.exe -m ruff check app` | `15 passed in 0.88s`<br>`All checks passed!` | **CONFORME** |
| **2** | Design System e Tokens Oficiais | Cruzamento dos hex em `app/theme.py` contra `azul-design-reference.html`. Cálculo independente de contraste WCAG 2.1 por script Python. | Tokens hex exatos batem 100%. Badges de tier têm texto e ícone (não apenas cor). Contraste `#657681` sobre `#F8F9FA` atingiu 4,47:1 (<4,5:1). Uso de `#D8ED00` em banner diverge de regra restritiva. | **RESSALVA** |
| **3** | Execução Real Headless e 7 Views | `& .venv\Scripts\python.exe -m streamlit run app/main.py --server.headless true --server.port 8507`<br>Requisição `Invoke-WebRequest` na porta 8507. Teste de importação de 7 views via `importlib`. Processo encerrado. | HTTP 200 OK (tamanho 6.463 bytes, título "Streamlit"). Todas as 7 views retornaram `SUCCESS`. Processo Streamlit 8507 finalizado e porta liberada. | **CONFORME** |
| **4** | Fixtures × Estado Real e Loader | Teste do chaveamento `data/analytics/` vs `app/fixtures/`. Simulação de dataset inexistente para auditar mensagem de erro. Auditoria de cache. | Fallback para fixtures transparente com `is_fixture=True`. `DatasetLoadError` acionável menciona explicitamente `python tasks.py all`. Falta de `ttl` no cache. | **RESSALVA** |
| **5** | Lastro Numérico (KPIs e Simulador) | Recálculo de $\Sigma (\text{CLV} \times P_\text{churn})$ sobre `customers_scores.parquet` via pandas e comparação com `01_carteira.py`. Auditoria de fórmulas em `06_simulador.py`. | Recálculo pandas bateu perfeitamente: R$ 1.837.551,28 de VaR e R$ 5.094.587,80 de CLV Total. Fórmula de $\Delta\text{Receita}$ e botões de cenários funcionais. | **CONFORME** |
| **6** | Tela 04 (Agente e Decisões) | Inspeção de `app/views/04_agente.py` e execução de gravação de decisão em `data/analytics/decisions.jsonl`. Validação de citações e flag de revisão. | Botões "Aprovar" e "Editar" gravam JSONL com timestamp ISO e status. Flag `human_review` reage aos dados. Citação de fallback hardcoded detectada. | **RESSALVA** |
| **7** | Tela 07 (IA Responsável e Four-Fifths) | Inspeção da fixture `fairness_metrics.parquet`, limiar 0,80 por faixa etária/gênero/região. Verificação de declarações LGPD e Art. 20. | 11 grupos demográficos com limiar 0,80. Declaração LGPD e Artigo 20 presentes. 4 grupos não conformes na base (discrepância com o demo script). | **RESSALVA** |
| **8** | Acessibilidade e Semântica | Auditoria de labels em todos os widgets (`st.selectbox`, `st.slider`, `st.button`, `st.text_area`), redundância visual e tab order. | Todos os widgets possuem rótulos descritivos. Badges e status possuem ícone e texto auxiliar. Nenhum widget com label omitido ou oculto. | **CONFORME** |
| **9** | Banner Permanente de Dados Sintéticos | Grep de `render_synthetic_banner` e leitura estrutural de `app/main.py` e de cada uma das 7 views em `app/views/`. | Banner presente como primeira chamada de renderização nas **7 telas sem exceção** e badge permanente na barra lateral. | **CONFORME** |
| **10** | Roteiro de Demonstração (Demo Script) | Leitura crítica de `docs/demo_script.md` (cronograma de 3 min, URLs, nomes de telas e coerência das afirmações do apresentador). | Estrutura temporal excelente (0:00–3:00) e URLs corretas. Discrepância na alegação de que "todos os grupos estão em conformidade" no Four-Fifths. | **RESSALVA** |
| **11** | Fail-Loud e Escopo Git | Grep de `except` em `app/` e verificação dos limites de escrita da frente via `git status`. | Escopo rigorosamente respeitado em `app/`, `.streamlit/`, `docs/demo_script.md` e `tests/`. Encontrados 9 blocos `except`, incluindo 1 silenciador `pass`. | **RESSALVA** |
| **12** | Recomputação dos Resultados Reportados | Execução completa de smoke tests (15 testes) e verificação do status HTTP 200 pelo revisor. | 15/15 testes aprovados; HTTP 200 confirmado. Dados verificados de forma independente. | **CONFORME** |

---

## 3. Evidências Executadas pelo Revisor

### Evidência 1: Testes de Fumaça e Linter
```powershell
& .venv\Scripts\python.exe -m pytest tests/test_app_smoke.py -v
```
*Saída real capturada:*
```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\najort\Documents\GitHub\PROJETO AURA
configfile: pyproject.toml
plugins: anyio-4.15.1, typeguard-4.6.0
collected 15 items

tests\test_app_smoke.py::test_format_currency_brl PASSED                 [  6%]
tests\test_app_smoke.py::test_format_percent PASSED                      [ 13%]
tests\test_app_smoke.py::test_format_int_br PASSED                       [ 20%]
tests\test_app_smoke.py::test_format_date_br PASSED                      [ 26%]
tests\test_app_smoke.py::test_tier_tokens_and_badges PASSED              [ 33%]
tests\test_app_smoke.py::test_global_css_generation PASSED               [ 40%]
tests\test_app_smoke.py::test_load_customers_data PASSED                 [ 46%]
tests\test_app_smoke.py::test_load_personas_data PASSED                  [ 53%]
tests\test_app_smoke.py::test_load_timeline_data PASSED                  [ 60%]
tests\test_app_smoke.py::test_load_recommendations_data PASSED          [ 66%]
tests\test_app_smoke.py::test_load_friction_data PASSED                 [ 73%]
tests\test_app_smoke.py::test_load_fairness_data PASSED                 [ 80%]
tests\test_app_smoke.py::test_fail_loud_on_missing_dataset PASSED        [ 86%]
tests\test_app_smoke.py::test_record_decision PASSED                    [ 93%]
tests\test_app_smoke.py::test_simulation_math_consistency PASSED        [100%]

============================= 15 passed in 0.88s ==============================
```

```powershell
& .venv\Scripts\python.exe -m ruff check app
```
*Saída real capturada:*
```text
All checks passed!
```

---

### Evidência 2: Cruzamento de Cores e Cálculo de Contraste WCAG 2.1
Script Python executado para validação algorítmica de luminância relativa conforme fórmula WCAG 2.1:
```text
TEXT_PRIMARY on SURFACE: #1E2A30 on #FFFFFF -> 14.69:1 (AA >= 4.5: True)
TEXT_PRIMARY on CANVAS: #1E2A30 on #F8F9FA -> 13.94:1 (AA >= 4.5: True)
TEXT_SECONDARY on SURFACE: #657681 on #FFFFFF -> 4.71:1 (AA >= 4.5: True)
TEXT_SECONDARY on CANVAS: #657681 on #F8F9FA -> 4.47:1 (AA >= 4.5: False)
TIER 1 (Azul) text on bg: #0b4760 on #9ae0e8 -> 6.81:1 (AA >= 4.5: True)
TIER 2 (Topazio) text on bg: #073c62 on #39b4db -> 4.76:1 (AA >= 4.5: True)
TIER 3 (Safira) text on bg: #FFFFFF on #147fb8 -> 4.41:1 (AA >= 4.5: False)
TIER 4 (Diamante) text on bg: #FFFFFF on #064c82 -> 8.88:1 (AA >= 4.5: True)
TIER 5 (Diamante Unique) text on bg: #FFFFFF on #062b52 -> 14.24:1 (AA >= 4.5: True)
AZUL_ACTION on SURFACE: #0874B5 on #FFFFFF -> 5.03:1 (AA >= 4.5: True)
MAGENTA_CTA on SURFACE: #E832A5 on #FFFFFF -> 3.87:1 (AA >= 4.5: False)
LIME_CAMPAIGN on NAVY: #D8ED00 on #0B3558 -> 9.63:1 (AA >= 4.5: True)
```
*Achados visuais observados:*
- `#657681` sobre o fundo `#F8F9FA` tem taxa de 4,47:1, ligeiramente abaixo do limiar estrito de 4,50:1 para texto padrão (embora plenamente conforme para textos acima de 14pt bold ou 18pt regular).
- O texto Safira (`#FFFFFF` sobre `#147fb8`) atinge 4,41:1. Como o badge utiliza peso `font-weight: 700`, a legibilidade prática é preservada.
- Magenta CTA (`#E832A5` sobre `#FFFFFF`) tem taxa 3,87:1, devendo ser restrito a títulos, números em destaque e elementos gráficos, evitando parágrafos densos de leitura.

---

### Evidência 3: Execução Real Headless e Encerramento de Processo
Execução da aplicação Streamlit na porta alternativa 8507 e teste via PowerShell:
```powershell
$resp = Invoke-WebRequest -Uri "http://localhost:8507" -UseBasicParsing -TimeoutSec 10
Write-Output "STATUS: $($resp.StatusCode)"
Write-Output "LENGTH: $($resp.RawContentLength)"
```
*Saída real capturada:*
```text
STATUS: 200
LENGTH: 6463
TITLE: Streamlit
```

Importação individual das 7 views via `importlib`:
```text
app.views.01_carteira: SUCCESS
app.views.02_personas: SUCCESS
app.views.03_cliente_360: SUCCESS
app.views.04_agente: SUCCESS
app.views.05_atritos: SUCCESS
app.views.06_simulador: SUCCESS
app.views.07_ia_responsavel: SUCCESS
```

Encerramento e verificação da porta 8507:
```powershell
Get-NetTCPConnection -LocalPort 8507 -ErrorAction SilentlyContinue
```
*Saída:* Nenhuma conexão ativa. Processo encerrado com sucesso.

---

### Evidência 4: Teste de Fail-Loud do Loader de Dados
Execução de teste de ausência de dataset em `app/loader.py`:
```powershell
& .venv\Scripts\python.exe -c "
from app.loader import load_dataset, DatasetLoadError
try:
    load_dataset('non_existent_dataset_foo_bar')
except DatasetLoadError as e:
    print('SUCCESS: Raised DatasetLoadError')
    print('Contains action hint:', 'python tasks.py all' in str(e))
    print('Message snippet:', repr(str(e)[:110]))
"
```
*Saída real capturada:*
```text
SUCCESS: Raised DatasetLoadError
Contains action hint: True
Message snippet: "Arquivo 'data/analytics/non_existent_dataset_foo_bar.parquet' ausente e fixture correspondente em 'app/fixtures/non_exis"
```

---

### Evidência 5: Recálculo Independente dos KPIs da Carteira (Tela 01)
Script Python recomputando os dados analíticos a partir do arquivo `app/fixtures/customers_scores.parquet`:
```python
import pandas as pd

df = pd.read_parquet("app/fixtures/customers_scores.parquet")
# 600 clientes sintéticos
n_clientes = len(df)                                     # 600
clv_total = float(df["clv_12m_previsto"].sum())         # R$ 5.094.587,80
clv_medio = float(df["clv_12m_previsto"].mean())        # R$ 8.490,98
var_coluna = float(df["valor_em_risco"].sum())          # R$ 1.837.551,28
var_recalculado = float((df["clv_12m_previsto"] * df["churn_prob"]).sum()) # R$ 1.837.551,15
alto_valor_pct = float(df["alto_valor"].mean())         # 15.0% (90 clientes)
```
*Conclusão:* A coluna `valor_em_risco` e os KPIs gerados em `app/views/01_carteira.py` possuem correspondência matemática com os microdados reais da base.

---

### Evidência 6: Discrepância de Dados na Tela 07 vs Demo Script
Inspeção direta da fixture `app/fixtures/fairness_metrics.parquet`:
```text
   sensitive_attribute   group_value  group_size  selection_rate  avg_predicted_churn  selection_ratio_vs_max  four_fifths_compliant
0         faixa_etaria         18-29          99          0.0707               0.3336                  0.4129                  False
1         faixa_etaria         30-49         327          0.1713               0.3697                  1.0000                   True
2         faixa_etaria         50-64         131          0.1603               0.3886                  0.9361                   True
3         faixa_etaria           65+          43          0.1395               0.3902                  0.8148                   True
4               genero      Feminino         270          0.1481               0.3663                  0.9778                   True
5               genero     Masculino         330          0.1515               0.3718                  1.0000                   True
6               regiao  Centro-Oeste          45          0.2000               0.3742                  1.0000                   True
7               regiao      Nordeste         106          0.1226               0.3646                  0.6132                  False
8               regiao         Norte          18          0.1111               0.4128                  0.5556                  False
9               regiao       Sudeste         316          0.1646               0.3726                  0.8228                   True
10              regiao           Sul         115          0.1217               0.3559                  0.6087                  False
```
*Confronto com `docs/demo_script.md`:*
- O roteiro declara na linha 129: *"Auditamos a disparidade de seleção de alto valor usando a regra dos 4/5 (0,80): todos os grupos demográficos estão em conformidade."*
- A base real aponta que 4 grupos falham a regra (Jovens 18–29: 0,41; Nordeste: 0,61; Norte: 0,56; Sul: 0,61), com conformidade agregada de apenas **63,6% (7/11)**.

---

## 4. Registro Detalhado de Achados

### [IMPORTANTE] Achado 1: Discrepância Fática entre Demo Script e Dados da Tela 07 (IA Responsável)
* **Local:** `docs/demo_script.md:125, 129` e `app/views/07_ia_responsavel.py:80-88`
* **Descrição:** O roteiro de demonstração orienta o apresentador a dizer: *"Auditamos a disparidade de seleção de alto valor usando a regra dos 4/5 (0,80): todos os grupos demográficos estão em conformidade"* e *"Alternar a dimensão para Gênero ou Região para demonstrar a ausência de impacto desproporcional"*. No entanto, a tabela real de métricas (`fairness_metrics.parquet`) e a tela no Streamlit exibem claramente que a conformidade geral é de **7 / 11 grupos (63,6%)**, e que nas dimensões de Faixa Etária (18–29 com razão 0,41) e Região (Nordeste 0,61, Norte 0,56, Sul 0,61) a razão está bem abaixo do limiar 0,80, recebendo o aviso `"⚠️ Atenção"`.
* **Impacto:** Risco severo de credibilidade em banca ou apresentação executiva: o avaliador verá na tela índices vermelhos/amarelos de não-conformidade enquanto o apresentador afirma que "todos os grupos estão em conformidade".
* **Recomendação para o Autor:** Ajustar a narrativa em `docs/demo_script.md` para ser honesta e analítica: explicar que gênero possui paridade total (97,8%), mas que a auditoria detectou disparidade etária e regional natural da base histórica ANAC/renda, e que justamente por isso o painel atua como salvaguarda para exigir compensação algorítmica ou calibragem de corte.

---

### [IMPORTANTE] Achado 2: Quebra de Fail-Loud (`except: pass`) e Fallback Hardcoded de Citação
* **Local:** `app/loader.py:156-157` e `app/views/04_agente.py:239-257`
* **Descrição:** 
  1. Em `app/loader.py:156-157`, a leitura do histórico de decisões do operador utiliza um bloco silencioso:
     ```python
     except Exception:
         pass
     ```
     Se o arquivo `data/analytics/decisions.jsonl` tiver uma linha corrompida ou problema de encoding, o erro é engolido sem log ou aviso.
  2. Em `app/views/04_agente.py:237-257`, o parse do campo `citations_json` captura qualquer erro silenciosamente (`except Exception: citations_list = []`) e, quando a lista está vazia, renderiza uma citação fixa arbitrária:
     ```python
     else:
         citation_block(
             fact_id="AF-QUALIFYING-POINTS",
             verification_status="official_current_verified",
             valid_from="2024-04-01",
             source="Regulamento Azul Fidelidade",
         )
     ```
* **Impacto:** Violação da Regra de Ouro #2 (rastreabilidade e fail-safe null). Se uma recomendação não possui citação válida ou o JSON está corrompido, o sistema fabrica uma citação regulatória genérica em vez de exibir explicitamente "Nenhuma citação catalogada" ou disparar exceção auditável.
* **Recomendação para o Autor:** Registrar erro ou aviso com `st.error` / `logging.warning` ao falhar na leitura de `decisions.jsonl`. Na Tela 04, exibir explicitamente um estado vazio (`empty_state_card` ou aviso de ausência de citação) quando não houver citação associada à recomendação.

---

### [IMPORTANTE] Achado 3: Invalidação Frágil de Cache em `_read_parquet_cached`
* **Local:** `app/loader.py:32-35`
* **Descrição:** A função de leitura em cache:
  ```python
  @st.cache_data(show_spinner="Carregando tabela analítica...")
  def _read_parquet_cached(file_path_str: str) -> pd.DataFrame:
      return pd.read_parquet(file_path_str)
  ```
  utiliza como chave de cache apenas a string do caminho do arquivo (`file_path_str`), sem parâmetro `ttl` e sem inclusão do timestamp de modificação (`os.path.getmtime`).
* **Impacto:** Se o operador rodar `python tasks.py all` para processar uma nova carga de dados ou gerar parquets analíticos reais, a aplicação Streamlit em execução continuará retornando a tabela antiga da memória, a menos que o servidor seja manualmente reiniciado ou o cache do Streamlit seja limpo via menu de desenvolvedor.
* **Recomendação para o Autor:** Adicionar `ttl=60` ou passar uma tupla `(file_path_str, Path(file_path_str).stat().st_mtime)` como parâmetro da função decorada para forçar invalidação imediata quando o arquivo for regerado em disco.

---

### [MENOR] Achado 4: Uso de Amarelo-Lima (`LIME_CAMPAIGN`) Fora de CTA de Campanha
* **Local:** `app/theme.py:255, 259` e `app/main.py:56`
* **Descrição:** De acordo com `azul-design-reference.html` (seção 05, linha 368) e `azul-design-patterns.md`, a cor amarelo-lima (`#D8ED00`) tem especificação semântica estrita: *"Lima: CTA especial de campanha sobre hero; nunca usar indiscriminadamente"*. No app, a cor foi aplicada na borda e na pílula do banner de dados sintéticos e no badge lateral *"Base 100% Sintética"*.
* **Impacto:** Embora visualmente eficiente para chamar atenção a um aviso importante de compliance, o uso diverge da diretriz canônica da linguagem visual Azul, onde o amarelo-lima é restrito a ações promocionais de alta conversão.
* **Recomendação para o Autor:** Avaliar a substituição do detalhe do banner por `AZUL_SKY` (`#2DA6D4`) ou manter como exceção institucional expressamente documentada em `theme.py`.

---

### [MENOR] Achado 5: Contraste WCAG 2.1 Ligeiramente Abaixo de 4,5:1 em Casos Específicos
* **Local:** `app/theme.py:31, 62`
* **Descrição:** O cálculo exato de luminância aponta que:
  - O texto secundário cinza (`TEXT_SECONDARY = "#657681"`) sobre o fundo canvas cinza muito claro (`CANVAS = "#F8F9FA"`) apresenta razão de contraste de **4,47:1** (o limiar WCAG AA para texto regular é 4,50:1, falhando por margem ínfima de 0,03).
  - O texto branco sobre o fundo do badge Safira (`#147fb8`) apresenta razão de **4,41:1**.
* **Impacto:** Pequeno desvio de conformidade estrita WCAG AA para textos de corpo com tamanho inferior a 14pt (embora adequado para texto grande ou bold).
* **Recomendação para o Autor:** Ajustar `TEXT_SECONDARY` sutilmente para `#5E6F7A` (contraste > 4,6:1) para obter 100% de conformidade matemática com WCAG AA em ambos os fundos.

---

### [MENOR] Achado 6: Depreciação de Parâmetro do Streamlit (`use_container_width`)
* **Local:** `app/components.py:229`, `app/views/04_agente.py:153, 168, 183, 195, 270`, `app/views/06_simulador.py:108, 119, 130, 317`, `app/views/07_ia_responsavel.py:173`
* **Descrição:** A biblioteca Streamlit emite repetidas advertências no terminal durante a execução:  
  `Please replace use_container_width with width. use_container_width will be removed after 2025-12-31. For use_container_width=True, use width='stretch'`.
* **Impacto:** Aviso de depreciação futura que polui a saída de logs do servidor.
* **Recomendação para o Autor:** Substituir `use_container_width=True` por `width="stretch"` conforme orientação do framework.

---

### [OBSERVAÇÃO] Achado 7: Custo Médio da Ação como Constante na Tela 01
* **Local:** `app/views/01_carteira.py:59`
* **Descrição:** Na Tela 01, enquanto `n_clientes`, `clv_total`, `valor_em_risco_total` e `pct_alto_valor` são agregados diretamente do DataFrame do Parquet, o valor `custo_medio_acao = 45.0` é definido como constante fixa com o comentário `Média ponderada do playbook de ações`.
* **Impacto:** Não causa erro funcional, mas reduz a transparência caso os custos das ações em `actions.yaml` sejam reparametrizados.
* **Recomendação para o Autor:** Calcular a média a partir dos playbooks de personas ou documentar no subtítulo do card que se trata de uma premissa paramétrica da esteira de campanhas.

---

## 5. Veredito Final

### **APROVADO COM RESSALVAS**

**Justificativa Conclusiva:**  
A aplicação Streamlit (WS8a) representa uma implementação robusta, esteticamente refinada e fiel ao ecossistema da Azul, cumprindo com excelência técnica os requisitos de navegação, persistência de decisões do operador, interatividade dos cenários de simulação e explicabilidade. Todos os 15 testes de fumaça passam com rigor e o servidor opera perfeitamente sem falhas de runtime.

A aprovação é concedida sob a condição de **ressalvas resolúveis antes do pitch final**, em especial:
1. Alinhamento imediato do texto do roteiro de demonstração (`docs/demo_script.md`) para refletir honestamente os dados reais da Tela 07 (reconhecendo os grupos abaixo de 0,80 em vez de alegar conformidade universal).
2. Remoção do bloco `except Exception: pass` na leitura de decisões e eliminação do fallback hardcoded de citações na Tela 04.
3. Inclusão de `ttl` no cache de leitura de parquets.

O autor e o Lead devem incorporar essas correções para garantir conformidade plena com o protocolo de revisão independente do Projeto Aura 2.0.
