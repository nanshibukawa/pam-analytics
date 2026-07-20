# 🐳 Fase 7: Containerização e Orquestração (Docker)

Este documento detalha o processo de empacotamento da aplicação em containers Docker e a orquestração multi-serviços utilizando o Docker Compose.

---

## 🎯 Objetivos
1. Criar imagens Docker dedicadas e otimizadas para o Backend (FastAPI) e Frontend (Streamlit).
2. Utilizar boas práticas de Docker, como **imagem base slim** para reduzir o tamanho e o tempo de build das imagens.
3. Configurar uma rede compartilhada interna do Docker para que os containers se comuniquem por meio do DNS interno.
4. Mapear as portas locais corretas: `8000` para a API e `8501` para o Dashboard.
5. Permitir inicializar o projeto completo com um único comando: `docker compose up --build`.

---

## ⚠️ Ponto Crítico de Atenção: Rede Interna no Docker

Quando rodamos o app localmente, o Streamlit acessa a API usando `http://localhost:8000`. 
* Porém, dentro de um container Docker, `localhost` refere-se ao **próprio container do Streamlit**, e não à máquina host ou ao container da API.
* **A Solução:** No Docker Compose, nomeamos o serviço da API como `api`. O Docker cria um servidor DNS interno automático. Assim, dentro da rede do Docker, o container do Streamlit consegue alcançar a API usando o endereço **`http://api:8000`**.
* **Tratamento Dinâmico:** No código do cliente da API ([api_client.py](../src/dashboard/api_client.py)), lemos a URL da API a partir de uma variável de ambiente (ex: `os.getenv("API_BASE_URL", "http://localhost:8000")`). Isso permite que localmente ele aponte para `localhost` e no Docker mude dinamicamente para `http://api:8000`.

---

## 📝 Estrutura de Containerização

Para evitar divergências entre a documentação e os arquivos de configuração que mudam constantemente durante o ciclo de desenvolvimento, os arquivos de infraestrutura são mantidos e versionados diretamente nos caminhos indicados abaixo.

### 1. Dockerfile da API ([api.Dockerfile](../docker/api.Dockerfile))
A imagem do Backend é construída a partir deste arquivo e segue as seguintes boas práticas:
* **Imagem Base Slim:** Utiliza `python:3.12-slim` para diminuir o tamanho final e acelerar o deploy.
* **Instalação com `uv`:** O gerenciador de pacotes ultrarrápido `uv` é copiado diretamente de sua imagem oficial para sincronizar e instalar as dependências de forma otimizada utilizando cache do Docker.
* **Resolução de Módulos:** Define `PYTHONPATH=/app` para garantir a correta importação do pacote `src` sem problemas de caminhos relativos.

### 2. Dockerfile do Dashboard ([dashboard.Dockerfile](../docker/dashboard.Dockerfile))
A imagem do Frontend (Streamlit) é configurada de forma independente:
* **Configurações de Produção:** Define variáveis de ambiente dedicadas para o Streamlit rodar em modo headless (`STREAMLIT_SERVER_HEADLESS=true`), porta `8501` e sem coleta de estatísticas de uso.
* **Ambiente Isolado:** Semelhante à API, utiliza o `uv` para a instalação limpa e congelada (`--frozen`) do ambiente.

### 3. Orquestração ([docker-compose.yml](../docker-compose.yml))
Gerencia a inicialização, a comunicação por rede privada e o ciclo de vida conjunto dos serviços.

#### Pontos de Destaque na Configuração:
* **Suporte a Hot-Reload:** Em ambiente de desenvolvimento, ambos os serviços montam o diretório local `./src` para `/app/src`. A API sobrescreve seu comando de entrada padrão para executar `src/api/main.py` com o Uvicorn em modo `reload=True`.
* **Healthcheck sem Dependências de Rede:** Como utilizamos imagens base `slim` que não possuem ferramentas de rede como `curl` ou `wget`, a verificação de saúde da API é feita usando um script inline de Python:
  ```yaml
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
  ```
* **Ordem de Inicialização Inteligente:** O Dashboard possui uma dependência estrita da saúde da API (`service_healthy`), garantindo que o painel Streamlit só inicie após a API ter carregado com sucesso toda a base de dados histórica em memória.

---

## 🚀 Comandos Úteis

Para inicializar todo o ecossistema com suporte a hot-reload:
```bash
docker compose up --build
```

Para desligar os serviços e limpar os volumes:
```bash
docker compose down -v
```
