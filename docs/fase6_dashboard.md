# 🎨 Fase 6: Dashboard de Visualização (Streamlit)

Este documento descreve as especificações técnicas, componentes de interface e regras de comunicação com o backend necessárias para construir o dashboard de visualização interativo em Streamlit.

---

## 🎯 Objetivos
1. Desenhar uma interface gráfica interativa simples para demonstração do produto final do desafio.
2. **Desacoplamento de Arquitetura (Regra de Ouro):** Garantir que o Dashboard se comunique com os dados **apenas através da API FastAPI**, sem realizar nenhuma leitura direta dos arquivos Parquet ou modelos salvos em disco.
3. Permitir filtros dinâmicos na barra lateral (cultura, ano, município e métrica).
4. Renderizar painéis de séries temporais históricas, rankings de produtores e a visualização dos perfis de clusters gerados.

---

## 🔌 Comunicação Frontend-Backend (Exemplo)
O dashboard deve utilizar a biblioteca `requests` para conversar com a API local (rodando em `http://localhost:8000`).

```mermaid
flowchart LR
    User([Usuário]) -->|1. Interage com os filtros| Dash["Streamlit (Porta 8501)"]
    Dash -->|2. Solicita dados via HTTP| API["FastAPI (Porta 8000)"]
    API -->|3. Retorna os dados em JSON| Dash
    Dash -->|4. Atualiza os gráficos na tela| User
```

---

## 📝 Blueprint do Código (Estrutura Recomendada para [app.py](../src/dashboard/app.py))

Abaixo está o fluxo lógico estruturado do painel Streamlit (a implementação completa encontra-se em [app.py](../src/dashboard/app.py) e a camada de consumo HTTP está isolada em [api_client.py](../src/dashboard/api_client.py)):

```python
import streamlit as st
import pandas as pd
from src.dashboard.api_client import APIClient

st.set_page_config(
    page_title="PAM Paraná Analytics",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Verificação de Saúde da API através do cliente HTTP (APIClient.check_health())
# 2. Carregar Metadados da API FastAPI para popular os filtros (APIClient.get_metadata())
# 3. Desenhar a barra lateral de filtros (Cultura e Ano Base)
# 4. Carregar os dados específicos da Cultura selecionada (APIClient.get_series(), APIClient.get_clusters())
# 5. Desenhar o painel principal estruturado em abas com st.tabs:
#    - Aba 1: Gráfico de evolução temporal e detalhamento do município
#    - Aba 2: Gráficos de dispersão e tabela de scores de Risco Agrícola
#    - Aba 3: Perfis descritivos dos clusters gerados e agrupamentos multidimensionais
```
