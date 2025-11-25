# Dockerfile para Neoson Reborn
# Baseado em Python 3.10 (compatível com a maioria das libs atuais)
FROM python:3.10-slim

# Definir diretório de trabalho
WORKDIR /app

# Variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependências do sistema necessárias para psycopg2 e outros
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de requisitos
COPY requirements.txt .
COPY requirements_fastapi.txt .

# Instalar dependências Python
# Combina os dois arquivos e instala
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_fastapi.txt && \
    pip install uvicorn gunicorn

# Copiar o código da aplicação
COPY . .

# Expor a porta que o FastAPI usará
EXPOSE 8000

# Comando para iniciar a aplicação
# Usa gunicorn como gerenciador de processos com workers uvicorn para produção
CMD ["gunicorn", "app_fastapi:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
