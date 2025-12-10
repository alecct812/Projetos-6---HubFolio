FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar MLflow e dependências
RUN pip install --no-cache-dir \
    mlflow==2.11.3 \
    psycopg2-binary \
    boto3

# Criar diretório para artifacts
RUN mkdir -p /mlflow/artifacts

# Expor porta do MLflow
EXPOSE 5000

# Comando padrão (será sobrescrito pelo docker-compose)
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]

