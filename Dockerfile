# =============================================================================
# PROJETO AURA 2.0 - Dockerfile do Cockpit Executivo (Next.js 15)
# Base: Node 20 Alpine | Gerenciador: pnpm (Corepack)
# =============================================================================

# Estágio Base com Node 20 Alpine e pnpm habilitado
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
# 3. Runner de Produção
# -----------------------------------------------------------------------------
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Segurança: usuário não-root (princípio de menor privilégio)
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Cria diretórios de dados com permissão de escrita para o dual-write de decisions.jsonl e estáticos
RUN mkdir -p public data/analytics && chown -R nextjs:nodejs /app

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/next.config.mjs ./next.config.mjs
COPY --from=builder --chown=nextjs:nodejs /app/data/analytics ./data/analytics

USER nextjs

EXPOSE 3000

CMD ["node_modules/.bin/next", "start"]
