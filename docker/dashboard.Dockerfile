FROM python:3.12-slim

# Instala o uv para gerenciamento rápido e otimizado de dependências
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

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

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Define variáveis de ambiente do Streamlit para rodar em produção de forma não interativa
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV PYTHONPATH=/app

# Executa o dashboard Streamlit por meio do uv
CMD ["uv", "run", "streamlit", "run", "src/dashboard/app.py", "--server.port", "8501", "--server.headless", "true"]
