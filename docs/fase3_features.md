# 📈 Fase 3: Engenharia de Features Temporais

Este documento detalha o pipeline de engenharia de features para converter a série histórica anual (2010 a 2024) de produção agrícola em indicadores analíticos estáticos por Município + Cultura.

---

## 🎯 Objetivos
1. Agrupar os dados históricos consolidados da fase anterior por `municipio_codigo` e `produto`.
2. Criar métricas que reflitam o comportamento temporal histórico do município, evitando análises baseadas em apenas um único ano estático.
3. Computar indicadores de **Escala, Produtividade, Tendência, Volatilidade, Risco Climático e Participação de Mercado**.
4. Salvar a base de features consolidada para modelagem.

---

## 📊 Mapeamento das Dimensões Analíticas Oficiais
Para atender rigorosamente aos requisitos do PDF oficial do desafio (escala, produtividade, crescimento, estabilidade e participação relativa), as features foram mapeadas da seguinte forma:

| Dimensão Oficial do PDF | Feature do Projeto | Descrição e Cálculo |
| :--- | :--- | :--- |
| **Escala** | `prod_media`<br>`area_media`<br>`valor_producao_medio` | Média histórica da produção (t), área plantada (ha) e valor da produção (R$ 1.000). |
| **Produtividade** | `rendimento_medio_med` | Média histórica do rendimento médio (kg/ha). |
| **Crescimento** | `cagr_producao`<br>`cagr_rendimento`<br>`trend_slope_producao` | CAGR da produção e rendimento (crescimento geométrico) e inclinação linear (Slope) da produção. |
| **Estabilidade** | `volatilidade_prod`<br>`perda_area_media` | Coeficiente de Variação da produção (volatilidade) e taxa média de área perdida (risco climático/operacional). |
| **Participação Relativa** | `market_share_medio` | Média anual de participação do município na produção total do estado do Paraná. |

---

## 📐 Fórmulas e Definições das Features

### 1. Volatilidade da Produção (Coeficiente de Variação - CV)
Mede o risco ou a instabilidade da produção ao longo dos anos.
$$\text{CV} = \frac{\sigma(Produção)}{\mu(Produção)}$$
*No Pandas:* `df.groupby(...).std() / df.groupby(...).mean()`.

### 2. Taxa de Crescimento Anual Composta (CAGR)
Calcula a taxa média geométrica de crescimento da produção e do rendimento médio ao longo do período.
$$\text{CAGR} = \left( \frac{V_{final}}{V_{inicial}} \right)^{\frac{1}{N}} - 1$$
*Onde:* $V_{final}$ é a produção de 2024, $V_{inicial}$ é a produção de 2010 (ou primeiro ano com dados maiores que zero), e $N$ é o número de anos decorridos.

### 3. Tendência Linear de Crescimento (Slope)
Inclinação da reta de regressão linear para diferenciar municípios em expansão daqueles em declínio ou estáticos.
$$\text{Slope} = \frac{\sum (x - \bar{x})(y - \bar{y})}{\sum (x - \bar{x})^2}$$
*Onde:* $x$ é o Ano (2010-2024) e $y$ é a Quantidade Produzida. Calculado de forma simples em Python usando a função `numpy.polyfit(anos, producao, 1)[0]`.

### 4. Perda Média de Área (Risco Climático/Operacional)
Mede o percentual médio de área plantada que não chegou a ser colhida (por conta de secas, geadas, pragas, etc.).
$$\text{Perda de Área} = \text{Média} \left( \frac{\text{Área Plantada} - \text{Área Colhida}}{\text{Área Plantada}} \right)$$

### 5. Participação de Mercado (Market Share do Município)
Percentual médio de contribuição da produção daquele município em relação à produção total do estado do Paraná para a mesma cultura em cada ano.
$$\text{Market Share}_{m, t} = \frac{\text{Produção}_{m, t}}{\sum_{i} \text{Produção}_{i, t}}$$

---

## 📝 Blueprint do Código (Estrutura Recomendada para `src/features/builder.py`)

Abaixo está o fluxo recomendado para construir a classe `FeatureBuilder`:

```python
import pandas as pd
from pathlib import Path

class FeatureBuilder:
    def __init__(self, processed_data_path: Path):
        """
        Inicializa o construtor de features com o caminho do arquivo processado.
        """
        self.data_path = processed_data_path
        
    def load_data(self) -> pd.DataFrame:
        """
        Carrega a base consolidada Parquet gerada na Fase 2.
        """
        pass

    def calculate_slope(self, series: pd.Series) -> float:
        """
        Calcula a inclinação linear (Slope) da série histórica do município/cultura.
        (A lógica detalhada do polyfit encontra-se implementada em src/features/builder.py)
        """
        pass

    def calculate_cagr(self, series: pd.Series) -> float:
        """
        Calcula a Taxa de Crescimento Anual Composta (CAGR) da produção ou rendimento.
        (A lógica detalhada de limites e anos válidos encontra-se em src/features/builder.py)
        """
        pass

    def build_features(self) -> pd.DataFrame:
        """
        Orquestra as agregações e cálculos temporais (CV, CAGR, Slope, Perda de Área,
        e Market Share) agrupados por municipio_codigo e produto.
        Retorna o DataFrame consolidado de features estáticas por município.
        """
        pass

    def run(self) -> Path:
        """
        Executa a geração completa de features e salva a base final no formato Parquet.
        """
        pass
```
