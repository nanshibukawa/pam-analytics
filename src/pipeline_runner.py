"""Script unificado para execução sequencial de todo o pipeline de dados.

Ingestão (SIDRA API) -> Engenharia de Features -> Clusterização (K-Means).
"""

import sys
from pathlib import Path

# Resolve a raiz do projeto e adiciona ao sys.path para imports absolutos
BASE_PATH = Path(__file__).resolve().parent.parent
if str(BASE_PATH) not in sys.path:
    sys.path.append(str(BASE_PATH))

from src.features.builder import FeatureBuilder  # noqa: E402
from src.ingestion.client import SidraClient  # noqa: E402
from src.ingestion.pipeline import IngestionPipeline  # noqa: E402
from src.models.clusterer import AgriculturalClusterer  # noqa: E402
from src.utils.logging_config import setup_logging  # noqa: E402

logger = setup_logging()


def run_full_pipeline(base_dir: Path):
    """Executa sequencialmente todas as fases do pipeline de ciência de dados.

    Fase 2 (Download e Ingestão) -> Fase 3 (Features) -> Fase 4 (Clusterização).
    """
    logger.info("=" * 60)
    logger.info("INICIANDO EXECUÇÃO DO PIPELINE DE DADOS PONTA A PONTA")
    logger.info("=" * 60)

    # 1. Executa a Ingestão e Processamento Inicial
    logger.info("[PASSO 1/3] Iniciando Ingestão de dados da API SIDRA/IBGE...")
    sidra_client = SidraClient()
    pipeline_ingestion = IngestionPipeline(client=sidra_client, base_dir=base_dir)
    pipeline_ingestion.run()

    # 2. Executa a Engenharia de Features
    logger.info("[PASSO 2/3] Iniciando Engenharia de Features Temporais...")
    processed_path = base_dir / "data" / "processed" / "pam_parana_consolidado.parquet"
    builder = FeatureBuilder(processed_path)
    features_path = builder.run()

    # 3. Executa a Modelagem (Clusterização)
    logger.info("[PASSO 3/3] Iniciando Clusterização (Treinamento do K-Means)...")
    clusters_path = base_dir / "data" / "processed" / "clusters_final.parquet"
    clusterer = AgriculturalClusterer(features_path=features_path, output_path=clusters_path)
    clusterer.run_pipeline()

    logger.info("=" * 60)
    logger.info("PIPELINE PONTA A PONTA EXECUTADO COM SUCESSO!")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_full_pipeline(BASE_PATH)
