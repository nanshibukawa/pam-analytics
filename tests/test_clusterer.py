import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.models.clusterer import AgriculturalClusterer


@pytest.fixture
def synthetic_features_df():
    """Cria um DataFrame de features sintético para testar o clusterizador sem acessar o disco."""
    np.random.seed(42)
    n_rows = 150
    
    # Geramos dados fictícios para 3 culturas
    products = ["soja", "milho", "trigo"] * (n_rows // 3)
    
    # Geramos produções médias diferentes para simular as escalas
    prod_media = np.concatenate([
        np.random.exponential(scale=100, size=50),      # Baixa produção (Cluster 0/1)
        np.random.normal(loc=15000, scale=3000, size=50), # Média produção (Cluster 1/2)
        np.random.normal(loc=90000, scale=10000, size=50) # Alta produção (Cluster 3)
    ])
    # Garante que não temos valores negativos na escala física
    prod_media = np.clip(prod_media, a_min=1, a_max=None)

    data = {
        "municipio": [f"Municipio_{i}" for i in range(n_rows)],
        "produto": products,
        "prod_media": prod_media,
        "rendimento_medio_med": np.random.uniform(500, 3500, size=n_rows),
        "cagr_producao": np.random.uniform(-0.1, 0.3, size=n_rows),
        "cagr_rendimento": np.random.uniform(-0.05, 0.1, size=n_rows),
        "trend_slope_producao": np.random.uniform(-100, 4000, size=n_rows),
        "volatilidade_prod": np.random.uniform(0.1, 3.0, size=n_rows),
        "perda_area_media": np.random.uniform(0.0, 0.05, size=n_rows),
    }
    
    return pd.DataFrame(data)


def test_agricultural_clusterer_pipeline(tmp_path, synthetic_features_df, monkeypatch):
    """Testa se a orquestração do pipeline de clusterização funciona de ponta a ponta.
    
    Valida:
    1. A criação da coluna de cluster rotulada.
    2. A ordenação correta e consistente dos clusters baseada na produção física média.
    3. A exportação correta do arquivo final em disco.
    """
    # Define caminhos temporários em disco usando o fixture tmp_path do pytest
    temp_in = tmp_path / "mock_features.parquet"
    temp_out = tmp_path / "mock_clusters_out.parquet"

    # Instancia o orquestrador
    clusterer = AgriculturalClusterer(
        features_path=temp_in,
        output_path=temp_out,
        n_clusters=4,
        random_state=42
    )

    # Simula o método _load_features para retornar a base mockada em vez de ler o disco
    monkeypatch.setattr(clusterer, "_load_features", lambda: synthetic_features_df)

    # Executa o pipeline
    df_output = clusterer.run_pipeline()

    # Validações estruturais do DataFrame retornado
    assert isinstance(df_output, pd.DataFrame)
    assert "cluster" in df_output.columns
    assert df_output["cluster"].nunique() <= 4
    
    # Validações específicas por cultura (ex: Soja)
    df_soja = df_output[df_output["produto"] == "soja"]
    assert not df_soja.empty

    # Validação Crítica: A ordenação consistente de clusters de 0 a 3 por produção física média
    means_by_cluster = df_soja.groupby("cluster")["prod_media"].mean()
    
    # Garante que os clusters estão em ordem estritamente crescente
    # A média de produção do Cluster 0 deve ser menor que a do 1, que é menor que a do 2, etc.
    sorted_means = means_by_cluster.sort_values()
    assert list(means_by_cluster.index) == list(sorted_means.index), (
        f"Os clusters não estão ordenados de forma crescente: {means_by_cluster.to_dict()}"
    )

    # Valida se o arquivo de saída Parquet foi criado fisicamente no disco
    assert temp_out.exists()
    
    # Valida se conseguimos ler o arquivo parquet gerado e se ele tem as mesmas dimensões
    df_disk = pd.read_parquet(temp_out)
    assert df_disk.shape == df_output.shape
