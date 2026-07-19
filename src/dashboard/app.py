import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.api_client import APIClient

# Configuração da página e layout do Streamlit
st.set_page_config(page_title="PAM Paraná Analytics", page_icon="🚜", layout="wide", initial_sidebar_state="expanded")

# Estilização CSS personalizada para dar uma cara premium (estética rica)
st.markdown(
    """
<style>
    /* Estilos globais e tamanho de fonte global do Streamlit */
    .stMarkdown p, .stMarkdown li, div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li {
        font-size: 1.18rem !important;
        line-height: 1.6 !important;
    }
    .stMarkdown h3, div[data-testid="stMarkdownContainer"] h3 {
        font-size: 1.75rem !important;
    }
    .stMarkdown h2, div[data-testid="stMarkdownContainer"] h2 {
        font-size: 2.25rem !important;
    }

    .main-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
    }
    .subtitle {
        font-size: 1.35rem;
        color: #64748b;
        margin-top: -1.5rem;
        margin-bottom: 2rem;
    }
    /* Estilos para cartões de KPI (adaptáveis a temas) */
    .kpi-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .kpi-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text-color);
        opacity: 0.75;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--text-color);
    }
    .kpi-delta {
        font-size: 0.95rem;
        font-weight: 600;
        margin-top: 8px;
    }
    .kpi-delta-up {
        color: #047857; /* Verde contrastado em Light Mode */
        background-color: rgba(4, 120, 87, 0.12);
        padding: 6px 12px;
        border-radius: 6px;
        display: inline-block;
        font-size: 0.95rem;
    }
    .kpi-delta-down {
        color: #b91c1c; /* Vermelho contrastado em Light Mode */
        background-color: rgba(185, 28, 28, 0.12);
        padding: 6px 12px;
        border-radius: 6px;
        display: inline-block;
        font-size: 0.95rem;
    }
    @media (prefers-color-scheme: dark) {
        .kpi-delta-up {
            color: #34d399 !important; /* Verde pastel visível em Dark Mode */
            background-color: rgba(52, 211, 153, 0.18) !important;
        }
        .kpi-delta-down {
            color: #f87171 !important; /* Vermelho pastel visível em Dark Mode */
            background-color: rgba(248, 113, 113, 0.18) !important;
        }
    }
    /* Estilos gerais */
    .status-badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-online {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-offline {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    /* Menu lateral */
    .sidebar-title {
        font-weight: 700;
        font-size: 1.4rem;
        color: var(--text-color);
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Funções auxiliares cacheadas para consulta da API
@st.cache_data(show_spinner="Carregando metadados...")
def load_metadata():
    return APIClient.get_metadata()


@st.cache_data(show_spinner="Carregando dados de clusters...")
def load_clusters_data(produto: str):
    return APIClient.get_clusters(produto)


@st.cache_data(show_spinner="Carregando série histórica...")
def load_series_data(produto: str):
    return APIClient.get_series(produto=produto)


@st.cache_data(show_spinner="Carregando rankings...")
def load_ranking_data(produto: str, ano: int, metric: str):
    return APIClient.get_ranking(produto=produto, ano=ano, metric=metric)


# --- 1. Verificação de Saúde da API ---
api_online = APIClient.check_health()

# --- 2. Barra Lateral de Filtros (Sidebar) ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">🚜 Painel Paraná Analytics</div>', unsafe_allow_html=True)

    # Exibe badge de status da conexão
    if api_online:
        st.markdown('<span class="status-badge status-online">● Backend Online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-offline">● Backend Offline</span>', unsafe_allow_html=True)

    st.write("---")

    if not api_online:
        st.error(
            "⚠️ Não foi possível se conectar à API backend na porta 8000. "
            "Por favor, verifique se o servidor FastAPI está rodando."
        )
        st.info("Execute no terminal:\n`uv run python src/api/main.py` ou inicie via Docker Compose.")
        st.stop()

    # Busca metadados dinâmicos
    try:
        metadata = load_metadata()
    except Exception as e:
        st.error(f"⚠️ Erro ao buscar metadados da API: {e}")
        st.stop()

    produtos = metadata.get("produtos", ["soja", "milho", "trigo"])
    anos = metadata.get("anos", list(range(2010, 2025)))
    municipios_meta = metadata.get("municipios", [])

    # Filtros interativos
    produto_selecionado = st.selectbox(
        "Selecione a Cultura:",
        options=produtos,
        format_func=lambda x: x.capitalize(),
        help="Escolha a cultura agrícola para filtrar todas as análises do dashboard.",
    )

    ano_selecionado = st.selectbox(
        "Selecione o Ano Base:",
        options=sorted(anos, reverse=True),
        help="Selecione o ano base para a aba de rankings e mercado.",
    )

    st.write("---")
    st.markdown("### ℹ️ Sobre os dados")
    st.caption(
        "Dados históricos extraídos da Pesquisa Agrícola Municipal (PAM - IBGE) "
        "cobrindo as safras de 2010 a 2024 para o estado do Paraná."
    )

# --- 3. Carregamento de Dados Principais da Safra ---
# Obtém séries históricas e clusters para a cultura selecionada
try:
    df_series_all = pd.DataFrame(load_series_data(produto=produto_selecionado))
    clusters_res = load_clusters_data(produto=produto_selecionado)
    df_clusters = pd.DataFrame(clusters_res.get("clusters", []))
    df_profiles = pd.DataFrame(clusters_res.get("profiles", []))
except Exception as e:
    st.error(f"⚠️ Erro ao carregar dados da API para '{produto_selecionado}': {e}")
    st.info("Por favor, certifique-se de que a API backend está ativa e tente recarregar a página.")
    st.stop()

CLUSTER_NAMES = {
    0: "Cluster 0: Baixa Escala",
    1: "Cluster 1: Intermediário",
    2: "Cluster 2: Eficiente / Alto Rend.",
    3: "Cluster 3: Gigantes Agrícolas",
}

if not df_clusters.empty:
    df_clusters["Cluster_Label"] = df_clusters["cluster"].map(CLUSTER_NAMES)

# Título do App
st.markdown('<div class="main-title">Plataforma Analítica PAM Paraná</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="subtitle">Análise de produção e inteligência agrícola '
    f"para a cultura de {produto_selecionado.capitalize()}</div>",
    unsafe_allow_html=True,
)

# Layout de Abas principais
tab_comercial, tab_risco, tab_clusters = st.tabs(
    ["📈 Inteligência Comercial", "🛡️ Crédito & Risco Climático", "🤖 Segmentação (Clusters)"]
)

# ==========================================
# ABA 1: INTELIGÊNCIA COMERCIAL
# ==========================================
with tab_comercial:
    st.markdown("### 📈 Oportunidades de Negócio e Expansão Comercial")
    st.markdown(
        "Esta aba é voltada para a equipe comercial identificar municípios com "
        "alto crescimento histórico e expansão de produtividade, otimizando a "
        "distribuição de insumos (sementes, defensivos e fertilizantes)."
    )

    if df_clusters.empty:
        st.warning("Sem dados de clusters disponíveis para análise comercial.")
    else:
        # 1. KPIs Comerciais Principais
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

        # CAGR Médio de Produção da Cultura
        cagr_prod_medio = df_clusters["cagr_producao"].mean()
        # CAGR Médio de Produtividade (Rendimento)
        cagr_rend_medio = df_clusters["cagr_rendimento"].mean()
        # Top Município em crescimento de volume
        top_grower_idx = df_clusters["trend_slope_producao"].idxmax()
        top_grower = df_clusters.loc[top_grower_idx]

        # Total Produzido no Ano Selecionado
        df_year = df_series_all[df_series_all["ano"] == ano_selecionado]
        total_prod_ano = df_year["quantidade_produzida"].sum() / 1e6  # em milhões de toneladas

        with kpi_col1:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-title">Produção Total ({ano_selecionado})</div>
                <div class="kpi-value">{total_prod_ano:.2f}M t</div>
                <div class="kpi-delta kpi-delta-up">Volume Físico no Estado</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with kpi_col2:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-title">CAGR Médio Produção</div>
                <div class="kpi-value">{cagr_prod_medio * 100:.2f}%</div>
                <div class="kpi-delta {"kpi-delta-up" if cagr_prod_medio >= 0 else "kpi-delta-down"}">
                    {"▲ Crescimento" if cagr_prod_medio >= 0 else "▼ Declínio"} anual composto
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with kpi_col3:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-title">CAGR Médio Rendimento</div>
                <div class="kpi-value">{cagr_rend_medio * 100:.2f}%</div>
                <div class="kpi-delta {"kpi-delta-up" if cagr_rend_medio >= 0 else "kpi-delta-down"}">
                    {"▲ Produtividade" if cagr_rend_medio >= 0 else "▼ Produtividade"} anual
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with kpi_col4:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-title">Destaque de Tendência</div>
                <div class="kpi-value" style="font-size: 1.2rem; line-height: 2.2rem;">
                    {top_grower["municipio_nome"]}
                </div>
                <div class="kpi-delta kpi-delta-up">▲ Maior crescimento físico absoluto (Slope)</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.write("---")

        # 2. Rankings e Análise Regional
        rank_col1, rank_col2 = st.columns([1, 1])

        with rank_col1:
            st.subheader("Top 10 Municípios com Maior Tendência de Crescimento (Slope)")
            st.caption(
                "A inclinação linear (Slope) indica o aumento médio absoluto anual de produção física em toneladas."
            )

            # Ordena municípios pelo slope
            df_slope_top = df_clusters.sort_values(by="trend_slope_producao", ascending=False).head(10)

            fig_slope = px.bar(
                df_slope_top,
                x="trend_slope_producao",
                y="municipio_nome",
                orientation="h",
                labels={"trend_slope_producao": "Tendência de Produção (t/ano)", "municipio_nome": "Município"},
                color="trend_slope_producao",
                color_continuous_scale="Viridis",
            )
            fig_slope.update_layout(
                yaxis={
                    "categoryorder": "total ascending",
                    "tickfont": {"size": 18},
                    "title": {"font": {"size": 22}},
                },
                xaxis={
                    "tickfont": {"size": 18},
                    "title": {"font": {"size": 22}},
                },
                height=400,
                coloraxis_showscale=False,
                font=dict(size=20),
            )
            st.plotly_chart(fig_slope, width="stretch")

        with rank_col2:
            st.subheader(f"Top 10 Municípios por Volume Produzido ({ano_selecionado})")
            st.caption(f"Volume físico total produzido em toneladas no ano de {ano_selecionado}.")

            # Consulta endpoint de ranking da API
            ranking_data = load_ranking_data(
                produto=produto_selecionado, ano=ano_selecionado, metric="quantidade_produzida"
            )
            df_ranking = pd.DataFrame(ranking_data).head(10)

            if not df_ranking.empty:
                fig_rank = px.bar(
                    df_ranking,
                    x="valor_metrica",
                    y="municipio_nome",
                    orientation="h",
                    labels={"valor_metrica": "Produção (toneladas)", "municipio_nome": "Município"},
                    color="valor_metrica",
                    color_continuous_scale="Blues",
                )
                fig_rank.update_layout(
                    yaxis={
                        "categoryorder": "total ascending",
                        "tickfont": {"size": 18},
                        "title": {"font": {"size": 22}},
                    },
                    xaxis={
                        "tickfont": {"size": 18},
                        "title": {"font": {"size": 22}},
                    },
                    height=400,
                    coloraxis_showscale=False,
                    font=dict(size=20),
                )
                st.plotly_chart(fig_rank, width="stretch")
            else:
                st.info("Nenhum dado de ranking retornado pela API para este ano.")

        st.write("---")

        # 3. Série Histórica Detalhada por Município
        st.subheader("🔍 Detalhamento Temporal do Município")
        st.markdown(
            "Selecione um município específico para acompanhar a evolução histórica "
            "da área plantada, produção e eficiência (rendimento)."
        )

        municipios_lista = sorted(df_series_all["municipio_nome"].unique().tolist())
        municipio_selecionado = st.selectbox(
            "Selecione o Município:",
            options=municipios_lista,
            index=municipios_lista.index("Cascavel") if "Cascavel" in municipios_lista else 0,
        )

        # Filtra dados do município selecionado
        df_mun_series = df_series_all[df_series_all["municipio_nome"] == municipio_selecionado].sort_values("ano")
        df_mun_cluster = df_clusters[df_clusters["municipio_nome"] == municipio_selecionado]

        if not df_mun_series.empty:
            # Informações adicionais do município
            if not df_mun_cluster.empty:
                m_cagr_p = df_mun_cluster.iloc[0]["cagr_producao"] * 100
                m_cagr_r = df_mun_cluster.iloc[0]["cagr_rendimento"] * 100
                m_cluster = df_mun_cluster.iloc[0]["cluster"]
                m_cluster_name = CLUSTER_NAMES.get(m_cluster, f"Cluster {m_cluster}")
                st.markdown(
                    f"**Cluster Associado:** `{m_cluster_name}` | "
                    f"**CAGR de Produção:** `{m_cagr_p:.2f}%` | "
                    f"**CAGR de Rendimento:** `{m_cagr_r:.2f}%`"
                )

            # Gráficos temporais
            fig_trend = go.Figure()
            # Eixo primário: Produção
            fig_trend.add_trace(
                go.Scatter(
                    x=df_mun_series["ano"],
                    y=df_mun_series["quantidade_produzida"],
                    name="Produção (toneladas)",
                    line=dict(color="#1f77b4", width=3),
                )
            )
            # Eixo secundário: Rendimento Médio
            fig_trend.add_trace(
                go.Scatter(
                    x=df_mun_series["ano"],
                    y=df_mun_series["rendimento_medio"],
                    name="Produtividade (kg/ha)",
                    yaxis="y2",
                    line=dict(color="#ff7f0e", width=3, dash="dot"),
                )
            )

            # Configura layout do duplo eixo Y
            fig_trend.update_layout(
                title=dict(text=f"Evolução Temporal em {municipio_selecionado}", font=dict(size=24)),
                xaxis=dict(
                    title=dict(text="Ano (Safra)", font=dict(size=22)),
                    tickfont=dict(size=18)
                ),
                yaxis=dict(
                    title=dict(text="Produção (t)", font=dict(color="#1f77b4", size=22)),
                    tickfont=dict(color="#1f77b4", size=18),
                ),
                yaxis2=dict(
                    title=dict(text="Produtividade (kg/ha)", font=dict(color="#ff7f0e", size=22)),
                    tickfont=dict(color="#ff7f0e", size=18),
                    anchor="x",
                    overlaying="y",
                    side="right",
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=18),
                ),
                height=450,
                font=dict(size=20),
            )
            st.plotly_chart(fig_trend, width="stretch")

            # Exibe tabela detalhada
            with st.expander("Ver Tabela de Dados Históricos"):
                st.dataframe(
                    df_mun_series[
                        [
                            "ano",
                            "area_plantada",
                            "area_colhida",
                            "quantidade_produzida",
                            "rendimento_medio",
                            "valor_producao",
                        ]
                    ]
                    .rename(
                        columns={
                            "ano": "Ano",
                            "area_plantada": "Área Plantada (ha)",
                            "area_colhida": "Área Colhida (ha)",
                            "quantidade_produzida": "Produção (t)",
                            "rendimento_medio": "Produtividade (kg/ha)",
                            "valor_producao": "Valor da Produção (mil R$)",
                        }
                    )
                    .set_index("Ano")
                )

# ==========================================
# ABA 2: CRÉDITO & RISCO CLIMÁTICO
# ==========================================
with tab_risco:
    st.markdown("### 🛡️ Matriz de Risco Agrícola e Concessão de Crédito")
    st.markdown(
        "Aba estruturada para apoiar analistas de risco e crédito na definição "
        "de limites, taxas de financiamento e seguros agrícolas. Foco na "
        "volatilidade da safra e nas perdas climáticas históricas."
    )

    if df_clusters.empty:
        st.warning("Sem dados de clusters disponíveis para análise de risco.")
    else:
        # 1. KPIs de Risco Globais
        r_col1, r_col2, r_col3, r_col4 = st.columns(4)

        mean_volatilidade = df_clusters["volatilidade_prod"].mean()
        mean_perda_area = df_clusters["perda_area_media"].mean()

        # Identifica município com maior perda percentual de área
        top_risk_loss = df_clusters.sort_values(by="perda_area_media", ascending=False).iloc[0]
        # Identifica município com maior volatilidade histórica
        top_risk_vol = df_clusters.sort_values(by="volatilidade_prod", ascending=False).iloc[0]

        with r_col1:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-title">Volatilidade Média do PR</div>
                <div class="kpi-value">{mean_volatilidade * 100:.2f}%</div>
                <div class="kpi-delta kpi-delta-down">Coeficiente de Variação Médio</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with r_col2:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-title">Perda de Área Média</div>
                <div class="kpi-value">{mean_perda_area * 100:.2f}%</div>
                <div class="kpi-delta kpi-delta-down">Área plantada não colhida</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with r_col3:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-title">Maior Risco Climático</div>
                <div class="kpi-value" style="font-size: 1.2rem; line-height: 2.2rem;">
                    {top_risk_loss["municipio_nome"]}
                </div>
                <div class="kpi-delta kpi-delta-down">
                    ▼ Perda de área de {top_risk_loss["perda_area_media"] * 100:.2f}%
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with r_col4:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-title">Maior Instabilidade</div>
                <div class="kpi-value" style="font-size: 1.2rem; line-height: 2.2rem;">
                    {top_risk_vol["municipio_nome"]}
                </div>
                <div class="kpi-delta kpi-delta-down">
                    ▼ Volatilidade de {top_risk_vol["volatilidade_prod"] * 100:.2f}%
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.write("---")

        # 2. Gráfico Quadrante de Risco: Volatilidade vs. Perda de Área
        st.subheader("📊 Matriz de Dispersão de Risco Municipal")
        st.markdown("""
        O gráfico abaixo cruza duas dimensões críticas de risco:
        * **Eixo X (Volatilidade da Produção):** Mede a instabilidade histórica (picos e quebras de safra).
        * **Eixo Y (Perda de Área Média):** Mede o risco climático severo direto
          (frustração de safra por eventos extremos, onde o produtor planta mas não colhe).

        **Quadrante de Atenção (Superior Direito):** Municípios que sofrem tanto com grande
        instabilidade quanto com recorrentes perdas de área plantada.
        """)

        # Cria quadrantes baseados nas médias
        fig_scatter_risk = px.scatter(
            df_clusters,
            x="volatilidade_prod",
            y="perda_area_media",
            hover_name="municipio_nome",
            size="prod_media",
            color="Cluster_Label",
            color_discrete_map={
                "Cluster 0: Baixa Escala": "#94a3b8",
                "Cluster 1: Intermediário": "#60a5fa",
                "Cluster 2: Eficiente / Alto Rend.": "#f59e0b",
                "Cluster 3: Gigantes Agrícolas": "#10b981",
            },
            category_orders={
                "Cluster_Label": [
                    "Cluster 0: Baixa Escala",
                    "Cluster 1: Intermediário",
                    "Cluster 2: Eficiente / Alto Rend.",
                    "Cluster 3: Gigantes Agrícolas",
                ]
            },
            labels={
                "volatilidade_prod": "Volatilidade da Produção (CV)",
                "perda_area_media": "Taxa de Perda de Área (Diferença Plantada vs Colhida)",
                "prod_media": "Produção Média (t)",
                "Cluster_Label": "Grupo (Cluster)",
            },
            title="Matriz de Risco: Volatilidade vs Perda de Área",
        )

        # Adiciona linhas de corte médias de referência
        fig_scatter_risk.add_vline(x=mean_volatilidade, line_width=1.5, line_dash="dash", line_color="gray")
        fig_scatter_risk.add_hline(y=mean_perda_area, line_width=1.5, line_dash="dash", line_color="gray")

        fig_scatter_risk.update_layout(
            height=550,
            font=dict(size=20),
            title=dict(
                text="Matriz de Risco: Volatilidade vs Perda de Área",
                font=dict(size=24),
                x=0.5,
                xanchor="center",
                y=0.95,
                yanchor="top",
            ),
            xaxis=dict(
                title=dict(font=dict(size=22)),
                tickfont=dict(size=18)
            ),
            yaxis=dict(
                title=dict(font=dict(size=22), standoff=25),
                tickfont=dict(size=18)
            ),
            legend=dict(font=dict(size=18)),
            margin=dict(t=100, l=120, r=50, b=80),
        )
        st.plotly_chart(fig_scatter_risk, width="stretch")

        st.write("---")

        # 3. Classificação e Filtragem Interativa de Municípios Críticos
        st.subheader("📋 Tabela de Exposição e Score de Risco")
        st.markdown(
            "Filtre os municípios do estado de acordo com os níveis de risco "
            "aceitáveis pela política de crédito interna."
        )

        min_vol, max_vol = st.slider(
            "Filtrar por Faixa de Volatilidade (CV %):",
            min_value=0.0,
            max_value=float(df_clusters["volatilidade_prod"].max() * 100),
            value=(0.0, float(df_clusters["volatilidade_prod"].max() * 100)),
            step=1.0,
        )

        min_perda, max_perda = st.slider(
            "Filtrar por Faixa de Perda de Área Média (%):",
            min_value=0.0,
            max_value=float(df_clusters["perda_area_media"].max() * 100),
            value=(0.0, float(df_clusters["perda_area_media"].max() * 100)),
            step=0.5,
        )

        # Filtra os dados baseados nos sliders
        df_filtered_risk = df_clusters[
            (df_clusters["volatilidade_prod"] >= min_vol / 100)
            & (df_clusters["volatilidade_prod"] <= max_vol / 100)
            & (df_clusters["perda_area_media"] >= min_perda / 100)
            & (df_clusters["perda_area_media"] <= max_perda / 100)
        ].copy()

        st.markdown(
            f"**Municípios filtrados nesta faixa:** `{len(df_filtered_risk)}` de `{len(df_clusters)}` cadastrados."
        )

        # Cria classificação de risco baseada nas features do município
        # Score de Risco = (Volatilidade normalizada + Perda de área normalizada) / 2
        vol_max = df_clusters["volatilidade_prod"].max() if df_clusters["volatilidade_prod"].max() > 0 else 1
        perda_max = df_clusters["perda_area_media"].max() if df_clusters["perda_area_media"].max() > 0 else 1

        df_filtered_risk["Risco Score"] = (
            (df_filtered_risk["volatilidade_prod"] / vol_max) + (df_filtered_risk["perda_area_media"] / perda_max)
        ) / 2

        # Reordena colunas de forma legível
        df_filtered_display = df_filtered_risk[
            [
                "municipio_nome",
                "prod_media",
                "rendimento_medio_med",
                "volatilidade_prod",
                "perda_area_media",
                "Risco Score",
                "cluster",
            ]
        ].sort_values(by="Risco Score", ascending=False).copy()

        # Mapeia rótulo numérico do cluster para o nome comercial correspondente
        df_filtered_display["cluster"] = df_filtered_display["cluster"].map(CLUSTER_NAMES)

        # Formatação das colunas para visualização premium
        st.dataframe(
            df_filtered_display.rename(
                columns={
                    "municipio_nome": "Município",
                    "prod_media": "Prod. Média (t)",
                    "rendimento_medio_med": "Rendimento Mediana (kg/ha)",
                    "volatilidade_prod": "Volatilidade (CV)",
                    "perda_area_media": "Perda de Área Média",
                    "Risco Score": "Score de Risco (0-1)",
                    "cluster": "Cluster",
                }
            ).style.format(
                {
                    "Prod. Média (t)": "{:,.1f}",
                    "Rendimento Mediana (kg/ha)": "{:,.0f}",
                    "Volatilidade (CV)": "{:.2%}",
                    "Perda de Área Média": "{:.2%}",
                    "Score de Risco (0-1)": "{:.2f}",
                }
            ),
            width="stretch",
        )

# ==========================================
# ABA 3: SEGMENTAÇÃO (CLUSTERS)
# ==========================================
with tab_clusters:
    st.markdown("### 🤖 Segmentação Multidimensional de Produtores (K-Means)")
    st.markdown("""
    A clusterização agrupa municípios com características agrícolas homogêneas
    considerando produção histórica, produtividade (mediana), crescimento e riscos climáticos.
    Os clusters foram reordenados em ordem crescente de acordo com a produção média
    (0 = Menores produtores, 3 = Maiores produtores).
    """)

    if df_profiles.empty:
        st.warning("Perfis de clusters não disponíveis.")
    else:
        # 1. Cartões dos Perfis de Clusters (Com analogia de mercado de negócios)
        st.subheader("📋 Perfis dos Grupos de Produtores")

        col_c0, col_c1, col_c2, col_c3 = st.columns(4)

        profile_dict = df_profiles.set_index("cluster").to_dict(orient="index")

        with col_c0:
            p0 = profile_dict.get(0, {})
            st.markdown(
                f"""
            <div class="kpi-card" style="border-top: 5px solid #94a3b8;">
                <div class="kpi-title">Cluster 0: Baixa Escala</div>
                <div class="kpi-value" style="font-size: 1.55rem; margin-bottom: 8px;">
                    Prod. Média: {p0.get("prod_media", 0) / 1e3:.1f}k t
                </div>
                <div style="font-size: 0.95rem; opacity: 0.85; margin-top: 10px; line-height: 1.6;">
                    <b>Rendimento:</b> {p0.get("rendimento_medio_med", 0):,.0f} kg/ha<br>
                    <b>Volatilidade (CV):</b> {p0.get("volatilidade_prod", 0) * 100:.1f}%<br>
                    <b>Perda Área:</b> {p0.get("perda_area_media", 0) * 100:.2f}%<br>
                    <b>CAGR Prod:</b> {p0.get("cagr_producao", 0) * 100:.2f}%
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_c1:
            p1 = profile_dict.get(1, {})
            st.markdown(
                f"""
            <div class="kpi-card" style="border-top: 5px solid #60a5fa;">
                <div class="kpi-title">Cluster 1: Intermediário</div>
                <div class="kpi-value" style="font-size: 1.55rem; margin-bottom: 8px;">
                    Prod. Média: {p1.get("prod_media", 0) / 1e3:.1f}k t
                </div>
                <div style="font-size: 0.95rem; opacity: 0.85; margin-top: 10px; line-height: 1.6;">
                    <b>Rendimento:</b> {p1.get("rendimento_medio_med", 0):,.0f} kg/ha<br>
                    <b>Volatilidade (CV):</b> {p1.get("volatilidade_prod", 0) * 100:.1f}%<br>
                    <b>Perda Área:</b> {p1.get("perda_area_media", 0) * 100:.2f}%<br>
                    <b>CAGR Prod:</b> {p1.get("cagr_producao", 0) * 100:.2f}%
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_c2:
            p2 = profile_dict.get(2, {})
            st.markdown(
                f"""
            <div class="kpi-card" style="border-top: 5px solid #f59e0b;">
                <div class="kpi-title">Cluster 2: Eficiente / Alto Rend.</div>
                <div class="kpi-value" style="font-size: 1.55rem; margin-bottom: 8px;">
                    Prod. Média: {p2.get("prod_media", 0) / 1e3:.1f}k t
                </div>
                <div style="font-size: 0.95rem; opacity: 0.85; margin-top: 10px; line-height: 1.6;">
                    <b>Rendimento:</b> {p2.get("rendimento_medio_med", 0):,.0f} kg/ha<br>
                    <b>Volatilidade (CV):</b> {p2.get("volatilidade_prod", 0) * 100:.1f}%<br>
                    <b>Perda Área:</b> {p2.get("perda_area_media", 0) * 100:.2f}%<br>
                    <b>CAGR Prod:</b> {p2.get("cagr_producao", 0) * 100:.2f}%
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_c3:
            p3 = profile_dict.get(3, {})
            st.markdown(
                f"""
            <div class="kpi-card" style="border-top: 5px solid #10b981;">
                <div class="kpi-title">Cluster 3: Gigantes Agrícolas</div>
                <div class="kpi-value" style="font-size: 1.55rem; margin-bottom: 8px;">
                    Prod. Média: {p3.get("prod_media", 0) / 1e3:.1f}k t
                </div>
                <div style="font-size: 0.95rem; opacity: 0.85; margin-top: 10px; line-height: 1.6;">
                    <b>Rendimento:</b> {p3.get("rendimento_medio_med", 0):,.0f} kg/ha<br>
                    <b>Volatilidade (CV):</b> {p3.get("volatilidade_prod", 0) * 100:.1f}%<br>
                    <b>Perda Área:</b> {p3.get("perda_area_media", 0) * 100:.2f}%<br>
                    <b>CAGR Prod:</b> {p3.get("cagr_producao", 0) * 100:.2f}%
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.write("---")

        # 2. Visualização Espacial dos Clusters (Gráfico de Dispersão Interativo)
        st.subheader("📊 Distribuição de Clusters: Produção vs. Rendimento Médio Mediana")
        st.markdown("""
        * **Eixo X (Rendimento Médio Mediana):** Indica a eficiência técnica e produtiva do
          município isolando anos atípicos de quebra severa por seca (outliers negativos climáticos).
        * **Eixo Y (Produção Média):** Reflete a escala física absoluta do município (t).
        * **Tamanho dos Pontos:** Proporcional ao CAGR de Produção (velocidade de expansão).
        * **Cores:** Indicam a classificação do Cluster (K-Means K=4).
        """)

        fig_clusters = px.scatter(
            df_clusters,
            x="rendimento_medio_med",
            y="prod_media",
            color="Cluster_Label",
            size=df_clusters["cagr_producao"].apply(lambda x: max(x, 0.001) if not pd.isna(x) else 0.001),
            hover_name="municipio_nome",
            hover_data={
                "cluster": True,
                "rendimento_medio_med": ":,.0f",
                "prod_media": ":,.0f",
                "cagr_producao": ":.2%",
            },
            color_discrete_map={
                "Cluster 0: Baixa Escala": "#94a3b8",
                "Cluster 1: Intermediário": "#60a5fa",
                "Cluster 2: Eficiente / Alto Rend.": "#f59e0b",
                "Cluster 3: Gigantes Agrícolas": "#10b981",
            },
            category_orders={
                "Cluster_Label": [
                    "Cluster 0: Baixa Escala",
                    "Cluster 1: Intermediário",
                    "Cluster 2: Eficiente / Alto Rend.",
                    "Cluster 3: Gigantes Agrícolas",
                ]
            },
            labels={
                "rendimento_medio_med": "Rendimento Médio Mediana (kg/ha)",
                "prod_media": "Produção Média Histórica (toneladas)",
                "Cluster_Label": "Grupo (Cluster)",
            },
        )

        fig_clusters.update_layout(
            height=550,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=18)),
            font=dict(size=20),
            xaxis=dict(
                title=dict(font=dict(size=22)),
                tickfont=dict(size=18)
            ),
            yaxis=dict(
                title=dict(font=dict(size=22)),
                tickfont=dict(size=18)
            ),
        )
        st.plotly_chart(fig_clusters, width="stretch")

        st.write("---")

        # 3. Tabela Comparativa de Médias dos Clusters
        st.subheader("📊 Tabela Comparativa dos Perfis")
        df_profiles_display = df_profiles.copy()

        st.dataframe(
            df_profiles_display.rename(
                columns={
                    "cluster": "Cluster",
                    "prod_media": "Prod. Média (t)",
                    "rendimento_medio_med": "Rendimento Mediana (kg/ha)",
                    "cagr_producao": "Média CAGR Produção",
                    "cagr_rendimento": "Média CAGR Rendimento",
                    "trend_slope_producao": "Slope Tendência (t/ano)",
                    "volatilidade_prod": "Média Volatilidade (CV)",
                    "perda_area_media": "Média Perda de Área",
                }
            )
            .set_index("Cluster")
            .style.format(
                {
                    "Prod. Média (t)": "{:,.1f}",
                    "Rendimento Mediana (kg/ha)": "{:,.0f}",
                    "Média CAGR Produção": "{:.2%}",
                    "Média CAGR Rendimento": "{:.2%}",
                    "Slope Tendência (t/ano)": "{:,.1f}",
                    "Média Volatilidade (CV)": "{:.2%}",
                    "Média Perda de Área": "{:.2%}",
                }
            ),
            width="stretch",
        )
