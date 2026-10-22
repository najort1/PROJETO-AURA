# Deploy 100% gratuito do PROJETO AURA — Render.com (guia de execução)

> **Objetivo:** expor o cockpit Next.js (+ Aura Concierge com IA) em uma URL
> pública gratuita para avaliadores, **preservando 100% das funções**.
>
> **Resultado esperado:** `https://aura-dashboard.onrender.com` (ou nome similar,
> definido no painel da Render).

---

## 0. Por que Render.com?

| Critério | Render free | Vercel Hobby |
|---|---|---|
| Roda Next.js + rotas API (Node) | ✅ | ✅ |
| Roda **Python (Concierge + RAG)** no mesmo serviço | ✅ (Docker) | ❌ (sem processo Python) |
| Custo | $0 (750h/mês) | $0 |
| URL pública | ✅ (*.onrender.com) | ✅ (*.vercel.app) |
| Sleep | 15 min de inatividade → acorda ~1 min | n/a (serverless) |
| Redis/DB obrigatório | Nenhum | Nenhum |

O Concierge spawn a um processo Python (`agent.autonomous_bridge`) e conversa com
um gateway LLM **OpenAI-compatível**. A imagem Docker deste projeto já entrega os
dois runtimes (Node + Python via `uv`) em um único container.

---

## 1. Pré-requisitos (instruções executáveis)

1. **Chave gratuita de LLM (Groq):**
   - Acesse https://console.groq.com/keys → crie uma conta gratuita → **Create API Key**.
     Guarde a chave (formato `gsk_...`).
   - Modelos grátis com *function calling* já usados pelo AURA:
     `llama-3.3-70b-versatile` (padrão) ou `openai/gpt-oss-20b`.
     Limites free (típico): 30 req/min e ~1.000 req/dia por modelo — folgão para demo.

2. **Git / GitHub:**
   - O projeto está na branch `refactor/ux-telas`. Para o deploy, o ideal é
     publicar a branch principal. Se as telas já estão estáveis, faça merge ou
     aponte a Render para esta branch (ambiente funciona igualmente).

3. **Dados das telas (data/analytics)**
   - `.gitignore` exclui `data/analytics/`. Os `parquet` (scores, personas,
     timeline, SHAP, fairness) e o `decisions.jsonl` precisam entrar no repo.
   - São **dados sintéticos** (~16 MB) — sem nenhum dado pessoal. Já os
     adicionamos como `git add -f` (veja seção "Pré-deploy").

---

## 2. Pré-deploy (checagens que já executamos neste repo)

- [x] `Dockerfile` reescrito: estágio `runner` agora é `node:20-slim` + `uv` +
      **`.venv` Python** com runtime mínimo do agente
      (`pandas, numpy, duckdb, pydantic, PyYAML, scikit-learn, python-dotenv`).
- [x] `dashboard/src/app/api/concierge/chat/route.ts` agora usa
      `.venv/bin/python` (ou `Scripts/python.exe` no Windows) e cai para
      `uv run` apenas em dev. Garante que o spawn funciona na cloud.
- [x] `data/curated` é criado e liberado ao usuário `nextjs` no container —
      o índice TF-IDF do RAG (`rag_index`) é construído sob demanda no 1º chat.
- [x] `render.yaml` (Blueprint) pronto na raiz.
- [ ] **Você precisa confirmar:** `git add -f data/analytics/*.parquet
      data/analytics/*.json*` (comando já deixado pronto, seção 4).
- [ ] **Você precisa criar:** repositório GitHub remoto (`git remote add origin ...`)
      e fazer `push`.

---

## 3. Fluxo de deploy (passo a passo)

### 3.1_PUSH e Blueprint

```bash
git add -f data/analytics/customers_scores.parquet data/analytics/personas_summary.parquet \
           data/analytics/customer_timeline.parquet data/analytics/clv_shap.parquet \
           data/analytics/agent_recommendations.parquet data/analytics/friction_map.parquet \
           data/analytics/fairness_metrics.parquet data/analytics/decisions.jsonl \
           data/analytics/agent_input.parquet
# + quaisquer outros parquet usados pelas rotas (ver dashboard/src/lib/data/reader.ts)

git add Dockerfile render.yaml dashboard/src/app/api/concierge/chat/route.ts docs/deploy-render-free.md
git commit -m "chore(deploy): container portável Node+Python (Render free) e rota de chat inline-venv"
git remote add origin https://github.com/<SEU-USUARIO>/projeto-aura.git
git push -u origin HEAD
```
> ⚠️ **Nunca faça commit do `.env`** (a chave local e `AURA_LLM_BASE_URL=localhost`
> não funcionam na cloud). O `.gitignore` já o protege — apenas confirme.

### 3.2 Na Render

1. https://dashboard.render.com → **New +** → *Blueprint*.
2. Conecte a conta GitHub e selecione o repositório.
3. A Render detecta `render.yaml` → cria `aura-dashboard` (plano `free`).
4. Quando a Render pedir os valores de `sync:false`, informe:
   | Variável | Valor |
   |---|---|
   | `AURA_LLM_API_KEY` | `gsk_...` (sua chave Groq) |
   | `AURA_LLM_BASE_URL` | `https://api.groq.com/openai/v1` |
   | `AURA_LLM_MODEL` | `llama-3.3-70b-versatile` |
5. **Deploy automático** — build executa o Dockerfile (estágio builder Node +
   estágio runner Python). URL final aparece no topo do painel.

### 3.3 Validação (com o avaliador em mente)

| Teste | Rota | Resultado esperado |
|---|---|---|
| Saúde | `GET /api/health` | `{"status": "healthy", ...}` |
| Carteira | `/carteira` | KPIs + histograma Lorenz populados |
| Cliente 360 | `/cliente-360/<id>` | timeline + SHAP renderizados |
| Atritos / Personas / IA Responsável | telas | (mesma usabilidade) |
| Concierge (status da LLM) | `GET /api/concierge/chat` | `status:"online"` |
| Concierge (chat real) | `POST /api/concierge/chat` — msg: “quem está em maior risco?” | resposta do agente com citações/regulamento |
| Kanban | `/agente` | colunas sugeridas/revisão aprovada |

---

## 4. Truques do plano Free

- **Cold start:** 15 min sem requisição → 1 min de espera no primeiro acesso.
  Abra a URL 1-2 min antes da avaliação.
- **Memória (512 MB):** já configuramos `NODE_OPTIONS=--max-old-space-size=320`
  para o Node sobrar espaço ao Concierge (Python on-demand).
- **decisions.jsonl (Kanban):** persistência em disco não existe no free tier.
  Decisões feitas durante a sessão vivem até o serviço reiniciar (redeploy ou
  sleep). Se quiser persistir de fato, a recomendação é um stickiness via
  volume pago (não-freemium) ou banco grátis (ex. Neon) — fora do escopo atual.
- **Limites do Groq free:** 30 RPM / 1.000 req/dia (por modelo). Piscar a tema
  se você e os avaliadores usarem o concierge ao mesmo tempo durante horas.

---

## 5. Alternativa mais “sempre no ar” (opcional, ainda gratuita)

**Oracle Cloud Always Free** (VPS ARM ~4 vCPU / 24 GB, sem sleep):
- exige cartão de crédito para verificação (sem cobrança);
- sobe o `docker-compose.yml` deste repo sem mudanças;
- sleep de 15 min desaparece e o `decisions.jsonl` persiste via volume nomeado.

Se o prazo estiver apertado, Render (acima) resolve a **avaliação** em 30-40
minutos de configuração total.

---

## 6. Rollback / troubleshooting rápido

| Sintoma | Causa provável | Ação |
|---|---|---|
| Build falha em “COPY data/analytics” | parquet não commitados | rode `git add -f` (seção 3.1) |
| Telas vazias | parquet ausentes no repo | mesmo acima |
| `GET /api/concierge/chat` → `offline` | LLM base URL errada / chave inválida | revise `AURA_LLM_*` nas *Environment* da Render |
| Chat “motor autônomo não produziu resposta” | timeout (Groq demorou) ou falha de import Python | foram 180s; valide nos logs “Logs” da Render |
| 502 / service unresponsive | serviço dormindo | aguarde ~1 min (acorda sozinho na 1ª requisição) |
