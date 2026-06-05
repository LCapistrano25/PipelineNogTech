# Use a imagem oficial do Python como base
FROM python:3.13-slim

# Copia o binário do uv de sua imagem oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Configura o uv para não tentar usar hardlinks (melhora compatibilidade com volumes Docker)
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de configuração de dependências
COPY pyproject.toml uv.lock ./

# Instala as dependências do projeto usando uv
RUN uv sync --frozen

# Copia todo o código do projeto para o container
COPY . .

# Expõe a porta do Luigi Central Scheduler
EXPOSE 8082

# Cria as pastas necessárias para logs e bancos se não existirem
RUN mkdir -p logs databases output/loaded output/processed output/transformed output/final

# Comando para iniciar o Luigi Central Scheduler e a Pipeline
# Usamos 'uv run' para garantir que o ambiente virtual correto seja utilizado
CMD ["uv", "run", "python", "main.py"]
