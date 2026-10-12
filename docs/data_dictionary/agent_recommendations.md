# `agent_recommendations`

> **Descrição:** Recomendações, mensagens e justificativas do agente de retenção e explicabilidade (WS7)  
> **Granularidade:** uma recomendação por cliente por campanha de retenção  
> **Produzida por:** agent.pipeline  
> **Consumidores:** app, ml.impact

| Coluna | Tipo | Nulo? | Descrição | Unidade | Fonte | Sensível | Exemplo |
|---|---|---|---|---|---|---|---|
| `customer_id` | string | não | Identificador único do cliente | - | data/analytics/agent_input.parquet | não | `C000001` |
| `action_id` | string | não | Identificador da ação recomendada no playbook (ex.: ACT-BONUS-PONTOS) | - | config/actions.yaml | não | `ACT-RESGATE-ESPECIAL` |
| `action_name` | string | não | Chave canônica da ação (ex.: oferta_resgate_especial) | - | config/actions.yaml | não | `oferta_resgate_especial` |
| `channel` | string | não | Canal selecionado para a comunicação (app, email, whatsapp, telefone) | - | agent.pipeline | não | `app` |
| `message` | string | não | Mensagem redigida em PT-BR para o cliente com suporte do regulamento e sem dados sensíveis | - | agent.composer | agent.llm | não | `Olá! Identificamos que você é cliente Safira...` |
| `justification_json` | string | não | Estrutura JSON com SHAP top-3, atritos dominantes e regras determinísticas acionadas | - | agent.pipeline | não | `{"shap_top3": ["queda_voos"], "atritos": ["resgate"], "regras": ["saldo_suficiente_para_cota"]}` |
| `citations_json` | string | não | Estrutura JSON com lista de citações formais do regulamento (fact_id, status, vigência, fonte) | - | agent.rag.retriever | não | `[{"fact_id": "AF-RESGATE-ESPECIAL-2025", "verification_status": "official_current_partial"}]` |
| `confidence` | float | não | Nível de confiança da recomendação (0.0 a 1.0) | score | agent.pipeline | não | `0.95` |
| `human_review` | bool | não | Flag que sinaliza necessidade de revisão humana (ex.: regras nulas no tier, caso sensível) | - | agent.guardrails | não | `False` |
| `mode` | string | não | Modo de execução que gerou a recomendação (offline ou llm) | - | agent.pipeline | não | `offline` |
| `snapshot_version` | string | não | Versão do snapshot do regulamento utilizada como base de conhecimento | - | config/program_rules.yaml | não | `research-2026-10-12` |
| `recommended_at` | string | não | Timestamp ISO-8601 da recomendação gerada | - | agent.pipeline | não | `2026-10-12T12:00:00Z` |

## Checagens de contrato

- **unicidade:** `customer_id`
- **não nulo:** `customer_id`
- **não nulo:** `action_id`
- **não nulo:** `action_name`
- **não nulo:** `channel`
- **não nulo:** `message`
- **não nulo:** `justification_json`
- **não nulo:** `citations_json`
- **não nulo:** `confidence`
- **não nulo:** `human_review`
- **não nulo:** `mode`
- **não nulo:** `snapshot_version`
- **não nulo:** `recommended_at`
