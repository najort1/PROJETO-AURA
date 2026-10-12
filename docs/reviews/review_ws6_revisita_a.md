# Revisão Independente — WS6 Revisita (Parte A: Métricas e Relatório)

> **Projeto Aura 2.0** — Pipeline Reproduzível de Inteligência de Clientes e Retenção do Azul Fidelidade  
> **Frente:** Workstream 6 (WS6 · Sentimento por Aspecto e Mapa de Atritos) — Re-auditoria pós-correções do Lead  
> **Revisor:** Revisor Independente Adversarial  
> **Data:** 12 de Outubro de 2026  
> **Escopo:** Verificação exclusiva dos itens A1–A4 (métricas, honestidade, coerência, adversarial). Parte B (código/artefatos) a cargo de outro revisor.

---

## Veredito Parcial da Parte A

**APROVADO (Parte A)** — Itens A1, A2, A3 **CONFORME**; item A4 tem achado **MENOR** (inconsistência narrativa no log de correções §6.1, sem impacto em métricas ou conclusões). Todos os IMPORTANTES estão resolvidos.

---

## Tabela de Verificações (A1–A4)

| Item | Verificação | Evidência | Status |
|------|-------------|-----------|--------|
| A1 | Métricas do relatório vs execução real | Execução de `run_evaluation()`: Lexicon P=0.6071, R=0.6315, κ=0.4169; TF-IDF P=0.8236, R=0.8747, κ=0.7924; inter-κ=0.3804. Deltas: +0.2165 (P), +0.2432 (R). Matrizes de confusão gerais (Lex: [[161,91,6],[12,25,24],[0,11,68]]; TF-IDF: [[230,26,2],[5,47,9],[0,3,76]]) e por aspecto (ex.: atraso Lex [[219,63],[0,116]], TF-IDF [[282,0],[0,116]]; preco Lex [[260,71],[0,67]], TF-IDF [[331,0],[1,66]]) conferem **exatamente** com §3.2, §3.3 e §1 item 3 do relatório. | ✅ CONFORME |
| A2 | Nota de honestidade sobre F1≈1,0 em §3.1 | Presente em §3.1 (linha 71-72 do relatório), após a tabela de F1 por aspecto. Texto: "o corpus sintético é gerado a partir de famílias limitadas de templates por aspecto (~16 variações léxicas por aspecto). Nesse regime, um F1 de presença próximo de 1,0 (TF-IDF) é um resultado quase-trivial esperado — a métrica valida a corretude mecânica do pipeline..., não a habilidade de NLP em linguagem natural espontânea." Redação adequada, clara e posicionada corretamente. | ✅ CONFORME |
| A3 | Coerência §4 vs friction_map.parquet | Parquet tem 49 linhas (7 aspectos × 7 semestres 2023-S2 a 2026-S2). Intensidades médias: atraso 0.8022, atendimento 0.7518, bagagem 0.7488, resgate_milhas 0.7427, app_checkin 0.6629, preco 0.5967, conforto 0.4275 — conferem com tabela §4. Totais: 2.074 menções, 1.386 negativas, 66.83% taxa — conferem. Tendências: resgate crescente, app decrescente, demais estáveis — conferem. Série semestral "Dinâmica Temporal": resgate 0.6643→0.8190 (2026-S1) e 0.7694 (2026-S2); app pico 0.8174 (2024-S1)→0.5991/0.5322; atraso picos 0.8810 (2023-S2) e 0.8625 (2024-S2), vale 0.6844 (2025-S2) — todos conferem com dados do parquet. Pesos somam 1.0000. | ✅ CONFORME |
| A4 | Adversarial: números sem lastro/contradições | Leitura atenta de todo o `sentiment_report.md` cruzando §1, §2, §3.1, §3.2, §3.3, §4, §5, §6. **Consistência interna excelente**: todos os números principais (métricas §3.2, matrizes §3.3, intensidades/pesos/tendências §4, pesos §5.1) conferem entre si e com os artefatos (parquet, json, execução real). **Achado MENOR**: §6.1 item 3 afirma "desvio máximo de peso: app_checkin -0,0040" na recálculo pós-correção de binning; porém, comparando os pesos reportados na revisão original (`review_ws6.md`: app_checkin=0,1645) com os atuais (`friction_weights.json`/relatório: app_checkin=0,1411), o desvio real é -0,0234. O valor -0,0040 não tem lastro observável nos artefatos comparáveis; pode referir-se a estado intermediário não documentado. Não afeta métricas principais nem conclusões. Severidade: **MENOR**. | ⚠️ MENOR |

---

## Achados Novos

| ID | Severidade | Componente | Descrição |
|----|------------|------------|-----------|
| **REV-A-01** | **MENOR** | `docs/sentiment_report.md` §6.1 item 3 | Valor de "desvio máximo de peso: app_checkin -0,0040" no log de correções não corresponde ao delta observável entre revisão original (0,1645) e versão atual (0,1411), que é -0,0234. Inconsistência narrativa no registro de correções, sem impacto nas métricas validadas (A1–A3). Recomenda-se alinhar o texto do §6.1 com o delta real ou clarificar a base de comparação. |