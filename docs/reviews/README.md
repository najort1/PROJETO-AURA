# Protocolo de revisão independente (obrigatório)

> Nenhuma frente é considerada aprovada pelo próprio autor. O ciclo de cada componente:
> **especificar → implementar → revisar (independente) → testar → corrigir → reavaliar → aprovar (Lead)**.

## 1. Quem revisa

- **Revisor independente**: subagente `mega-brain` SEM envolvimento com a implementação
  da frente; recebe a especificação (task no quadro) + os artefatos produzidos e é
  instruído a procurar problemas DELIBERADAMENTE — nunca a confirmar que está tudo certo.
- **Lead**: integra achados, decide, reitera correções e é o único que aprova.

## 2. Checklist por frente (o revisor preenche com evidências)

| # | Verificação | Evidência exigida |
|---|---|---|
| 1 | Requisitos da task cumpridos um a um | Mapa entregável × arquivo × comando |
| 2 | Fail-loud real (sem except-pass/fallback silencioso) | grep de `except` + casos de erro executados |
| 3 | Determinismo (seeds; re-execução reproduz) | Hash de saídas antes/depois |
| 4 | Contratos de dados válidos (schemas + validate) | Saída do validador |
| 5 | Anti-vazamento temporal (features/métricas) | Testes + inspeção SQL/dbt + tentativa de quebrar |
| 6 | Métricas corretas (fórmulas) | Recálculo independente em amostra |
| 7 | Números do relatório = números executados | Cruzamento relatório × artefatos |
| 8 | Honestidade (premissas rotuladas; limitações declaradas) | Leitura crítica dos docs |
| 9 | LGPD/viés (sensíveis fora de features; mensagens limpas) | Testes + grep |
| 10 | Integridade RAG/eligibilidade (citações reais; fail-safe null) | Testes + amostras manuais |
| 11 | Segurança (injection, caminhos, segredos fora do repo) | Testes adversariais + inspeção |
| 12 | Ruff + pytest verdes com saída real | Execução pelo revisor (não confiar no relatório) |

## 3. Revisão de sistema (após todas as frentes)

- `python tasks.py all` do zero (estado limpo) reproduz tudo?
- Integração cruzada: app lê analytics real; agente cita fact_ids reais; KPIs do app
  batem com os parquet; demo script corresponde ao app.
- Documentação coerente com o comportamento real (comandos testados).
- Revisão de segurança/LGPD dedicada (dados sintéticos, sem segredos, RIPD).

## 4. Registro

- Cada revisão produz `docs/reviews/review_<frente>.md`: achados classificados
  [CRÍTICO | IMPORTANTE | MENOR | OBSERVAÇÃO], evidências e veredito.
- CRÍTICO e IMPORTANTE bloqueiam a aprovação até correção + reavaliação.
- O Lead mantém o quadro de tarefas como fonte de estado.
