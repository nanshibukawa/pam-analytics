"""Pipeline de Ingestão e Tratamento de dados agrícolas da API SIDRA."""

import os
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

from src.ingestion.client import SidraClient

from src.ingestion.sidra_mapping import (
    SidraCrops,
    SidraTable,
    SidraPeriod,
    SidraLocality,
    SidraVariables,
)


logger = logging.getLogger(__name__)

class IngestionPipeline:
    """Orquestrador que gerencia o download dos dados brutos e o processamento final."""

    def __init__(self, client: SidraClient, base_dir: Path):
        self.client = client
        self.base_dir = base_dir
        self.raw_dir = base_dir / "data" / "raw"
        self.processed_dir = base_dir / "data" / "processed"
        
        # Garante a criação física das pastas locais
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _build_query_path(self, crop_code: str) -> str:
        """Monta o caminho da query dinamicamente a partir dos Enums."""
        table = SidraTable.CULTIVARS_PRODUCAO.value
        period = SidraPeriod.P2010_2024.value
        variables = ",".join(v.value for v in SidraVariables)
        location = SidraLocality.PARANA.value
        
        return f"t/{table}/p/{period}/v/{variables}/n6/{location}/c782/{crop_code}"

    def download_all_raw_data(self):
        """Etapa 1 da Estratégia A: Baixa os dados brutos e salva em JSON locais."""
        for crop in SidraCrops:
            crop_name = crop.name.lower()
            crop_code = crop.value
            
            logger.info(f"Iniciando download dos dados brutos de: {crop_name}")
            query_path = self._build_query_path(crop_code)
            
            try:
                # Baixa os dados usando o cliente
                raw_data = self.client.fetch_raw_data(query_path)
                
                # Salva o arquivo JSON bruto no disco
                file_path = self.raw_dir / f"pam_parana_{crop_name}_raw.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_data, f, ensure_ascii=False, indent=4)
                    
                logger.info(f"Dados brutos de {crop_name} salvos em: {file_path}")
            except Exception as e:
                logger.error(f"Erro no download da cultura {crop_name}: {e}")
                raise e

    def run(self):
        """Executa a ingestão completa (download) das três culturas."""
        logger.info("Iniciando execução do pipeline de ingestão...")
        self.download_all_raw_data()
        logger.info("Execução do pipeline finalizada com sucesso!")


if __name__ == "__main__":
    import sys
    
    # Resolve a raiz do projeto (sobe 3 níveis a partir de src/ingestion/pipeline.py)
    base_path = Path(__file__).resolve().parent.parent.parent
    sys.path.append(str(base_path))
    
    from src.utils.logging_config import setup_logging
    
    setup_logging()
    
    sidra_client = SidraClient()
    pipeline = IngestionPipeline(client=sidra_client, base_dir=base_path)
    pipeline.run()