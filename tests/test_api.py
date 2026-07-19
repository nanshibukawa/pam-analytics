import pytest
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

# Resolve e importa o app
from src.api.main import app
from src.api.services import data_store

@pytest.fixture
def client(monkeypatch):
    """Fixture para inicializar o TestClient da FastAPI injetando dados sintéticos em memória."""
    
    # 1. Cria DataFrame histórico consolidado sintético
    df_consolidado = pd.DataFrame({
        "ano": [2020, 2021, 2022] * 3,
        "municipio_codigo": [410010, 410010, 410010, 410020, 410020, 410020, 410030, 410030, 410030],
        "municipio_nome": ["Londrina", "Londrina", "Londrina", "Maringa", "Maringa", "Maringa", "Cascavel", "Cascavel", "Cascavel"],
        "produto": ["soja", "soja", "soja", "milho", "milho", "milho", "trigo", "trigo", "trigo"],
        "area_plantada": [1000.0] * 9,
        "area_colhida": [980.0] * 9,
        "quantidade_produzida": [3000.0, 3100.0, 3200.0, 1500.0, 1600.0, 1700.0, 800.0, 900.0, 1000.0],
        "rendimento_medio": [3000.0] * 9,
        "valor_producao": [5000.0] * 9,
    })

    # 2. Cria DataFrame de clusters sintético
    df_clusters = pd.DataFrame({
        "municipio_codigo": [410010, 410020, 410030],
        "municipio_nome": ["Londrina", "Maringa", "Cascavel"],
        "produto": ["soja", "soja", "soja"],
        "cluster": [0, 1, 2],
        "prod_media": [1000.0, 15000.0, 90000.0],
        "rendimento_medio_med": [2500.0, 2900.0, 3300.0],
        "cagr_producao": [0.02, 0.25, 0.05],
        "cagr_rendimento": [-0.01, 0.0, 0.01],
        "trend_slope_producao": [10.0, 200.0, 3000.0],
        "volatilidade_prod": [0.8, 1.2, 0.25],
        "perda_area_media": [0.01, 0.02, 0.001],
    })

    # Evita que o startup do TestClient tente ler arquivos reais do disco
    monkeypatch.setattr("src.api.main.load_data_to_store", lambda: None)

    # Retorna o cliente de teste configurado
    with TestClient(app) as tc:
        # Injeta os DataFrames mockados no data_store em memória APÓS o startup_event do TestClient
        monkeypatch.setitem(data_store, "consolidado", df_consolidado)
        monkeypatch.setitem(data_store, "clusters", df_clusters)
        yield tc


def test_get_health(client):
    """Valida se o endpoint de health check responde com OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_metadata(client):
    """Valida se o endpoint de metadados retorna as listas de produtos, anos e cidades."""
    response = client.get("/metadata")
    assert response.status_code == 200
    json_data = response.json()
    
    assert "produtos" in json_data
    assert "anos" in json_data
    assert "municipios" in json_data
    
    assert "soja" in json_data["produtos"]
    assert 2020 in json_data["anos"]
    assert json_data["municipios"][0]["nome"] == "Cascavel"


def test_get_series(client):
    """Valida o filtro de séries históricas por município e produto."""
    # Filtro apenas por produto
    response = client.get("/series?produto=soja")
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["produto"] == "soja"

    # Filtro por município
    response = client.get("/series?municipio_codigo=410020")
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["municipio_nome"] == "Maringa"


def test_get_ranking(client):
    """Valida a ordenação e numeração do ranking municipal."""
    response = client.get("/ranking?produto=soja&ano=2021&metric=quantidade_produzida")
    assert response.status_code == 200
    json_data = response.json()
    
    # Soja em 2021 só tem 1 registro (de Londrina) na nossa base sintética
    assert len(json_data) == 1
    assert json_data[0]["posicao"] == 1
    assert json_data[0]["municipio_nome"] == "Londrina"
    assert json_data[0]["valor_metrica"] == 3100.0


def test_get_ranking_invalid_metric(client):
    """Valida se a API barra e retorna 400 Bad Request para métricas de ranking inválidas."""
    response = client.get("/ranking?produto=soja&ano=2021&metric=metrica_inexistente")
    assert response.status_code == 400
    assert "Métrica inválida" in response.json()["detail"]


def test_get_clusters(client):
    """Valida se a API retorna a lista de clusters e calcula os perfis agregados em tempo real."""
    response = client.get("/clusters?produto=soja")
    assert response.status_code == 200
    json_data = response.json()
    
    assert "clusters" in json_data
    assert "perfis" in json_data
    
    assert len(json_data["clusters"]) == 3
    assert len(json_data["perfis"]) == 3 # 3 clusters distintos (0, 1, 2)
    
    # O perfil do cluster 0 deve ter a mesma prod_media do único município nele (Londrina = 1000.0)
    profile_0 = next(p for p in json_data["perfis"] if p["cluster"] == 0)
    assert profile_0["prod_media"] == 1000.0
