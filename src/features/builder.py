"""Pipeline de Engenharia de Features para séries temporais agrícolas."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Resolve a raiz do projeto e adiciona ao sys.path para imports absolutos
BASE_PATH = Path(__file__).resolve().parent.parent.parent
if str(BASE_PATH) not in sys.path:
    sys.path.append(str(BASE_PATH))

from src.utils.logging_config import setup_logging  # noqa: E402

logger = setup_logging()


class FeatureBuilder:
    """Classe responsável por transformar séries temporais históricas em features analíticas

    estáticas por Município + Cultura.
    """

    def __init__(self, processed_data_path: Path):
        self.data_path = processed_data_path

    def run(self) -> Path:
        """Executa o pipeline de features completo e salva em arquivo Parquet."""
        df_features = self._build_features()

        output_path = self.data_path.parent / "pam_parana_features.parquet"
        logger.info(f"Salvando features consolidadas em: {output_path}")
        df_features.to_parquet(output_path, index=False, engine="pyarrow")
        logger.info("Execução da Engenharia de Features concluída com sucesso!")
        return output_path

    def _build_features(self) -> pd.DataFrame:
        """Gera as features agregadas por município e cultura."""
        df = self._load_data()

        logger.info("Calculando Market Share e Risco Climático por ano...")

        # 1. Calcular Market Share por ano e produto (com tratamento para divisão por zero)
        df["total_prod_ano"] = df.groupby(["ano", "produto"])["quantidade_produzida"].transform("sum")
        df["market_share"] = df["quantidade_produzida"] / df["total_prod_ano"].replace(0, np.nan)
        # Evita quebrar o modelo caso houver Nan
        df["market_share"] = df["market_share"].fillna(0.0)

        # 2. Calcular Risco Climático (Perda de Área) por ano
        # Evitar divisão por zero se area_plantada for zero
        df["perda_area_pct"] = (df["area_plantada"] - df["area_colhida"]) / df["area_plantada"].replace(0, np.nan)
        df["perda_area_pct"] = df["perda_area_pct"].fillna(0.0)
        # Clip: todo numero negativo vira 0.0, evita inconsistencia da base
        df["perda_area_pct"] = df["perda_area_pct"].clip(lower=0.0)

        # 3. Agregações e Cálculos Temporais por Município + Produto
        logger.info("Agrupando dados históricos por município + produto...")
        features_list = []

        # Ordena o DataFrame por ano uma única vez para garantir a ordem cronológica nos grupos
        df = df.sort_values("ano")
        grouped = df.groupby(["municipio_codigo", "municipio_nome", "produto"])

        for (m_cod, m_nome, prod), group in grouped:
            # Média das variáveis físicas/financeiras (Escala)
            mean_prod = group["quantidade_produzida"].mean()
            mean_area = group["area_plantada"].mean()
            median_yield = group["rendimento_medio"].median()
            mean_value = group["valor_producao"].mean()

            # Prepara séries com o ano como índice para os cálculos temporais de forma eficiente
            prod_series = pd.Series(group["quantidade_produzida"].values, index=group["ano"].values)
            yield_series = pd.Series(group["rendimento_medio"].values, index=group["ano"].values)

            # Volatilidade (Coeficiente de Variação) da produção
            cv_prod = self._calculate_volatility(prod_series)

            # CAGR e Slope
            cagr_prod = self._calculate_cagr(prod_series)
            cagr_yield = self._calculate_cagr(yield_series)
            slope_prod = self._calculate_slope(prod_series)
            slope_prod_norm = slope_prod / mean_prod if mean_prod > 0 else 0.0

            # Médias de market share e perda de área
            mean_market_share = group["market_share"].mean()
            mean_area_loss = group["perda_area_pct"].mean()

            features_list.append(
                {
                    "municipio_codigo": m_cod,
                    "municipio_nome": m_nome,
                    "produto": prod,
                    "prod_media": mean_prod,
                    "area_media": mean_area,
                    "rendimento_medio_med": median_yield,
                    "valor_producao_medio": mean_value,
                    "volatilidade_prod": cv_prod,
                    "cagr_producao": cagr_prod,
                    "cagr_rendimento": cagr_yield,
                    "trend_slope_producao": slope_prod,
                    "trend_slope_producao_norm": slope_prod_norm,
                    "market_share_medio": mean_market_share,
                    "perda_area_media": mean_area_loss,
                }
            )

        df_features = pd.DataFrame(features_list)
        logger.info(f"Feature engineering finalizado. Total de registros gerados: {len(df_features)}")
        return df_features

    def _load_data(self) -> pd.DataFrame:
        """Carrega a base consolidada Parquet."""
        logger.info(f"Carregando dados consolidados de: {self.data_path}")
        return pd.read_parquet(self.data_path)

    def _calculate_slope(self, series: pd.Series) -> float:
        """
        Calcula a inclinação linear da série histórica (Slope).
        Utiliza o índice da série (ano) como variável independente.
        """
        y = series.astype(float).values
        if len(y) < 2 or np.all(np.isnan(y)):
            return 0.0

        x = series.index.astype(float).values

        # Remove eventuais nulos de X e Y
        mask = ~np.isnan(y) & ~np.isnan(x)
        if np.sum(mask) < 2:
            return 0.0

        slope, _ = np.polyfit(x[mask], y[mask], 1)
        return float(slope)

    def _calculate_cagr(self, series: pd.Series) -> float:
        """
        Calcula a taxa de crescimento anual composta (CAGR) entre o primeiro e último ano
        com dados maiores que zero, usando o índice da série (ano) para o número de anos decorridos.
        """
        # Filtra valores maiores que zero, remove NaNs e ordena pelo ano (índice)
        valid_series = series[series > 0].dropna().sort_index()
        if len(valid_series) < 2:
            return 0.0

        v_ini = valid_series.iloc[0]
        v_fin = valid_series.iloc[-1]

        y_ini = int(valid_series.index[0])
        y_fin = int(valid_series.index[-1])

        n_years = y_fin - y_ini

        if n_years <= 0 or v_ini <= 0:
            return 0.0

        cagr = (v_fin / v_ini) ** (1.0 / n_years) - 1.0
        return float(cagr)

    def _calculate_volatility(self, series: pd.Series) -> float:
        """
        Calcula o Coeficiente de Variação (CV) da série histórica de forma segura.
        Mantido em decimal para consistência no KMeans.
        """
        # Remove NaNs logo no início para garantir que Mean e Std usem os mesmos dados
        clean_series = series.dropna().astype(float)
        if len(clean_series) < 2:
            return 0.0

        mean_val = clean_series.mean()

        # Evita divisão por zero ou por valores extremamente próximos de zero (ex: 0.0000001)
        # que fariam o CV explodir e distorcer o KMeans
        if abs(mean_val) < 1e-6:
            return 0.0

        std_val = clean_series.std()
        cv = std_val / mean_val

        return 0.0 if np.isnan(cv) else float(cv)


if __name__ == "__main__":
    setup_logging()
    processed_path = BASE_PATH / "data" / "processed" / "pam_parana_consolidado.parquet"
    builder = FeatureBuilder(processed_path)
    builder.run()
