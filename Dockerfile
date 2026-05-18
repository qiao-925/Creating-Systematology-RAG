# ============================================================
# Stage 1: Build Next.js frontend (standalone mode)
# ============================================================
FROM node:20-slim AS frontend-builder

WORKDIR /build/web

# Install dependencies first (layer cache)
COPY web/package.json web/package-lock.json ./
RUN npm ci

# Copy source and build
COPY web/ ./
RUN npm run build

# Prune to production-only node_modules
RUN npm ci --omit=dev

# ============================================================
# Stage 2: Python runtime + backend
# ============================================================
FROM python:3.12-slim

# HF Spaces: run as non-root user (uid 1000)
RUN useradd -m -u 1000 user

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Install Python dependencies (layer cache)
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy backend code
COPY --chown=user backend/ backend/
COPY --chown=user application.yml ./
COPY --chown=user scripts/ scripts/
COPY --chown=user data/ data/
COPY --chown=user skills/ skills/

# Copy Next.js standalone build from Stage 1
COPY --chown=user --from=frontend-builder /build/web/.next/standalone/web/ web/.next/standalone/
COPY --chown=user --from=frontend-builder /build/web/.next/static/ web/.next/standalone/.next/static/
COPY --chown=user --from=frontend-builder /build/web/public/ web/.next/standalone/public/

# Copy startup script
COPY --chown=user start.sh ./
RUN chmod +x start.sh

# Switch to non-root user
USER user

# HF Spaces uses port 7860
EXPOSE 7860

CMD ["bash", "start.sh"]
