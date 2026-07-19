from typing import List

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Modelo de resposta para o status da API."""

    status: str = Field(..., description="Status de integridade da API ('ok')")


class MunicipioMetadata(BaseModel):
    """Modelo para representar um município nos metadados."""

    codigo: int = Field(..., description="Código IBGE do município")
    nome: str = Field(..., description="Nome do município")


class MetadataResponse(BaseModel):
    """Modelo de resposta para os metadados da base."""

    produtos: List[str] = Field(..., description="Lista de culturas agrícolas disponíveis")
    anos: List[int] = Field(..., description="Lista de anos históricos na base de dados")
    municipios: List[MunicipioMetadata] = Field(..., description="Lista de municípios mapeados")


class SeriesItem(BaseModel):
    """Modelo para representar um ponto temporal da série histórica."""

    ano: int = Field(..., description="Ano da safra")
    municipio_codigo: int = Field(..., description="Código IBGE do município")
    municipio_nome: str = Field(..., description="Nome do município")
    produto: str = Field(..., description="Cultura agrícola")
    area_plantada: float = Field(..., description="Área plantada ou destinada à colheita (hectares)")
    area_colhida: float = Field(..., description="Área colhida (hectares)")
    quantidade_produzida: float = Field(..., description="Quantidade produzida (toneladas)")
    rendimento_medio: float = Field(..., description="Rendimento médio da produção (kg/ha)")
    valor_producao: float = Field(..., description="Valor da produção (mil reais)")


class RankingItem(BaseModel):
    """Modelo para representar um item em um ranking municipal."""

    posicao: int = Field(..., description="Posição do município no ranking")
    municipio_codigo: int = Field(..., description="Código IBGE do município")
    municipio_nome: str = Field(..., description="Nome do município")
    valor_metrica: float = Field(..., description="Valor físico ou financeiro da métrica ordenada")


class ClusterItem(BaseModel):
    """Modelo para representar o cluster de um município específico."""

    municipio_codigo: int = Field(..., description="Código IBGE do município")
    municipio_nome: str = Field(..., description="Nome do município")
    produto: str = Field(..., description="Cultura agrícola")
    cluster: int = Field(..., description="Rótulo do cluster ordenado (0 a K-1)")
    prod_media: float = Field(..., description="Produção média histórica (t)")
    rendimento_medio_med: float = Field(..., description="Rendimento médio histórico (kg/ha)")
    cagr_producao: float = Field(..., description="Taxa de crescimento anual composta da produção")
    cagr_rendimento: float = Field(..., description="Taxa de crescimento anual composta do rendimento")
    trend_slope_producao: float = Field(..., description="Inclinação da tendência linear de produção")
    volatilidade_prod: float = Field(..., description="Volatilidade da produção (CV)")
    perda_area_media: float = Field(..., description="Taxa média histórica de perda de área")


class ClusterProfile(BaseModel):
    """Modelo para representar a média de features (perfil) de um cluster."""

    cluster: int = Field(..., description="Rótulo do cluster (0 a K-1)")
    prod_media: float = Field(..., description="Média de produção física do cluster")
    rendimento_medio_med: float = Field(..., description="Média do rendimento médio do cluster")
    cagr_producao: float = Field(..., description="Média de CAGR de produção do cluster")
    cagr_rendimento: float = Field(..., description="Média de CAGR de rendimento do cluster")
    trend_slope_producao: float = Field(..., description="Média de Slope de tendência do cluster")
    volatilidade_prod: float = Field(..., description="Média de volatilidade do cluster")
    perda_area_media: float = Field(..., description="Média de perda de área do cluster")


class ClustersResponse(BaseModel):
    """Modelo de resposta contendo a lista de municípios rotulados e seus perfis médios."""

    clusters: List[ClusterItem] = Field(..., description="Lista de municípios e seus rótulos de cluster")
    perfis: List[ClusterProfile] = Field(..., description="Resumo médio das features por perfil de cluster")
