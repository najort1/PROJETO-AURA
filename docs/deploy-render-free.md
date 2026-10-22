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

1. **API de LLM gratuita — escolha 1 principal (+ 1 reserva).** O agente fala o
   padrão OpenAI (`tools`/`tool_calls`); os provedores abaixo são 100% grátis e
   OpenAI-compatíveis. **Por que sair do Groq:** o free deles é 30 RPM /
   **8.000 TPM** / 1.000 RPD por modelo — os schemas das 8 ferramentas + contexto
   RAG somam 10-20k tokens por turno do loop ReAct, então o TPM estoura já no
   2º-3º uso.

      **Recomendado (principal) — NVIDIA NIM (build.nvidia.com), sem cartão:**
   - Key grátis com conta NVIDIA Developer: https://build.nvidia.com/explore/discover
     → botão "Get API Key" (formato `nvapi-...`).
   - `AURA_LLM_BASE_URL` = `https://integrate.api.nvidia.com/v1`
   - `AURA_LLM_MODEL` = `meta/llama-3.3-70b-instruct` (contexto 128k, function calling OpenAI)
   - Limites free: ~40 RPM e teto diário de até 10.000 req/dia por modelo
     (varia por modelo — o limite exato aparece no canto superior do build.nvidia.com).

   **Reserva automática — Cloudflare Workers AI (300 RPM em text-gen):**
   - Free: **10.000 neurons/dia**, sem cartão. O `agent/llm.py` do AURA agora faz
     **fallback automático** para este provedor quando o principal esgotar/travar
     (HTTP 429/5xx) — configure os 3 envs `AURA_LLM_FALLBACK_*` na Render.
   - Crie um API Token (dash.cloudflare.com → API Tokens → permissão *Workers AI*)
     e copie seu `Account ID` (Home → Workers & Pages, coluna lateral).
   - `AURA_LLM_FALLBACK_BASE_URL` = `https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/ai/v1`
   - `AURA_LLM_FALLBACK_API_KEY` = `<API token>`
   - `AURA_LLM_FALLBACK_MODEL` = `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
     (function calling OpenAI-compat confirmado; contexto 24k; ~20 conversas
     completas/dia no free — contingência do dia de avaliação).
     Alternativa mais barata em neurons/dia: `@cf/qwen/qwen3-30b-a3b-fp8`.

   **Por que NÃO o Gemini como principal (dado 2026):** o free tier foi apertado
   (flash peregrino medido em ~5 RPM / 20 RPD por trackers) e Google não publica
   mais cotas — risco alto para o dia da demo.

   **Também reaproveitável — Groq (só perguntas curtas):**
   - `AURA_LLM_BASE_URL` = `https://api.groq.com/openai/v1` + `llama-3.1-8b-instant`,
     key em https://console.groq.com/keys. Free: 30 RPM / 8.000 TPM / 1.000 RPD —
     não sirva como principal: estoura TPM já no 2º-3º uso do Concierge.

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
   | `AURA_LLM_API_KEY` | `nvapi-...` (chave NVIDIA NIM) |
   | `AURA_LLM_BASE_URL` | `https://integrate.api.nvidia.com/v1` |
   | `AURA_LLM_MODEL` | `meta/llama-3.3-70b-instruct` |
   | `AURA_LLM_FALLBACK_BASE_URL` | `https://api.cloudflare.com/client/v4/accounts/<ID>/ai/v1` |
   | `AURA_LLM_FALLBACK_API_KEY` | API Token Cloudflare (Workers AI) |
   | `AURA_LLM_FALLBACK_MODEL` | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` |
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
- **Limites da malha LLM (2026):** principal NVIDIA NIM ~40 RPM e até ~10.000
  req/dia; reserva Cloudflare 300 RPM e 10.000 neurons/dia (consumo no dash →
  Workers AI, reset à meia-noite UTC). Juntas, fecham um dia de avaliação
  com folga zerando custo.

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
