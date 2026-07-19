FROM python:3.12-slim

# Instala o uv para gerenciamento rápido e otimizado de dependências
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instala as dependências sem instalar o projeto pam-analytics de forma a otimizar cache
RUN uv sync --frozen --no-cache --no-install-project

# Copia o código fonte para dentro do container
COPY src/ ./src/

# Instala o projeto pam-analytics no ambiente sincronizado
RUN uv sync --frozen --no-cache

# Define PYTHONPATH para garantir que o python encontre o módulo src a partir da raiz
ENV PYTHONPATH=/app

# Expõe a porta padrão do FastAPI
EXPOSE 8000

# Executa o servidor ASGI uvicorn diretamente do ambiente virtual (evita overhead do uv run e garante signal handling correto)
CMD ["/app/.venv/bin/uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
