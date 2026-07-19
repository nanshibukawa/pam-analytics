from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import RobustScaler

from src.utils.logging_config import setup_logging

logger = setup_logging()


class AgriculturalClusterer:
    """Orquestrador do pipeline de modelagem e clusterização das culturas do PR."""

    def __init__(
        self,
        features_path: str | Path,
        output_path: str | Path,
        n_clusters: int = 4,
        random_state: int = 42,
    ):
        self.features_path = Path(features_path)
        self.output_path = Path(output_path)
        self.n_clusters = n_clusters
        self.random_state = random_state

        # Features selecionadas após tratamento de multicolinearidade
        self.feature_cols = [
            "prod_media",
            "rendimento_medio_med",
            "cagr_producao",
            "cagr_rendimento",
            "trend_slope_producao",
            "volatilidade_prod",
            "perda_area_media",
        ]

    def run_pipeline(self) -> pd.DataFrame:
        """Executa a clusterização de todas as culturas e consolida os resultados."""
        df_features = self._load_features()
        # i.e. ["soja", "milho", "trigo"]
        crops = df_features["produto"].unique().tolist()
        processed_dfs = []

        # Processa cada cultura isoladamente devido à incompatibilidade de escala física
        for crop in crops:
            df_crop = df_features[df_features["produto"] == crop].copy()
            assert isinstance(df_crop, pd.DataFrame)

            if df_crop.empty:
                logger.warning(f"Nenhum registro encontrado para: {crop}")
                continue

            logger.info(f"Iniciando modelagem para: {crop}")
            df_clustered = self._train_crop_model(df_crop, crop)
            processed_dfs.append(df_clustered)

        df_final = pd.concat(processed_dfs, ignore_index=True)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Salvando base de clusters em: {self.output_path}")
        df_final.to_parquet(self.output_path, index=False, engine="pyarrow")
        return df_final

    def _load_features(self) -> pd.DataFrame:
        """Carrega a base de features do arquivo Parquet."""
        if not self.features_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.features_path}")
        return pd.read_parquet(self.features_path)

    def _train_crop_model(self, df_crop: pd.DataFrame, crop_name: str) -> pd.DataFrame:
        """Aplica normalização, treina o KMeans e reordena os labels de forma crescente."""
        df = df_crop.copy()
        X = df[self.feature_cols].values

        # RobustScaler: protege o KMeans de distorções causadas por mega-produtores (outliers)
        scaler = RobustScaler()
        x_scaled = scaler.fit_transform(X)

        # random_state garante reprodutibilidade. n_init=10 evita o padrão 'auto' (1 run)
        # e protege contra mínimos locais e warnings entre versões do sklearn.
        kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10,
        )
        raw_labels = kmeans.fit_predict(x_scaled)
        df["temp_cluster"] = raw_labels

        # Reordenação: garante que 0 seja sempre menor produção e K-1 seja a maior
        cluster_means = df.groupby("temp_cluster")["prod_media"].mean().sort_values()
        cluster_mapping = {old_label: new_label for new_label, old_label in enumerate(cluster_means.index)}

        df["cluster"] = df["temp_cluster"].map(cluster_mapping)
        df = df.drop(columns=["temp_cluster"])

        # Avaliação estatística
        sil = silhouette_score(x_scaled, df["cluster"])
        logger.info(f"Cultura: {crop_name.upper()} | Silhouette Score: {sil:.4f}")

        means_log = df.groupby("cluster")["prod_media"].mean().round(2).to_dict()
        logger.info(f"Produção Média por Cluster Ordenado ({crop_name}): {means_log}")

        return df


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    features_in = BASE_DIR / "data" / "processed" / "pam_parana_features.parquet"
    clusters_out = BASE_DIR / "data" / "processed" / "clusters_final.parquet"

    clusterer = AgriculturalClusterer(features_path=features_in, output_path=clusters_out)
    clusterer.run_pipeline()
