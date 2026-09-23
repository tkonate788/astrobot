# ── AstroBot Admin Dashboard — Dockerfile ─────────────────────
FROM node:18-alpine

LABEL maintainer="AstroBot Team"
LABEL description="AstroBot Admin Dashboard (port 7040)"
LABEL version="1.0.0"

RUN apk add --no-cache dumb-init

RUN addgroup -g 1002 -S adminbot && \
    adduser  -u 1002 -S adminbot -G adminbot

WORKDIR /app

# Copy + install deps
COPY admin/backend/package*.json ./
RUN npm install --omit=dev --silent && npm cache clean --force

# Copy app source
COPY admin/backend/ .

# Shared modules (LLM provider catalog / client / crypto)
COPY shared/ ./shared/

# Permissions
RUN chown -R adminbot:adminbot /app
USER adminbot

EXPOSE 7040

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD node -e "require('http').get('http://localhost:7040/api/health', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1)).on('error', () => process.exit(1))"

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["node", "server.js"]
