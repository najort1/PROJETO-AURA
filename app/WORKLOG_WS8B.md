# WORKLOG WS8b · Integração do App Streamlit com a Base Analítica Real (50k clientes)

## [2026-10-12 / Início WS8b]
- Inicializado escopo da task-9 / WS8b: integração das 7 telas com 50k clientes reais de `data/analytics/`.
- Regras ativas: console curto (`Select-Object`), sem comandos git, escopo de escrita restrito (`app/`, `docs/demo_script.md`, `tests/test_app_smoke.py`), zero edição em `agent/` ou `ml/`.

## [2026-10-12 / Etapa 1 - Início Precompute Real]
- Disparado `python tasks.py agent-precompute` (job background pwsh-1218) consumindo `data/analytics/agent_input.parquet` (50.000 linhas).
- Verificado que `agent/pipeline.py` detecta arquivo analítico automaticamente; mantido congelado conforme instrução.
- Estimativa de execução ~26 min em background enquanto avançamos com a auditoria do loader e telas.

## [2026-10-12 / Etapa 2 - Loader Real-First e Banners]
- `app/loader.py`: prioridade analítica estrita via `is_analytics_mode()`. Se a base real existir, erro em qualquer arquivo crítico aciona fail loud e nunca cai silenciosamente para fixtures.
- `app/components.py`: banner adaptativo exibindo `DADOS SINTÉTICOS · BASE ANALÍTICA v3` quando operando sobre dados analíticos reais.
- `app/views/01_carteira.py`: Valor em Risco total ajustado para Σ(clv × churn_prob) resultando em R$ 8.305.496,50 exatos.
- `app/views/03_cliente_360.py`: vetorização instantânea do seletor de 50k clientes, suporte bidirecional de explicabilidade SHAP no CLV e guardrail de corte temporal (max 2025-08-31).
- `app/views/05_atritos.py`: exibição explícita dos pesos de 49 linhas de `friction_map.parquet` (atraso 0,1965 ... conforto 0,0502).
- `app/views/07_ia_responsavel.py`: cálculo exato de 9/14 grupos conformes e 5 não conformes, com marcação formal de 2 grupos "não informado" fora do escopo 4/5.
- `docs/demo_script.md`: alinhamento de 100% dos dados para a coorte real de 50.000 clientes e caso de uso real C038454.

## [2026-10-12 / Etapa 3 - Conclusão do Precompute e Validação]
- Job `pwsh-1218` (`tasks.py agent-precompute`) concluído com sucesso (exit code 0): 50.000 recomendações geradas em ~26m20s e validadas estritamente contra o contrato `schemas/recommendations.yaml` (0 violações).
- Distribuição de ações na base real de 50k: ACT-NO-ACTION (35.362), ACT-AVISO-ANTENCIPADO (9.758), ACT-ANTECIPACAO-NIVEL (4.610), ACT-EDUCA-BENEFICIO (139), ACT-PACOTE-EXPERIENCIA (130), ACT-ATRATRIBUI-ATRASO (1).
- `app/views/04_agente.py`: seletor de clientes otimizado com filtro para alternar entre ações proativas elegíveis (14.638) e toda a base (50.000), garantindo sincronização e citação formal auditável com snapshot `research-2026-10-12`.
- Streamlit validado em modo headless na porta 8507 (Job `pwsh-1265`), respondendo HTTP 200 OK via curl.
- Testes automatizados: `pytest tests/test_app_smoke.py` (16/16 verde), suíte completa `pytest` (177/177 verde) e `ruff check app tests` 100% limpo.
- `app/VERIFICATION.md`: documentação completa de verificação cruzada das 7 telas com os números reais recalculados.

## [2026-10-12 / Adendo do Orquestrador — pós-gate final]
- As contagens acima (14.638 alvos; 35.362 silêncio; 9.758/4.610) referem-se aos artefatos pré-regeneração canônica.
- O gate de reprodução do zero detectou não-determinismos de features (ordem de linhas, empates de rota, soma float — corrigidos na raiz em `dbt/`; ver `docs/limitations.md §7b`) e, na sequência, um crash silencioso por tipo DECIMAL no parquet de features que deixava `customers_scores` obsoleto — corrigido com publicação `::DOUBLE` e guarda de consistência permanente em `tests/test_integration.py`.
- A cadeia foi regenerada LIMPAMENTE a partir das predições canônicas (bitwise estáveis); as contagens finais constam em `docs/impact_simulation.md` e em `app/VERIFICATION.md`. O snapshot `research-2026-10-12` e todos os contratos permanecem válidos.


