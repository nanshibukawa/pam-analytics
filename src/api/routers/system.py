from fastapi import APIRouter, HTTPException

from src.api.schemas import HealthResponse, MetadataResponse
from src.api.services import DataService

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """Verifica se o servidor da API está ativo e se os dados foram carregados."""
    if not DataService.get_health_status():
        raise HTTPException(status_code=503, detail="API inicializando ou sem dados carregados.")
    return {"status": "ok"}


@router.get("/metadata", response_model=MetadataResponse)
async def get_metadata():
    """Retorna opções disponíveis na base de dados: produtos, anos e lista de municípios."""
    return DataService.get_metadata()
