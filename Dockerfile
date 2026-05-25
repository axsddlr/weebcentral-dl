FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY src/frontend/package*.json ./
RUN npm ci

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

# Copy backend source and bootstrap files
COPY src/ ./src/
COPY server.py entrypoint.sh example.config.toml ./

# Copy built frontend into FastAPI static web directory
COPY --from=frontend-builder /frontend/dist/ ./src/web/

# Runtime data directory + non-root user in one layer
RUN mkdir -p manga_downloads \
    && adduser --disabled-password --gecos "" --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
