# 🔌 Fase 5: API de Exposição (FastAPI)

Este documento descreve as especificações técnicas, padrões de rotas (REST) e validações de dados necessárias para criar a API de backend usando o framework FastAPI.

---

## 🎯 Objetivos Concluídos (Fase 5)
* **Construir uma API REST assíncrona, robusta e rápida** com FastAPI.
* **Ler os dados consolidados** dos arquivos Parquet (`pam_parana_consolidado.parquet` e clusters).
* **Implementar validação estrita** de tipos na entrada e saída com **Pydantic**.
* **Expor endpoints parametrizados** para prover séries históricas, rankings e clusters.
* **Habilitar documentação interativa automática** no Swagger UI na rota `/docs`.

---

## 🛠️ Endpoints Mínimos Requeridos

### 1. `GET /health`
* **Descrição:** Healthcheck simples para monitorar se a API está no ar (essencial para monitoramento e orquestração do Docker).
* **Retorno:** JSON simples (ex: `{"status": "ok"}`).

### 2. `GET /metadata`
* **Descrição:** Retorna as listas de valores únicos presentes na base para que o Dashboard Streamlit possa desenhar seus filtros dinamicamente.
* **Retorno:** Produtos disponíveis, anos disponíveis, e municípios disponíveis (nome e código).

### 3. `GET /series`
* **Parâmetros:** `produto: str` (opcional), `municipio_codigo: int` (opcional).
* **Descrição:** Retorna a série histórica de produção anual (2010 a 2024) para a combinação selecionada.
* **Retorno:** Lista de dicionários com ano, variáveis físicas e financeiras da lavoura.

### 4. `GET /ranking`
* **Parâmetros:** `produto: str` (obrigatório), `ano: int` (obrigatório), `metric: str` (opcional - padrão: 'quantidade_produzida', opções: 'quantidade_produzida', 'area_plantada', 'area_colhida', 'rendimento_medio', 'valor_producao').
* **Descrição:** Retorna a lista dos maiores municípios produtores com base na métrica especificada.
* **Retorno:** Lista ordenada contendo nome do município, código e o valor correspondente.

### 5. `GET /clusters`
* **Parâmetros:** `produto: str` (obrigatório).
* **Descrição:** Retorna o agrupamento final dos municípios e um resumo descritivo das médias das features para cada cluster daquela cultura.
* **Retorno:** Resumos descritivos por cluster e a listagem de municípios classificados.

---

## 📝 Blueprint da Nova Arquitetura Modular

Para garantir manutenibilidade, extensibilidade e facilidade de testes, a API foi refatorada para uma **Arquitetura em Camadas (Layered Architecture)**:

```text
src/api/
├── __init__.py
├── main.py             # Configuração global, lifespan e registro dos routers
├── schemas.py          # Contratos Pydantic de entrada e saída
├── services.py         # Camada de Serviço (Pandas queries, cache e Fail-Fast)
└── routers/
    ├── __init__.py     # Inicialização de pacote
    ├── system.py       # Endpoints administrativos (/health, /metadata)
    └── analytics.py    # Endpoints de negócio (/series, /ranking, /clusters)
```

### 1. Camada de Serviço ([services.py](../src/api/services.py))
Responsável por encapsular a manipulação de dados (Pandas) e o cache global em memória (`data_store`). Os endpoints não realizam operações diretas de dados, apenas invocam os métodos estáticos da classe `DataService`. Implementa validações robustas e o padrão Fail-Fast (lançando exceções no startup se os dados cruciais estiverem ausentes). Os contratos de entrada e saída são definidos em [schemas.py](../src/api/schemas.py).

### 2. Camada de Rotas (Routers)
Desacopla as URLs e as regras de controle do FastAPI:
* **[system.py](../src/api/routers/system.py)**: Gerencia endpoints utilitários como `/health` e `/metadata`.
* **[analytics.py](../src/api/routers/analytics.py)**: Gerencia consultas de séries temporais, ordenação de rankings e dados de clusters.

### 3. Arquivo Principal ([main.py](../src/api/main.py))
Fica responsável estritamente por instanciar o `FastAPI`, gerenciar o ciclo de vida (`lifespan`) para carga e limpeza de cache, e acoplar os routers modulares por meio do método `app.include_router()`.
