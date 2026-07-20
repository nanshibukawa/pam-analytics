from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import HTTPException

from src.pipeline_runner import run_full_pipeline
from src.utils.logging_config import setup_logging

logger = setup_logging()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONSOLIDADO_PATH = BASE_DIR / "data" / "processed" / "pam_parana_consolidado.parquet"
CLUSTERS_PATH = BASE_DIR / "data" / "processed" / "clusters_final.parquet"

# Cache em memória global
data_store = {}


def load_data_to_store():
    """Carrega os arquivos Parquet de produção para a memória cache do servidor.

    Executa a leitura única dos arquivos no startup do app. Implementa o princípio
    Fail-Fast, lançando exceção caso as bases necessárias não estejam no disco.

    Raises:
        FileNotFoundError: Se algum dos arquivos de dados esperados não for encontrado.
    """
    logger.info("Iniciando carregamento de dados em memória...")

    if not CONSOLIDADO_PATH.exists() or not CLUSTERS_PATH.exists():
        logger.warning(
            "Bases de dados de produção não encontradas localmente. "
            "Iniciando execução automática do pipeline ponta a ponta..."
        )

        try:
            run_full_pipeline(BASE_DIR)
        except Exception as e:
            logger.error(f"Falha na execução automática do pipeline de dados: {e}")
            raise FileNotFoundError(
                f"Arquivos de dados necessários ausentes e falha ao gerá-los automaticamente. Erro: {e}"
            ) from e

    logger.info(f"Carregando histórico de: {CONSOLIDADO_PATH}")
    df_consolidado = pd.read_parquet(CONSOLIDADO_PATH)
    data_store["consolidado"] = df_consolidado

    logger.info(f"Carregando clusters de: {CLUSTERS_PATH}")
    df_clusters = pd.read_parquet(CLUSTERS_PATH)
    data_store["clusters"] = df_clusters

    # Pré-computa metadados para O(1) no endpoint /metadata e validação rápida
    produtos = sorted(df_consolidado["produto"].dropna().unique().tolist())
    anos = sorted(df_consolidado["ano"].dropna().unique().tolist())

    df_mun = (
        df_consolidado[["municipio_codigo", "municipio_nome"]].dropna().drop_duplicates().sort_values("municipio_nome")
    )
    municipios = [
        {"codigo": int(row["municipio_codigo"]), "nome": row["municipio_nome"]} for _, row in df_mun.iterrows()
    ]

    data_store["metadata"] = {"produtos": produtos, "anos": anos, "municipios": municipios}
    data_store["valid_produtos"] = set(produtos)
    data_store["valid_anos"] = set(anos)

    logger.info("Carregamento e pré-computação concluídos com sucesso!")


def clear_data_store():
    """Limpa a memória do servidor."""
    data_store.clear()
    logger.info("Dados limpos da memória.")


class DataService:
    @staticmethod
    def get_health_status() -> bool:
        """Verifica se as bases de dados de produção foram carregadas em cache com sucesso.

        Returns:
            bool: True se ambos os DataFrames estiverem em memória e populados,
                  False caso contrário.
        """

        consolidado = data_store.get("consolidado")
        clusters = data_store.get("clusters")
        if consolidado is None or consolidado.empty or clusters is None or clusters.empty:
            return False
        return True

    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        """Obtém metadados da base histórica para preenchimento de filtros.

        Retorna as listas de culturas agrícolas, anos e municípios (código e nome)
        mapeados na base consolidada de produção.

        Returns:
            Dict[str, Any]: Dicionário contendo as listas de 'produtos', 'anos' e 'municipios'.

        Raises:
            HTTPException: Se a base de dados histórica não estiver carregada em memória.
        """
        metadata = data_store.get("metadata")
        if not metadata:
            raise HTTPException(status_code=404, detail="Dados históricos não carregados na API.")
        return metadata

    @staticmethod
    def get_series(municipio_codigo: Optional[int] = None, produto: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtém a série histórica de produção filtrada por município e/ou produto.

        Realiza a consulta sobre a base consolidada, tratando valores nulos e
        convertendo as linhas em dicionários prontos para serialização.

        Args:
            municipio_codigo (Optional[int]): Código IBGE do município para filtro.
            produto (Optional[str]): Nome da cultura agrícola (soja, milho, trigo).

        Returns:
            List[Dict[str, Any]]: Lista de dicionários representando a série temporal.

        Raises:
            HTTPException: Se a base de dados consolidada não estiver carregada em memória.
        """

        df = data_store.get("consolidado")
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="Dados históricos não carregados na API.")

        df_filtered = df.copy()
        if municipio_codigo is not None:
            df_filtered = df_filtered[df_filtered["municipio_codigo"] == municipio_codigo]
        if produto is not None:
            produto_clean = produto.lower().strip()
            df_filtered = df_filtered[df_filtered["produto"] == produto_clean]

        if df_filtered.empty:
            return []

        df_filtered = df_filtered.fillna(0.0)
        return df_filtered.to_dict(orient="records")

    @staticmethod
    def get_ranking(produto: str, ano: int, metric: str) -> List[Dict[str, Any]]:
        """Gera o ranking municipal ordenado com base no produto, ano e métrica escolhidos.

        Filtra a base consolidada de produção para a cultura e a safra informadas,
        ordena os resultados em ordem decrescente pela métrica selecionada e calcula
        a posição ordinal de cada município (1-indexed).

        Args:
            produto (str): Cultura agrícola a ser ranqueada (soja, milho, trigo).
            ano (int): Ano da safra analisada.
            metric (str): Coluna numérica usada para ordenação (quantidade_produzida,
                area_plantada, area_colhida, rendimento_medio, valor_producao).

        Returns:
            List[Dict[str, Any]]: Lista de dicionários representando o ranking ordenado,
                contendo as chaves 'posicao', 'municipio_codigo', 'municipio_nome'
                e 'valor_metrica'.

        Raises:
            HTTPException: Se a base consolidada não estiver carregada em memória (404)
                ou se a métrica, produto ou ano fornecidos forem inválidos (400).
        """
        df = data_store.get("consolidado")
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="Dados históricos não carregados na API.")

        valid_metrics = ["quantidade_produzida", "area_plantada", "area_colhida", "rendimento_medio", "valor_producao"]

        metric_clean = metric.lower().strip()
        if metric_clean not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Métrica inválida. Escolha entre: {', '.join(valid_metrics)}")

        produto_clean = produto.lower().strip()
        if "valid_produtos" in data_store and produto_clean not in data_store["valid_produtos"]:
            valid_prods = ", ".join(sorted(data_store["valid_produtos"]))
            raise HTTPException(
                status_code=400,
                detail=f"Produto inválido: '{produto}'. Escolha entre: {valid_prods}",
            )

        if "valid_anos" in data_store and ano not in data_store["valid_anos"]:
            valid_years = ", ".join(map(str, sorted(data_store["valid_anos"])))
            raise HTTPException(
                status_code=400,
                detail=f"Ano inválido: {ano}. Escolha entre: {valid_years}",
            )

        df_filtered = df[(df["produto"] == produto_clean) & (df["ano"] == ano)].copy()
        if df_filtered.empty:
            return []

        df_filtered = df_filtered.sort_values(by=metric_clean, ascending=False).reset_index(drop=True)
        df_filtered = df_filtered.fillna(0.0)

        # Vetorização do Pandas para evitar iterrows() lento
        df_filtered["posicao"] = df_filtered.index + 1
        df_filtered["valor_metrica"] = df_filtered[metric_clean].astype(float)
        df_filtered["municipio_codigo"] = df_filtered["municipio_codigo"].astype(int)

        return df_filtered[["posicao", "municipio_codigo", "municipio_nome", "valor_metrica"]].to_dict(orient="records")

    @staticmethod
    def get_clusters(produto: str) -> Dict[str, Any]:
        """Obtém os municípios rotulados e calcula os perfis médios dos clusters para uma cultura.

        Filtra os dados da modelagem para a cultura informada, extrai as métricas de
        clusterização de cada município e calcula dinamicamente a média das variáveis
        de modelagem agrupadas por cluster (perfilamento em tempo real).

        Args:
            produto (str): Cultura agrícola analisada (soja, milho, trigo).

        Returns:
            Dict[str, Any]: Dicionário contendo duas listas:
                - 'clusters': Lista com a classificação e indicadores individuais de cada município.
                - 'perfis': Resumo médio estatístico característico de cada um dos clusters (0 a K-1).

        Raises:
            HTTPException: Se os dados de clusters não estiverem carregados na API (404)
                ou se a cultura informada não possuir dados de cluster processados (404).
        """

        df_clusters = data_store.get("clusters")
        if df_clusters is None or df_clusters.empty:
            raise HTTPException(status_code=404, detail="Dados de clusters não carregados ou não processados na API. ")

        produto_clean = produto.lower().strip()
        df_filtered = df_clusters[df_clusters["produto"] == produto_clean].copy()
        if df_filtered.empty:
            raise HTTPException(status_code=404, detail=f"Nenhum cluster encontrado para a cultura: {produto_clean}")

        df_filtered = df_filtered.fillna(0.0)
        clusters_list = df_filtered.to_dict(orient="records")

        feature_cols = [
            "prod_media",
            "rendimento_medio_med",
            "cagr_producao",
            "cagr_rendimento",
            "trend_slope_producao",
            "volatilidade_prod",
            "perda_area_media",
        ]

        df_profiles = df_filtered.groupby("cluster")[feature_cols].mean().reset_index()
        profiles_list = df_profiles.to_dict(orient="records")

        return {"clusters": clusters_list, "perfis": profiles_list}
