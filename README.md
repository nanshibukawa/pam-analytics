# PAM Analytics - Clusterização Agrícola do Paraná

Plataforma analítica ponta a ponta projetada para a ingestão de dados históricos da Pesquisa Agrícola Municipal (PAM) via API SIDRA/IBGE, engenharia de features temporais, modelagem não supervisionada (clusterização de perfis produtivos de soja, milho e trigo) e exposição dos resultados através de um ecossistema com API (FastAPI) e interface visual (Streamlit), totalmente containerizado com Docker Compose.

---

## 🏗️ Arquitetura do Projeto

O projeto adota uma estrutura modular focada em boas práticas de engenharia de software (Clean Code, separação de responsabilidades e reprodutibilidade):

```text
pam-analytics/
├── data/                            # Diretório de dados (raw e processed)
├── docker/                          # Configurações de containerização (Dockerfiles)
├── src/                             # Código-fonte principal do projeto
│   ├── ingestion/                   # Módulo de Ingestão e Iniciação de dados (SIDRA API)
│   ├── features/                    # Módulo de Engenharia de Features temporais
│   ├── models/                      # Módulo de Modelagem e Clusterização (K-Means)
│   ├── api/                         # Módulo de Exposição de dados (FastAPI)
│   └── dashboard/                   # Interface Gráfica Interativa (Streamlit)
├── tests/                           # Suíte de testes automatizados (pytest)
├── docker-compose.yml               # Orquestração local dos containers
└── pyproject.toml                   # Gerenciamento de dependências e padrões (Ruff)
```

---

## 📖 Documentação Detalhada das Fases

Para compreender a fundo os detalhes técnicos, as regras de negócios e as decisões arquiteturais de cada etapa do ecossistema, consulte as documentações dedicadas:

*   **Fase 2 (Ingestão & Sanitização):** [docs/fase2_ingestao.md](docs/fase2_ingestao.md)
*   **Fase 3 (Engenharia de Features):** [docs/fase3_features.md](docs/fase3_features.md)
*   **Fase 4 (Modelagem & Clusterização):** [docs/fase4_modelagem.md](docs/fase4_modelagem.md)
*   **Fase 5 (API FastAPI):** [docs/fase5_api.md](docs/fase5_api.md)
*   **Fase 6 (Dashboard Streamlit):** [docs/fase6_dashboard.md](docs/fase6_dashboard.md)
*   **Fase 7 (Docker Compose & Deploy):** [docs/fase7_docker.md](docs/fase7_docker.md)

---

## 🚀 Como Executar o Ecossistema Completo

Toda a infraestrutura do projeto está orquestrada via Docker Compose. Os containers utilizam imagens base leves com o gerenciador de pacotes ultraveloz `uv`.

### Pré-requisitos
*   [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/) instalados na máquina host.

### Passos para Execução
Na raiz do projeto, execute o seguinte comando no terminal:

```bash
docker compose up --build
```

Este comando irá compilar as imagens, sincronizar as dependências e iniciar os dois serviços na mesma rede virtual privada:

1.  **API Backend (FastAPI):** Disponível na porta `8000`.
    *   Health Check: [http://localhost:8000/health](http://localhost:8000/health)
    *   Documentação Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
2.  **Dashboard Frontend (Streamlit):** Disponível na porta `8501`.
    *   Interface Visual: [http://localhost:8501](http://localhost:8501)

O front-end Streamlit aguarda a API estar completamente iniciada e ativa (status "healthy") antes de se inicializar, graças à política de healthcheck HTTP interna baseada em script Python leve.

---

## 🧠 Principais Decisões Técnicas e Arquiteturais

### 1. Desacoplamento de Camadas (API + Dashboard)
Seguindo a **regra de ouro** de sistemas web distribuídos, o dashboard Streamlit atua estritamente como um cliente de apresentação. Ele **não acessa os arquivos Parquet diretamente**. Toda a troca de dados é realizada via requisições HTTP (`requests`) aos endpoints da API FastAPI, permitindo a fácil substituição do frontend por tecnologias como React/Vue ou o escalonamento independente dos serviços.

### 2. Isolamento de Modelagem por Cultura Agrícola
A modelagem de clusterização foi executada de forma **independente para cada grão (Soja, Milho e Trigo)**. Misturar as culturas no mesmo espaço vetorial geraria um viés de magnitude extrema: a Soja, devido à sua gigantesca escala física e financeira no Paraná, sufocaria o Trigo, rotulando grandes polos de trigo incorretamente como "pequenos produtores". Além disso, as dinâmicas geográficas de crescimento e riscos climáticos (como geadas de inverno no trigo e secas de verão na soja) são distintas e seriam mascaradas em um modelo conjunto.

### 3. Tratamento Contra Extremos Climáticos: Mediana vs. Média
*   **Produtividade (Rendimento Médio):** Foi implementada utilizando a **Mediana** (`.median()`) em vez da média aritmética. Isso blinda o indicador de eficiência agrícola contra picos históricos de secas severas (outliers negativos climáticos pontuais), retendo a real capacidade técnica produtora do município.
*   **Perda de Área:** Foi calculada como a **Média** aritmética (`.mean()`) da diferença entre a área plantada e a colhida. Isso mantém a retenção histórica do risco climático acumulado a longo prazo.

### 4. Normalização com RobustScaler
Para o pré-processamento das features antes do K-Means, adotou-se o `RobustScaler`. O estado do Paraná possui megaprodutores agrícolas discrepantes que funcionariam como fortes outliers na escala convencional (como o `StandardScaler`). O `RobustScaler` utiliza mediana e intervalos interquartílicos (IQR), evitando distorções nos centroides do modelo de clusterização.

### 5. Estabilização e Reordenação de Rótulos de Clusters
Para resolver a variabilidade aleatória da inicialização do K-Means, implementamos um algoritmo de **reordenação dinâmica dos clusters**. Os grupos são ordenados de forma crescente de acordo com a produção média histórica dos municípios daquela cultura:
*   **Cluster 0:** Baixa Escala / Menores Produtores.
*   **Cluster 1:** Escala Intermediária / Produtores em Crescimento Moderado.
*   **Cluster 2:** Eficientes / Alta Produtividade em Média Escala.
*   **Cluster 3:** Gigantes Agrícolas / Polos de Altíssima Produção e Estabilidade.

### 6. Design de Visualização Científico (Zero Pizza/Rosquinha)
Respeitando as melhores práticas de visualização de dados científicos e inteligência de negócios, **o painel não contém gráficos de pizza ou de rosquinha**. Em vez disso, focamos em visualizações de alta capacidade analítica:
*   **Bar charts horizontais ordenados** para rankings.
*   **Linhas temporais com duplo eixo Y** para cruzar volume com eficiência.
*   **Scatter plots bidimensionais** com retas de corte para matrizes de risco (Volatilidade vs. Perda de Área) e separação de clusters (Produção vs. Rendimento).

---

## 🔍 Limitações da Solução

1.  **Dados em Memória na API:** Para otimização de velocidade de resposta em requisições concorrentes, a API realiza o cache em memória (`data_store`) dos arquivos Parquet durante o seu startup. Em um cenário produtivo com frequente inserção de dados, seria recomendada a migração para um banco de dados relacional indexado (como PostgreSQL) ou NoSQL (como MongoDB).
2.  **Variáveis Climáticas Indiretas:** As métricas de volatilidade (coeficiente de variação) e perda de área funcionam como proxies para o risco climático severo, mas não substituem variáveis meteorológicas reais (índice de chuva, déficit hídrico e temperatura).

---

## 📅 Cronograma de Desenvolvimento do Projeto (Prazo: 10 Dias)

Detalhamento da execução e entregas ao longo do período do desafio técnico:

*   **Dias 1 a 3: Planejamento, Arquitetura e Ingestão:** Análise de escopo, especificação da arquitetura e implementação do pipeline de ingestão e sanitização ([client.py](src/ingestion/client.py) e [pipeline.py](src/ingestion/pipeline.py)).
*   **Dias 4 e 5: Engenharia de Features:** Desenvolvimento das features temporais de escala, produtividade e risco ([builder.py](src/features/builder.py)).
*   **Dias 6 a 8: Pesquisa e Clusterização:** Modelagem dos agrupamentos por grão, normalização robusta e algoritmo de estabilização de centroides ([clusterer.py](src/models/clusterer.py)).
*   **Dia 9: APIs e Validação:** Construção dos endpoints REST FastAPI ([main.py](src/api/main.py)), esquemas de validação Pydantic ([schemas.py](src/api/schemas.py)) e escrita de testes unitários ([test_api.py](tests/test_api.py)).
*   **Dia 10: Frontend, Docker e Documentação:** Dashboard interativo Streamlit ([app.py](src/dashboard/app.py)), orquestração com Docker Compose ([docker-compose.yml](docker-compose.yml)) e consolidação da documentação técnica.

---


## 🧪 Executando Testes Locais

Para executar a suíte completa de testes automatizados unitários e de integração, certifique-se de ter as dependências de desenvolvimento instaladas e execute:

```bash
uv run pytest
```

Para checagem estática de formatação e boas práticas via Ruff:

```bash
uv run ruff check src/
```
