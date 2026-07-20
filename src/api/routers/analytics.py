from typing import List, Optional

from fastapi import APIRouter, Query

from src.api.schemas import ClustersResponse, RankingItem, SeriesItem
from src.api.services import DataService

router = APIRouter(tags=["Analytics"])


@router.get("/series", response_model=List[SeriesItem])
async def get_series(
    produto: Optional[str] = Query(None, description="Cultura agrícola (soja, milho, trigo)"),
    municipio_codigo: Optional[int] = Query(None, description="Filtrar por código IBGE do município."),
):
    """Retorna a série histórica de produção por município e/ou produto."""
    return DataService.get_series(municipio_codigo=municipio_codigo, produto=produto)


@router.get("/ranking", response_model=List[RankingItem])
async def get_ranking(
    produto: str = Query(..., description="Cultura agrícola (soja, milho, trigo)"),
    ano: int = Query(..., description="Ano da safra para ranqueamento."),
    metric: str = Query(
        "quantidade_produzida",
        description=(
            "Métrica para ordenação (quantidade_produzida, area_plantada, "
            "area_colhida, valor_producao, rendimento_medio)"
        ),
    ),
):
    """Retorna o ranking municipal baseado em produto, ano e uma métrica selecionada."""
    return DataService.get_ranking(produto=produto, ano=ano, metric=metric)


@router.get("/clusters", response_model=ClustersResponse)
async def get_clusters(
    produto: str = Query(..., description="Cultura agrícola (soja, milho, trigo) para obter os perfis e rótulos"),
):
    """Retorna a lista de municípios rotulados com seus respectivos clusters e o perfil resumo médio por grupo."""
    return DataService.get_clusters(produto=produto)
