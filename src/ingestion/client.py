
import requests
from src.utils.logging_config import setup_logging
from src.ingestion.sidra_mapping import BASE_URL_API_SIDRA

logger = setup_logging()

class SidraClient:
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    def fetch_raw_data(self, query_path: str) -> list[dict]:
        """
        Faz a chamada GET na API e retorna a lista JSON de dados.

        Args:
            query_path (str): Path da API contendo todas as variáveis, 
            unidades, periodicidade, culturas e filtros territoriais.

        Returns:
            list[dict]: Lista JSON contendo os dados da pesquisa.

        Raises:
            Exception: Se o timeout for excedido ou ocorrer um erro HTTP.
        """

        url = f"{BASE_URL_API_SIDRA}/{query_path.lstrip('/')}"

        logger.info(f"Fazendo requisição GET para a API: {url}")

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout na requisição GET para {url}")
            raise Exception(f"Timeout na requisição GET para {url}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro HTTP ao fazer GET para {url}: {e}")
            raise Exception(f"Erro HTTP ao fazer GET para {url}: {e}")


 