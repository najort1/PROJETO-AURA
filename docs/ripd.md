# RIPD simplificado — Relatório de Impacto à Proteção de Dados (LGPD)

> Projeto Aura 2.0 · Versão 1.0 · Elaborado pelo orquestrador (Lead)
> Base legal de referência: Lei nº 13.709/2018 (LGPD), em especial arts. 5º, 6º, 20, 38 e 46.

## 1. Identificação do tratamento

| Item | Descrição |
|---|---|
| Produto | Pipeline de inteligência de clientes e retenção (Azul Fidelidade) com painel e agente de recomendação |
| Natureza dos dados | **100% SINTÉTICOS** — nenhum dado pessoal real é coletado, tratado ou armazenado |
| Dados pessoais envolvidos | Nenhum de titulares reais. A base sintética contém atributos artificiais de auditoria (faixa etária, gênero, região) gerados por código, usados EXCLUSIVAMENTE para auditoria de viés |
| Dados sensíveis | Nenhum (LGPD art. 5º, II). Atributos de auditoria são sintéticos e não correspondem a pessoas |
| Fontes públicas usadas | Microdados ANAC (dados de mercado, sem pessoas); fatos do programa Azul Fidelidade verificados por pesquisa (regras comerciais, não dados de titulares) |
| Finalidade | Demonstração técnica e validação de pipeline de retenção; prova de conceito de IA responsável |

## 2. Por que este relatório existe

O objetivo do projeto é **preparar a troca para dados reais** (plano em
[docs/snowflake_plan.md](snowflake_plan.md)). Este RIPD documenta (a) a postura de
proteção do MVP sintético e (b) os requisitos obrigatórios para qualquer uso com
dados de titulares reais.

## 3. Riscos e medidas — MVP sintético (estado atual)

| Risco | Medida implementada | Evidência |
|---|---|---|
| Atributos de auditoria virarem features de modelo (discriminação indireta) | Atributos sensíveis PROIBIDOS nas features; teste automatizado que falha o pipeline se vazar | `config/settings.yaml fairness`, `tests/test_fairness.py` |
| Recomendação opaca | Toda recomendação cita fact_id + status de verificação + vigência do regulamento; SHAP top-3 como justificativa; humano no circuito (aprovar/editar no painel) | `schemas/recommendations.yaml`, tela 04 do app |
| Mensagem com dado sensível | Guardrail que bloqueia qualquer dado sensível na mensagem | `agent/guardrails.py`, `tests/test_guardrails.py` |
| Viés nas recomendações | Auditoria por grupo (faixa etária, gênero, região) com limiar de disparidade 0,8 | `ml/fairness/`, `docs/responsible_ai.md` |
| Segredos no repositório | `.gitignore` cobre `.env*` e `secrets.toml`; nenhuma credencial no código | inspeção do repo |
| Regras de programa desatualizadas | Snapshot versionado com `verification_status` por fato; fail-safe: regra não confirmada → inelegível + revisão humana | `config/program_rules.yaml` |

## 4. Requisitos obrigatórios para uso com dados reais (pré-piloto)

1. **RIPD completo** por titularidade da Azul, aprovado pelo DPO/encarregado, antes de
   qualquer contato com titulares reais.
2. **Base legal definida** para cada tratamento (execução de contrato art. 7º, V;
   legítimo interesse art. 7º, IX com teste de necessidade/proporcionalidade).
3. **Minimização**: ingestão apenas dos campos do contrato de dados
   (`schemas/`); atributos sensíveis fora das features (mantém a arquitetura atual).
4. **Retenção e descarte** documentados por tabela; `data/raw` imutável com manifesto
   e prazos de expurso.
5. **Direitos dos titulares**: fluxos para acesso, correção, exclusão e portabilidade;
   capacidade de regenerar o pipeline sem um titular específico.
6. **Opt-out** de recomendação automatizada e revisão humana garantida (art. 20:
   direito à revisão de decisão automatizada).
7. **Monitoramento contínuo** de viés e incidentes; registro de decisões do agente
   (logs) com trilha de auditoria.
8. **Contratos de processadores** (Snowflake e eventuais fornecedores de LLM) com
   cláusulas LGPD; dados não saem da jurisdição acordada.
9. **Modo LLM**: se ativado com dados reais, proibir PII no prompt; avaliar
   processamento local ou contrato de confidencialidade do provedor.

## 5. Conclusão do MVP

O projeto **não trata dados pessoais reais**; riscos do MVP são de demonstração e
estão mitigados pelas medidas da seção 3. A arquitetura já implementa, por design, as
salvaguardas exigidas para o cenário real (seção 4).

> ⚠️ **Limitação declarada**: este documento NÃO constitui conformidade LGPD plena para
> operação com titulares reais — é a postura do MVP sintético + o roteiro de requisitos
> para o piloto real.
