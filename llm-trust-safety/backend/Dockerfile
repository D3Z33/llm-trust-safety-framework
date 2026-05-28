FROM python:3.12-slim

WORKDIR /app

# Instala curl para healthcheck e limpa cache
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Usuário não-root para reduzir superfície de ataque
RUN useradd --create-home --shell /bin/bash appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck — verifica /health a cada 30s, falha após 3 tentativas
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]
