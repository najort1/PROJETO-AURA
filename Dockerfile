# =============================================================================
# PROJETO AURA 2.0 - Dockerfile do Cockpit Executivo (Next.js 15)
#
# Arquitetura:
#   deps / builder -> Node 20 Alpine (build do Next.js)
#   runner         -> Node 20 Debian-slim (glibc) + ambiente Python do
#                     Aura Concierge via uv (o chat spawn
#                     `python -m agent.autonomous_bridge` na mesma imagem)
# =============================================================================

# Estágio Base com Node 20 e pnpm habilitado (estágios de build)
FROM node:20-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

# -----------------------------------------------------------------------------
# 1. Dependências
# -----------------------------------------------------------------------------
FROM base AS deps
WORKDIR /app
RUN apk add --no-cache libc6-compat
COPY dashboard/package.json dashboard/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# -----------------------------------------------------------------------------
# 2. Builder
# -----------------------------------------------------------------------------
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY dashboard/ ./
RUN mkdir -p /app/public
# Disponibiliza artefatos curados em data/analytics para pré-renderização de Server Components
COPY data/analytics ./data/analytics
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN pnpm run build

# -----------------------------------------------------------------------------
# 3. Runner de Produção (Node + Python do Concierge)
#    Debian-slim (glibc) para compatibilidade total dos wheels Python
#    (duckdb, pandas, numpy, scikit-learn) executados em um único container.
# -----------------------------------------------------------------------------
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
# Teto de heap do V8 para comportar o plano Free da Render (512 MB) mesmo com
# o processo Python do Concierge rodando em paralelo durante o chat.
ENV NODE_OPTIONS="--max-old-space-size=320"

# Certificados TLS + variáveis do uv (gerenciador Python da Astral)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_CACHE_DIR=/opt/uv-cache \
    UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    UV_PYTHON_DOWNLOADS=manual \
    UV_NO_SYNC=true \
    HOME=/home/nextjs

# 3.1 Ambiente Python do Aura Concierge (criado no build; rodando via venv direto)
#     Deps são o runtime mínimo dos módulos agent/* e aura_core/*:
#     duckdb (ferramentas de dados), pandas+numpy (parquet/RAG),
#     scikit-learn (TfidfVectorizer do RAG), pydantic (modelos), PyYAML (config),
#     python-dotenv (compat do .env local).
RUN uv python install 3.12 && \
    uv venv /app/.venv --python 3.12 && \
    uv pip install --python /app/.venv/bin/python \
        "pandas>=2.2,<3" \
        "numpy>=1.26" \
        "duckdb>=1.1" \
        "pydantic>=2.7" \
        "PyYAML>=6.0" \
        "scikit-learn>=1.5" \
        "python-dotenv>=1.0"

# pyproject.toml fica disponível caso algum caminho use `uv run` como fallback
COPY pyproject.toml ./

# Segurança: usuário não-root (princípio de menor privilégio)
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs --home /home/nextjs nextjs

# Cria diretórios de dados com permissão de escrita para o dual-write de
# decisions.jsonl, estáticos e a construção do índice TF-IDF do RAG
# (data/curated/rag_index), gerado sob demanda no primeiro uso do Concierge.
RUN mkdir -p public data/analytics data/curated && chown -R nextjs:nodejs /app /home/nextjs

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/next.config.mjs ./next.config.mjs
COPY --from=builder --chown=nextjs:nodejs /app/data/analytics ./data/analytics

# Fonte do Concierge (Python) + configuração de negócio (RAG/actions/program rules)
COPY --chown=nextjs:nodejs agent ./agent
COPY --chown=nextjs:nodejs aura_core ./aura_core
COPY --chown=nextjs:nodejs schemas ./schemas
COPY --chown=nextjs:nodejs config ./config

USER nextjs

EXPOSE 3000

CMD ["node_modules/.bin/next", "start"]
