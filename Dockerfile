FROM node:26-alpine AS frontend-builder

WORKDIR /frontend

COPY src/frontend/package*.json ./
RUN for i in 1 2 3; do echo "npm ci attempt $i"; npm ci && break || sleep 5; done

COPY src/frontend/ ./
RUN npm run build


FROM python:3.11-slim AS runtime

WORKDIR /app

LABEL org.opencontainers.image.description="Web UI and CLI for downloading manga from WeebCentral as CBZ/ZIP archives"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install uv for fast, reproducible dependency installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Install Playwright browsers required by scrapling StealthyFetcher
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && uv run scrapling install --force

# Copy backend source and bootstrap files
COPY src/ ./src/
COPY server.py entrypoint.sh example.config.toml ./

# Copy built frontend into FastAPI static web directory
COPY --from=frontend-builder /frontend/dist/ ./src/web/

# Runtime data directory + non-root user in one layer
RUN chmod +x entrypoint.sh \
    && mkdir -p manga_downloads \
    && adduser --disabled-password --gecos "" --uid 1000 appuser \
    && chown -R appuser:appuser /app

EXPOSE 8000

# Entrypoint runs as root to fix bind-mount permissions, then drops to appuser
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
