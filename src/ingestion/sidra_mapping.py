"""Constantes e identificadores imutáveis da API SIDRA/IBGE."""

from enum import Enum

BASE_URL_API_SIDRA = "https://apisidra.ibge.gov.br/values"

# Mapeamento para renomeação de colunas da API SIDRA.
# NOTA: D4C e D4N são mantidos aqui para garantir a validação de contrato (esquema) do JSON bruto,
# embora o pipeline opte por preencher a coluna final 'produto' de forma simplificada pós-pivotagem.
SIDRA_RENAME_MAP = {
    "D1N": "ano",
    "D2C": "variavel_codigo",
    "D3C": "municipio_codigo",
    "D3N": "municipio_nome",
    "D4C": "cultura_codigo",
    "D4N": "cultura_nome",
    "V": "valor",
}


class SidraCrops(Enum):
    """Culturas agrícolas solicitadas pelo escopo do projeto."""

    SOJA = "40124"
    MILHO = "40122"
    TRIGO = "40127"


class SidraTable(Enum):
    """Tabelas do SIDRA/IBGE utilizadas no projeto."""

    CULTIVARS_PRODUCAO = "5457"


class SidraPeriod(Enum):
    """Períodos históricos de coleta configuráveis."""

    P2010_2024 = "2010-2024"


class SidraLocality(Enum):
    """Filtros de localidade territorial da API."""

    PARANA = "in n3 41"  # Todos os municípios (n6) no Estado do Paraná (n3 = 41)


class SidraVariables(Enum):
    """
    Variáveis da pesquisa PAM do IBGE (Tabela 5457).
    Os nomes das chaves em maiúsculo (ex: AREA_PLANTADA) são convertidos
    dinamicamente para minúsculo pelo pipeline para nomear as colunas do Pandas.
    """

    AREA_PLANTADA = "8331"
    AREA_COLHIDA = "216"
    QUANTIDADE_PRODUZIDA = "214"
    RENDIMENTO_MEDIO = "112"
    VALOR_PRODUCAO = "215"
