# ── Stage 1: build the React frontend ────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci --silent

COPY frontend/ ./
RUN npm run build


# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY backend/ ./backend/

# Deploy built frontend into backend/static/ (mirrors install.sh logic)
RUN mkdir -p backend/static/assets
COPY --from=frontend-builder /build/frontend/dist/index.html backend/static/
COPY --from=frontend-builder /build/frontend/dist/assets/    backend/static/assets/

# Install Python package (no venv needed inside container)
RUN pip install --no-cache-dir .

# Hermes data directory — mount your ~/.hermes here at runtime
VOLUME ["/root/.hermes"]

EXPOSE 3001

ENV HERMES_HOME=/root/.hermes

CMD ["hermes-hudui", "--host", "0.0.0.0", "--port", "3001"]
```
