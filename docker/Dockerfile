# ── AstroBot — Production Dockerfile ──────────────────────────
# Node 18 Alpine for minimal image size
FROM node:18-alpine

# Add metadata labels
LABEL maintainer="AstroBot Team"
LABEL authors="Tidiane Konaté, Sidi Mohamed Sall, Ahmed Essalem, Saad Ibrahim Houssein"
LABEL description="AstroBot — Intelligent Space Assistant (University graduation project)"
LABEL version="2.0.0"

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user for security
RUN addgroup -g 1001 -S astrobot && \
    adduser  -u 1001 -S astrobot -G astrobot

# Set working directory
WORKDIR /app

# Copy package files first (layer caching)
COPY backend/package*.json ./

# Install production dependencies only
RUN npm install --omit=dev --silent && \
    npm cache clean --force

# Copy backend source
COPY backend/ .

# Copy frontend into public/ (served as static files)
COPY frontend/ ./public/

# Shared modules (LLM provider catalog / client / crypto)
COPY shared/ ./shared/

# Set permissions
RUN chown -R astrobot:astrobot /app

# Switch to non-root user
USER astrobot

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1)).on('error', () => process.exit(1))"

# Use dumb-init to handle PID 1 and signal forwarding
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Start the server
CMD ["node", "server.js"]
