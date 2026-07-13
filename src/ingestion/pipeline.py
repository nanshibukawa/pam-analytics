"""Pipeline de Ingestão e Tratamento de dados agrícolas da API SIDRA."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.utils.logging_config import setup_logging
from src.ingestion.client import SidraClient
from src.ingestion.sidra_mapping import (
    SidraCrops,
    SidraTable,
    SidraPeriod,
    SidraLocality,
    SidraVariables,
)

logger = setup_logging()


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

        # Nome da localidade dinâmico para organização de arquivos
        self.locality_name = SidraLocality.PARANA.name.lower()

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
                file_path = self.raw_dir / f"pam_{self.locality_name}_{crop_name}_raw.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_data, f, ensure_ascii=False, indent=4)

                logger.info(f"Dados brutos de {crop_name} salvos em: {file_path}")
            except Exception as e:
                logger.error(f"Erro no download da cultura {crop_name}: {e}")
                raise e

    def process_raw_data(self) -> pd.DataFrame:
        """Limpa, sanitiza valores especiais, pivota as tabelas e consolida as culturas."""
        variables_mapping = {v.value: v.name.lower() for v in SidraVariables}

        dfs_all = []

        for crop in SidraCrops:
            crop_name = crop.name.lower()

            logger.info(f"Processando dados brutos de: {crop_name}")
            file_path = self.raw_dir / f"pam_{self.locality_name}_{crop_name}_raw.json"

            if not file_path.exists():
                logger.warning(f"Arquivo {file_path} não encontrado. Pulando.")
                continue

            try:
                df = pd.read_json(file_path).iloc[1:]

                rename_map = {
                    "D1N": "ano",
                    "D2C": "variavel_codigo",
                    "D3C": "municipio_codigo",
                    "D3N": "municipio_nome",
                    "V": "valor",
                }
                df_2 = df[rename_map.keys()].rename(columns=rename_map)

                # Sanitização defensiva completa de caracteres especiais do IBGE
                df_2["valor"] = df_2["valor"].replace(
                    {
                        "-": "0",
                        "..": np.nan,
                        "...": np.nan,
                        "X": np.nan,
                        "x": np.nan,
                    }
                )

                df_2["valor"] = pd.to_numeric(df_2["valor"], errors="coerce")
                df_2["ano"] = df_2["ano"].astype(int)
                df_2["municipio_codigo"] = df_2["municipio_codigo"].astype(int)

                # Pivotagem para transformar de Formato Longo para Largo
                df_pivot = df_2.pivot_table(
                    index=["municipio_codigo", "municipio_nome", "ano"],
                    columns="variavel_codigo",
                    values="valor",
                    aggfunc="first",
                ).reset_index()

                df_final = df_pivot.rename(columns=variables_mapping)
                df_final["produto"] = crop_name

                dfs_all.append(df_final)

            except Exception as e:
                logger.error(f"Erro ao processar {file_path}: {e}")
                raise e

        # Concatenação e Consolidação
        if not dfs_all:
            logger.warning("Nenhum DataFrame processado. Retornando vazio.")
            return pd.DataFrame()

        df_concat = pd.concat(dfs_all, ignore_index=True)
        return df_concat

    def _build_query_path(self, crop_code: str) -> str:
        """Monta o caminho da query dinamicamente a partir dos Enums."""
        table = SidraTable.CULTIVARS_PRODUCAO.value
        period = SidraPeriod.P2010_2024.value
        variables = ",".join(v.value for v in SidraVariables)
        location = SidraLocality.PARANA.value

        return f"t/{table}/p/{period}/v/{variables}/n6/{location}/c782/{crop_code}"

    def run(self):
        """Executa a ingestão completa (download) das três culturas."""

        # 1. Baixar os dados brutos
        logger.info("Iniciando execução do pipeline de ingestão...")
        self.download_all_raw_data()

        # 2. Processar os dados brutos
        logger.info("Processando os dados brutos...")
        df = self.process_raw_data()
        logger.info("Processamento dos dados brutos finalizado com sucesso!")

        # 3. Salvar o parquet de saída
        logger.info("Salvando os dados consolidados...")
        output_path = self.processed_dir / f"pam_{self.locality_name}_consolidado.parquet"
        df.to_parquet(output_path, index=False, engine="pyarrow")
        logger.info(f"Dados consolidados salvos em: {output_path}")

        logger.info("Execução do pipeline finalizada com sucesso!")


if __name__ == "__main__":
    import sys

    # Resolve a raiz do projeto (sobe 3 níveis a partir de src/ingestion/pipeline.py)
    base_path = Path(__file__).resolve().parent.parent.parent
    sys.path.append(str(base_path))

    setup_logging()

    sidra_client = SidraClient()
    pipeline = IngestionPipeline(client=sidra_client, base_dir=base_path)
    pipeline.run()
