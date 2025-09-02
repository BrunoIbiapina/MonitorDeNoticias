
import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from collections import Counter
import re
import html as _html  # escapar strings em cards

from src.fetch import fetch_news
from src.clean import clean_text, strip_html_keep_text
from src.sentiment import classify_text_series, SENTIMENT_ORDER
from src.utils import sentiment_counts, add_clickable_links, make_wordcloud_image

st.set_page_config(page_title="IA no Piauí — Monitor de Notícias", layout="wide")
st.markdown("""
<style>
.search-card {
    background: #fff;
    border: 1px solid #e3e7ee;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,.07);
    padding: 18px 16px 16px 16px;
    margin-bottom: 18px;
}
.search-card label, .search-card .stTextInput, .search-card .stSlider, .search-card .stSelectbox {
    margin-bottom: 10px !important;
}
.search-card .stButton button {
    background: #2563eb;
    color: #fff;
    border-radius: 8px;
    font-weight: 500;
    box-shadow: 0 1px 4px rgba(37,99,235,.08);
}
</style>
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 0.8rem; padding-bottom: 0.8rem;}
h1, h2, h3 { letter-spacing: .2px; }

/* Estilos para cartões KPI e badges */
.kpi-grid {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: .5rem;}
.kpi-card {
  background: var(--secondary-background-color, #1B1F2A);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 14px; padding: 16px 18px;
  box-shadow: 0 6px 18px rgba(0,0,0,.15);
}
.kpi-title {font-size: .85rem; opacity:.85; margin-bottom: 6px;}
.kpi-value {font-size: 2rem; font-weight: 700; line-height:1.1; margin: 0;}
.kpi-sub {font-size: .8rem; opacity:.7;}
.kpi-icon {font-size: 1.1rem; margin-right: .4rem; opacity:.9}

.badges {display:flex; flex-wrap:wrap; gap:8px; margin-top:.5rem;}
.badge {
  background: rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.08);
  padding: 6px 10px; border-radius: 999px; font-size: .85rem;
}

/* “cartões” de notícias */
.card {
  background: var(--secondary-background-color, #1B1F2A);
  border:1px solid rgba(255,255,255,.06); border-radius: 12px; padding: 12px 14px;
  margin-bottom: 10px;
}
.card a {text-decoration: none;}
.card .meta {font-size:.8rem; opacity:.7}
</style>
""", unsafe_allow_html=True)

st.title("IA no Piauí — Monitor de Notícias")
st.caption("Coleta via RSS do Google Notícias, limpeza, análise de sentimento por regras e visualização.")

def build_google_news_query(base: str, must: str = "", exclude: str = "", site: str = "") -> str:
    """
    Monta a query final aceitando:
      - base: texto livre (pode conter OR, aspas, etc.)
      - must: palavras/expressões obrigatórias separadas por vírgula
      - exclude: termos a excluir, separados por vírgula
      - site: domínio único (ex: meionorte.com)
    """
    parts = [base.strip()] if base and base.strip() else []

    def _terms(s):
        toks = [t.strip() for t in s.split(",") if t.strip()]
        fmt = []
        for t in toks:
            fmt.append(f'"{t}"' if " " in t else t)
        return fmt

    if must:
        parts.extend(_terms(must))

    if exclude:
        parts.extend([f"-{t}" for t in _terms(exclude)])

    if site:
        site = site.strip().replace("https://", "").replace("http://", "").replace("www.", "")
        if site:
            parts.append(f"site:{site}")

    return " ".join(parts).strip()

st.sidebar.markdown("## Consulta")

c1, c2, c3 = st.sidebar.columns(3)
if c1.button("IA Piauí", use_container_width=True):
    st.session_state["query_base"] = '("Inteligência Artificial" Piauí)'
if c2.button("SIA Piauí", use_container_width=True):
    st.session_state["query_base"] = '("SIA Piauí")'
if c3.button("IA Governo", use_container_width=True):
    st.session_state["query_base"] = '("Inteligência Artificial" governo Piauí)'

query_base = st.session_state.get("query_base", '("Inteligência Artificial" Piauí) OR ("SIA Piauí")')

with st.sidebar.form("search_form", clear_on_submit=False):
    base = st.text_input(
        "Termo de busca (Google News RSS)",
        value=query_base,
        placeholder='Ex.: "Inteligência Artificial" Piauí OR "SIA Piauí"',
    )
    qtd = st.slider("Quantidade de notícias", 5, 30, 15, 1)
    lang = st.selectbox("Idioma (hl)", ["pt-BR", "pt-PT", "en-US"], index=0)
    region = st.selectbox("Região (ceid)", ["BR:pt-419", "PT:pt-150", "US:en"], index=0)

    with st.expander("Filtros avançados"):
        must = st.text_input("Palavras obrigatórias (separe por vírgula)", value="")
        exclude = st.text_input("Palavras para excluir (separe por vírgula)", value="")
        site = st.text_input("Domínio (site:)", value="", placeholder="ex.: meionorte.com")

    submitted = st.form_submit_button("Coletar notícias", use_container_width=True)

final_query = build_google_news_query(base, must=must, exclude=exclude, site=site)
query = final_query
max_items = qtd
go = submitted

if not go:
    st.info("Use o painel lateral e clique em **Coletar notícias**.")
    st.stop()

@st.cache_data(show_spinner=False, ttl=600)
def get_news(query, max_items, lang, region):
    return fetch_news(query=query, max_items=max_items, hl=lang, ceid=region)

with st.spinner("Buscando RSS..."):
    news = get_news(query, max_items, lang, region)

if not news:
    st.warning("Sem notícias agora. Usando exemplo local.")
    news = [
        {"title": "Universidade lança laboratório de IA no Piauí", "link": "https://exemplo.local/1",
         "description": "Projeto destaca inovação e benefício para educação e economia regional.", "pubDate": None},
        {"title": "Debate sobre impactos da IA no Piauí", "link": "https://exemplo.local/2",
         "description": "Desafios e oportunidades foram discutidos por especialistas.", "pubDate": None},
    ]

df = pd.DataFrame(news)

df["data_pub"] = pd.to_datetime(df.get("pubDate"), errors="coerce", utc=True)

def _domain(url):
    try:
        host = urlparse(url).netloc
        return host.replace("www.", "") if host else ""
    except Exception:
        return ""

df["fonte"] = df.get("link", "").map(_domain)
df = df.drop_duplicates(subset=["link", "title"], keep="first").reset_index(drop=True)

df["descricao_limpa"] = df["description"].fillna("").map(strip_html_keep_text).map(clean_text)
df["sentimento"] = classify_text_series(df["descricao_limpa"])


counts = sentiment_counts(df["sentimento"])
total = len(df)

tab_overview, tab_graficos, tab_tabela, tab_nuvem = st.tabs(
    ["Visão Geral", "Gráficos", "Tabela", "Nuvem & Temas"]
)

with tab_overview:
    pos = int(counts.get("Positivo", 0))
    neu = int(counts.get("Neutro", 0))
    neg = int(counts.get("Negativo", 0))

    def perc(x):
        return f"{(x/total*100):.0f}%" if total else "0%"

    kpi_html = f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title"><span class="kpi-icon"></span>Total de notícias</div>
        <div class="kpi-value">{total}</div>
        <div class="kpi-sub">coletadas nesta busca</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title"><span class="kpi-icon"></span>Positivas</div>
        <div class="kpi-value">{pos}</div>
        <div class="kpi-sub">{perc(pos)} do total</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title"><span class="kpi-icon"></span>Neutras</div>
        <div class="kpi-value">{neu}</div>
        <div class="kpi-sub">{perc(neu)} do total</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title"><span class="kpi-icon"></span>Negativas</div>
        <div class="kpi-value">{neg}</div>
        <div class="kpi-sub">{perc(neg)} do total</div>
      </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

    st.divider()

    top_fontes = (
        df["fonte"].fillna("").replace("", pd.NA).dropna().value_counts().head(10).reset_index()
    )
    if top_fontes.shape[1] == 2:
        c0, c1 = top_fontes.columns
        top_fontes = top_fontes.rename(columns={c0: "Fonte", c1: "Quantidade"})
    else:
        top_fontes.columns = ["Fonte", "Quantidade"]

    st.subheader("Principais fontes")
    if not top_fontes.empty:
        badge_html = '<div class="badges">' + "".join(
            [f'<span class="badge">{row.Fonte} • {int(row.Quantidade)}</span>' for _, row in top_fontes.iterrows()]
        ) + "</div>"
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.info("Não foi possível identificar fontes nesta coleta.")

    st.divider()

    st.subheader("Últimas notícias")

    def humanize(ts):
        try:
            ts = pd.to_datetime(ts, errors="coerce")
            if pd.isna(ts):
                return ""
            ts = ts.tz_localize(None) if getattr(ts, "tzinfo", None) else ts
            delta = pd.Timestamp.now() - ts
            mins = int(delta.total_seconds() // 60)
            if mins < 1: return "agora"
            if mins < 60: return f"{mins} min atrás"
            hrs = mins // 60
            if hrs < 24: return f"{hrs} h atrás"
            dias = hrs // 24
            return f"{dias} d atrás"
        except Exception:
            return ""

    latest = df.sort_values("data_pub", ascending=False).head(6).copy()
    col_left, col_right = st.columns(2)

    for idx, r in enumerate(latest.itertuples(index=False)):
        titulo = r.title or "(sem título)"
        link = r.link or "#"
        fonte = r.fonte or ""
        quando = humanize(r.data_pub)
        desc_clean = (getattr(r, "descricao_limpa", "") or "").strip()
        desc_clean = (desc_clean[:200] + "…") if len(desc_clean) > 200 else desc_clean

        titulo = _html.escape(titulo)
        desc_clean = _html.escape(desc_clean)

        card_html = f"""
        <div class="card">
          <div><a href="{link}" target="_blank" rel="noopener noreferrer"><strong>{titulo}</strong></a></div>
          <div class="meta">{fonte} • {quando}</div>
          <div style="margin-top:6px">{desc_clean}</div>
        </div>
        """

        if idx % 2 == 0:
            with col_left:
                st.markdown(card_html, unsafe_allow_html=True)
        else:
            with col_right:
                st.markdown(card_html, unsafe_allow_html=True)

with tab_graficos:
    import plotly.express as px

    st.subheader("Distribuição de Sentimentos")
    series = pd.Series(counts).reindex(SENTIMENT_ORDER, fill_value=0)
    df_plot = series.reset_index()
    df_plot.columns = ["Sentimento", "Quantidade"]

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.caption("Barras")
        fig_bar = px.bar(
            df_plot, x="Sentimento", y="Quantidade", text="Quantidade",
            category_orders={"Sentimento": SENTIMENT_ORDER}
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title=None, yaxis_title=None,
            uniformtext_minsize=10, uniformtext_mode="hide",
            height=360, showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.caption("Donut (Pizza)")
        if df_plot["Quantidade"].sum() > 0:
            fig_pie = px.pie(
                df_plot[df_plot["Quantidade"] > 0],
                names="Sentimento", values="Quantidade",
                hole=0.55, category_orders={"Sentimento": SENTIMENT_ORDER},
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                legend_title=None, legend_orientation="h", legend_y=-0.12,
                height=360,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem dados para a pizza.")

    st.caption(
        f"**Resumo** — Positivo: {int(series.get('Positivo',0))} • "
        f"Neutro: {int(series.get('Neutro',0))} • "
        f"Negativo: {int(series.get('Negativo',0))}"
    )

with tab_tabela:
    st.subheader("Tabela de Notícias (com filtros)")

    colf1, colf2, colf3 = st.columns([1.2, 1, 1])
    termo = colf1.text_input("Filtrar por termo (título/descrição)", "")
    fontes = sorted([f for f in df["fonte"].dropna().unique() if f])
    sel_fontes = colf2.multiselect("Filtrar por fonte", fontes)
    sentimentos_opt = colf3.multiselect("Filtrar por sentimento", SENTIMENT_ORDER, default=SENTIMENT_ORDER)

    cdl, cdr = st.columns(2)
    min_dt = pd.to_datetime(df["data_pub"].min()) if not df["data_pub"].dropna().empty else None
    max_dt = pd.to_datetime(df["data_pub"].max()) if not df["data_pub"].dropna().empty else None
    date_initial = cdl.date_input("Data inicial", value=min_dt.date() if min_dt else None)
    date_final = cdr.date_input("Data final", value=max_dt.date() if max_dt else None)

    dff = df.copy()

    if termo:
        t = termo.strip().lower()
        dff = dff[
            dff["title"].fillna("").str.lower().str.contains(t) |
            dff["description"].fillna("").str.lower().str.contains(t)
        ]

    if sel_fontes:
        dff = dff[dff["fonte"].isin(sel_fontes)]

    if sentimentos_opt:
        dff = dff[dff["sentimento"].isin(sentimentos_opt)]

    if min_dt and max_dt and date_initial and date_final:
        d1 = pd.to_datetime(date_initial).date()
        d2 = pd.to_datetime(date_final).date()
        dff = dff[
            (dff["data_pub"].dt.date >= d1) &
            (dff["data_pub"].dt.date <= d2)
        ]

    df_show = dff[["title", "link", "description", "sentimento", "fonte", "data_pub"]].copy()
    df_show = add_clickable_links(df_show, "title", "link", new_col="título")
    if pd.api.types.is_datetime64tz_dtype(df_show["data_pub"]):
        df_show["data_pub"] = df_show["data_pub"].dt.tz_convert(None)
    df_show["data_pub"] = pd.to_datetime(df_show["data_pub"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M").fillna("")

    st.dataframe(
        df_show[["título", "sentimento", "fonte", "data_pub", "description"]],
        use_container_width=True,
    )

    csv = dff[["title", "link", "description", "sentimento", "fonte", "data_pub"]].to_csv(index=False)
    st.download_button("⬇️ Exportar CSV filtrado", data=csv, file_name="ia_piaui_noticias_filtrado.csv", mime="text/csv")

with tab_nuvem:
    st.subheader("Nuvem de Palavras")
    texto = " ".join(df["descricao_limpa"].tolist())
    img = make_wordcloud_image(texto)
    if img is not None:
        st.image(img, use_container_width=True)
    else:
        st.info("Nuvem indisponível (instale `pillow` e `wordcloud`).")

    st.subheader("Temas recorrentes")
    STOP = {
        "de","da","do","das","dos","a","o","as","os","e","é","em","um","uma","para","por",
        "com","no","na","nas","nos","que","se","sua","seu","são","ser","ao","à","às","ou",
        "mais","menos","sobre","entre","até","como","também","ja","já","apos","após","pela","pelo"
    }

    tokens = []
    for txt in df["descricao_limpa"].fillna(""):
        ws = [w for w in re.findall(r"[a-zà-ú0-9\-]+", txt) if w not in STOP and len(w) > 2]
        tokens.extend(ws)

    unigrams = Counter(tokens).most_common(15)
    bigrams = Counter(zip(tokens, tokens[1:])).most_common(15)
    bigrams = [(" ".join(bi), c) for bi, c in bigrams]

    col_a, col_b = st.columns(2)
    with col_a:
        st.caption(" Top palavras")
        st.dataframe(pd.DataFrame(unigrams, columns=["termo","freq"]), use_container_width=True)
    with col_b:
        st.caption("Top bigramas")
        st.dataframe(pd.DataFrame(bigrams, columns=["termo","freq"]), use_container_width=True)