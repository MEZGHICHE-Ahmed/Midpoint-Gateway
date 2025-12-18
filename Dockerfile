# Stage 1: Build
FROM python:3.13-slim as builder

WORKDIR /app

# Installe les dépendances de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie les requirements
COPY requirements.txt .

# Installe les dépendances Python
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Crée un utilisateur non-root pour sécurité
RUN useradd -m -u 1000 appuser

# Copie les dépendances depuis le builder
COPY --from=builder /root/.local /home/appuser/.local

# Copie le code de l'application
COPY --chown=appuser:appuser . .

# Définit les variables d'environnement
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch vers l'utilisateur non-root
USER appuser

# Port d'écoute
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Lance l'application
CMD ["uvicorn", "gateway.api.http:app", "--host", "0.0.0.0", "--port", "8000"]
