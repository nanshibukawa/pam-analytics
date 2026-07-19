import logging
import os
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Configuração de logging
logger = logging.getLogger(__name__)

# URL base da API obtida do ambiente ou fallback para localhost
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


class APIClient:
    """Cliente HTTP para comunicação com a API do PAM Paraná Analytics."""

    # Sessão compartilhada para manter conexões ativas (Keep-Alive) e pooling de conexões
    _session = requests.Session()

    # Configuração de retentativas para tratar instabilidades temporárias e reloads
    _retries = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[502, 503, 504],
        raise_on_status=False,
    )
    _adapter = HTTPAdapter(max_retries=_retries)
    _session.mount("http://", _adapter)
    _session.mount("https://", _adapter)

    @staticmethod
    def check_health() -> bool:
        """Verifica a integridade e inicialização da API.

        Returns:
            bool: True se a API estiver operacional, False caso contrário.
        """
        try:
            url = f"{API_BASE_URL}/health"
            response = APIClient._session.get(url, timeout=5)
            if response.status_code == 200:
                return response.json().get("status") == "ok"
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao verificar integridade da API: {e}")
            return False

    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        """Obtém metadados da base (produtos, anos e municípios disponíveis).

        Returns:
            Dict[str, Any]: Dicionário contendo metadados.
        """
        url = f"{API_BASE_URL}/metadata"
        response = APIClient._session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_series(produto: str, municipio_codigo: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtém séries históricas de produção filtradas por município e produto.

        Args:
            produto (str): Nome do produto/cultura (soja, milho, trigo).
            municipio_codigo (Optional[int]): Código IBGE do município.

        Returns:
            List[Dict[str, Any]]: Lista de itens da série histórica.
        """
        params: Dict[str, Any] = {}
        if municipio_codigo is not None:
            params["municipio_codigo"] = municipio_codigo
        if produto is not None:
            params["produto"] = produto

        url = f"{API_BASE_URL}/series"
        response = APIClient._session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_ranking(produto: str, ano: int, metric: str = "quantidade_produzida") -> List[Dict[str, Any]]:
        """Obtém o ranking de municípios para um produto, ano e métrica específicos.

        Args:
            produto (str): Cultura agrícola (soja, milho, trigo).
            ano (int): Ano da safra.
            metric (str): Métrica para ordenação.

        Returns:
            List[Dict[str, Any]]: Lista ordenada com a classificação dos municípios.
        """
        params: Dict[str, Any] = {"produto": produto, "ano": ano, "metric": metric}
        url = f"{API_BASE_URL}/ranking"
        response = APIClient._session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_clusters(produto: str) -> Dict[str, Any]:
        """Obtém dados detalhados de clusters e perfis médios para um determinado produto.

        Args:
            produto (str): Cultura agrícola (soja, milho, trigo).

        Returns:
            Dict[str, Any]: Dicionário contendo a lista de clusters e os perfis médios.
        """
        params: Dict[str, Any] = {"produto": produto}
        url = f"{API_BASE_URL}/clusters"
        response = APIClient._session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
