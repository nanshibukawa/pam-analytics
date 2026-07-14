# 📥 Fase 2: Ingestão e Processamento de Dados

Este documento descreve as especificações técnicas, decisões de engenharia e a estrutura de código para o processamento e salvamento dos dados de produção agrícola.

---

## 🎯 Objetivos
1. Ler os dados brutos salvos em JSON em `data/raw/` para Soja, Milho e Trigo.
2. Descartar os metadados (primeira linha do JSON retornado pela API SIDRA).
3. Filtrar e renomear as colunas originais do IBGE para nomes legíveis.
4. **Sanitizar os dados:** Tratar símbolos especiais (`-`, `..`, `...`) e converter todos os valores para tipos numéricos adequados (`float64`).
5. **Pivotar a tabela:** Transformar o formato "longo" retornado pela API em formato "largo", onde cada variável vira uma coluna.
6. **Consolidar os dados:** Reunir as três culturas em um único DataFrame, identificadas por uma coluna `produto`.
7. **Salvar em Parquet:** Exportar a base final para `data/processed/pam_parana_consolidado.parquet`.

---

## 🛠️ Tecnologias e Bibliotecas
* **Pandas:** Para manipulação, limpeza e pivotagem de dados.
* **PyArrow / FastParquet:** Engine de suporte para salvar os dados em formato Parquet de forma eficiente.

---

## 📋 Regras de Limpeza e Transformação

### 1. Tratamento de Símbolos Especiais do IBGE
A coluna de valores (`V` no JSON bruto) contém strings e caracteres especiais que representam ausências de dados, segredos estatísticos ou valores insignificantes. O pipeline aplica a sanitização com base nas definições oficiais do IBGE:

| Símbolo IBGE | Significado Oficial | Exemplo Prático | Mapeamento no Pandas |
| :--- | :--- | :--- | :--- |
| **`-` (traço)** | Zero absoluto, não resultante de cálculo ou arredondamento. | Determinado município não produziu soja naquele ano. | Mapeia para `"0"` (vira `0.0` no float) |
| **`0`** | Zero resultante de um cálculo ou arredondamento. | Município produziu 400kg de girassol e a tabela está em toneladas (arredonda para 0). | Mantém como `"0"` (vira `0.0` no float) |
| **`X`** | Valor inibido para não identificar o informante (Segredo Estatístico). | Município possui apenas uma empresa produtora de cimento, inibindo o valor para sigilo. | Mapeia para `NaN` (nulo) |
| **`..`** | Valor não se aplica. | Tentar obter produtividade média dividindo $0 / 0$ em município sem área plantada. | Mapeia para `NaN` (nulo) |
| **`...`** | Valor não disponível. | A produção de feijão em determinado município não foi pesquisada naquele ano. | Mapeia para `NaN` (nulo) |
| **Letras A a Z** | Significa uma faixa de valores (nível de precisão da estimativa). | A precisão da produção estimada de combustíveis está na faixa A (até 5%). | Mapeia para `NaN` (nulo) |

Esse tratamento defensivo limpa a coluna `valor` antes de convertê-la e pivotá-la.

### 2. Mapeamento de Variáveis Numéricas (`SidraVariables`)
Durante a pivotagem, os códigos numéricos imutáveis das variáveis (`D2C`) são mapeados para nomes amigáveis em minúsculo no Pandas. O mapeamento completo das nomenclaturas originais e unidades oficiais é apresentado abaixo:

| Código IBGE (`D2C`) | Nome Original IBGE (`D2N`) | Unidade de Medida (`MN`) | Nome Final (Pandas) |
| :--- | :--- | :--- | :--- |
| **`8331`** | Área plantada ou destinada à colheita | Hectares | `area_plantada` |
| **`216`** | Área colhida | Hectares | `area_colhida` |
| **`214`** | Quantidade produzida | Toneladas | `quantidade_produzida` |
| **`112`** | Rendimento médio da produção | Quilogramas por Hectare | `rendimento_medio` |
| **`215`** | Valor da produção | Mil Reais | `valor_producao` |

### 3. A Importância Crítica da Pivotagem (Formato Longo vs. Largo)
A API do SIDRA retorna os dados originalmente no **Formato Longo** (onde as variáveis de um mesmo município e ano ficam empilhadas verticalmente em linhas separadas). Para a modelagem e exposição em API, é **estritamente necessário** transformar esse layout para o **Formato Largo** (uma única linha por município-ano, com as variáveis distribuídas em colunas horizontais).

#### **Por que essa transformação é obrigatória?**
1. **Cálculos entre Variáveis (Engenharia de Features):** No formato longo, métricas como Área Plantada e Área Colhida ficam em linhas distintas, inviabilizando subtrações diretas no Pandas. Com a pivotagem, elas viram colunas na mesma linha, permitindo cálculos simples como `df['perda'] = df['area_plantada'] - df['area_colhida']`.
2. **Entrada de Algoritmos (Machine Learning):** Modelos de clusterização (como K-Means ou K-Medoids) exigem matrizes de dados estruturadas onde **cada linha representa uma observação única** (município + ano) e **cada coluna representa uma feature** (característica).
3. **Consumo Simplificado pela API e Dashboard:** Permite que os endpoints retornem séries completas e estruturadas em um único registro JSON por ano, otimizando o fluxo de dados.

---

## 🏃 Passo a Passo Simplificado do Código

### **Passo 1: Carregar os dados ignorando metadados da API**
```python
df = pd.read_json(path).iloc[1:]
```
* O IBGE sempre devolve a primeira linha da resposta com descrições em texto das colunas (metadados). O `.iloc[1:]` joga essa primeira linha fora e mantém apenas as linhas com dados reais.

### **Passo 2: Filtrar e Renomear as colunas básicas**
```python
rename_map = {"D1N": "ano", "D2C": "variavel_codigo", "D3C": "municipio_codigo", "D3N": "municipio_nome", "V": "valor"}
df_2 = df[rename_map.keys()].rename(columns=rename_map)
```
* **A Origem do Mapeamento:** As siglas nativas (`D1N`, `D2C`, `D3C`, `D3N`, `V`) e suas correspondências amigáveis não são arbitrárias. Elas foram deduzidas a partir da análise da primeira linha (metadados) retornada pelo SIDRA. Por exemplo:
  * A sigla `D1N` tem como valor no cabeçalho `"Ano"` (que mapeamos para `"ano"`).
  * A sigla `D2C` tem como valor no cabeçalho `"Variável (Código)"` (que mapeamos para `"variavel_codigo"`).
  * A sigla `D3C` tem como valor no cabeçalho `"Município (Código)"` (que mapeamos para `"municipio_codigo"`).
  * A sigla `D3N` tem como valor no cabeçalho `"Município"` (que mapeamos para `"municipio_nome"`).
  * A sigla `V` tem como valor no cabeçalho `"Valor"` (que mapeamos para `"valor"`).
* Esse filtro seleciona apenas o subconjunto necessário e dá nomes consistentes em português.

### **Passo 3: O Pivot (A transformação de linhas em colunas)**
```python
df_pivot = df_2.pivot_table(
    index=["municipio_codigo", "municipio_nome", "ano"], 
    columns="variavel_codigo", 
    values="valor", 
    aggfunc="first"
).reset_index()
```
* Essa linha reorganiza os dados para que cada município em cada ano ocupe **apenas uma linha** na tabela.

### **Passo 4: Renomear as colunas finais**
```python
variables_mapping = {v.value: v.name.lower() for v in SidraVariables}
df_final = df_pivot.rename(columns=variables_mapping)
```
* O pivot cria colunas nomeadas temporariamente com os IDs numéricos (`"8331"`, `"216"`, etc.). Esse passo converte os códigos para seus nomes legíveis (como `area_plantada`, `area_colhida`).

---

## 📊 Exemplo Prático da Transformação (Município de Abatiá em 2010)

### 1. Formato Original (Longo) recebido da API
No formato de resposta padrão do SIDRA, os dados para a mesma observação temporal vêm fragmentados em linhas múltiplas:

```text
 municipio_nome     | ano  | variavel_codigo      | valor
 -------------------|------|----------------------|-------
  Abatiá - PR        | 2010 | 8331 (Área Plantada) | 2810
  Abatiá - PR        | 2010 | 216 (Área Colhida)   | 2810
  Abatiá - PR        | 2010 | 214 (Qtd Produzida)  | 16511
```

### 2. Formato Final (Largo) obtido via `pivot_table`
Após rodar o pivot e aplicar a renomeação das variáveis, os dados são consolidados horizontalmente:

```text
 municipio_nome | ano  | area_plantada | area_colhida | quantidade_produzida
 ---------------|------|---------------|--------------|----------------------
  Abatiá - PR    | 2010 | 2810          | 2810         | 16511
```

#### **Vantagens Finais:**
1. **Linha Única:** O registro município/ano ocupa exatamente uma linha no DataFrame.
2. **Cálculos Fáceis:** Operações matemáticas entre colunas (ex: perda de área) são vetorizadas de forma trivial.
3. **Pronto para Machine Learning:** Os dados ficam prontos na forma de matriz de atributos $[N \times D]$ exigida por algoritmos do `scikit-learn`.

---

## 📝 Blueprint do Código (Estrutura Recomendada para `src/ingestion/pipeline.py`)

Abaixo está o fluxo lógico recomendado para implementar dentro da classe `IngestionPipeline`:

```python
import pandas as pd
from pathlib import Path

class IngestionPipeline:
    def __init__(self, client, base_dir: Path):
        """
        Inicializa o pipeline de ingestão com o cliente de API e diretórios do projeto.
        """
        self.client = client
        self.base_dir = base_dir
        self.raw_dir = base_dir / "data" / "raw"
        self.processed_dir = base_dir / "data" / "processed"

    def process_raw_data(self) -> pd.DataFrame:
        """
        Lê os arquivos JSON brutos de data/raw, aplica o tratamento dos símbolos especiais
        do IBGE, pivota as colunas de formato longo para largo e unifica as três culturas.
        (A lógica detalhada de processamento encontra-se em src/ingestion/pipeline.py)
        """
        pass

    def run(self):
        """
        Orquestra a pipeline executando o download (se necessário) e o processamento,
        salvando a base consolidada final no formato Parquet em data/processed.
        """
        pass
```
