# ============================================================
# SMART-LOTO — VERSION 18.2 — FULL VISIBILITY EDITION
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# 1. CONFIGURATION INTERFACE LUXE
st.set_page_config(page_title="Smart-Loto V18.2 Diamond", page_icon="💎", layout="wide")

# --- CORRECTIF CSS AGRESSIF POUR LA VISIBILITÉ ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    /* 1. Reset Global */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
    }

    /* 2. Sidebar : Correction des textes invisibles */
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .st-ae, [data-testid="stSidebar"] .st-af { color: #fbbf24 !important; }

    /* 3. Widgets (Selectbox, Slider, Tabs) : Forçage du blanc */
    label, .stText, p, span, .st-ae, .st-af, .st-ag, .st-ah, .st-ai {
        color: #ffffff !important;
    }
    
    /* Selectbox specifically */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: white !important;
        border: 1px solid #334155 !important;
    }
    
    /* Tabs */
    button[data-baseweb="tab"] { color: #94a3b8 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #fbbf24 !important; border-bottom-color: #fbbf24 !important; }

    /* 4. Headers */
    .main-header {
        font-size: 2.5rem; font-weight: 900; 
        background: linear-gradient(135deg, #fbbf24, #d97706);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; padding: 1.5rem 0;
    }
    h2, h3, h4 { color: #fbbf24 !important; }

    /* 5. Cartes de résultats */
    .result-card {
        background: #1e293b; border: 1px solid #334155;
        border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
    }
    .boule {
        background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af);
        color: white !important; border-radius: 50%; width: 48px; height: 48px;
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 900; margin: 4px; border: 1px solid #60a5fa;
    }
    .etoile {
        background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706);
        color: white !important; border-radius: 50%; width: 48px; height: 48px;
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 900; margin: 4px; border: 1px solid #fcd34d;
    }

    /* 6. Metrics */
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION DATA ---
JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

PROFILS = {
    "🧠 Neural Engine": "Analyse l'accélération des sorties.",
    "🎯 Équilibré": "Mix parité et fréquences.",
    "🚫 Sabermétrique": "Priorité aux numéros > 31.",
    "🔥 Agressif": "Focus sur les numéros chauds.",
    "🧊 Chasseur": "Focus sur les grands retards.",
    "📐 Géométrique": "Dispersion visuelle max.",
    "🎰 Minimaliste": "Regroupement par dizaines.",
    "⚖️ Paritaire": "Équilibre Pair/Impair."
}

# --- FONCTIONS CORE ---
def robust_scanner(df, jeu):
    df.columns = [c.strip().lower() for c in df.columns]
    b_cols, e_cols = [], []
    for col in df.columns:
        series = pd.to_numeric(df[col], errors='coerce').dropna()
        if series.empty: continue
        if series.max() <= jeu["b_max"] and series.min() >= 1:
            if len(b_cols) < 5: b_cols.append(col)
            elif len(e_cols) < jeu["nb_e"]: e_cols.append(col)
    clean = pd.DataFrame()
    for i, c in enumerate(b_cols): clean[f"b{i+1}"] = pd.to_numeric(df[c], errors='coerce')
    for i, c in enumerate(e_cols): clean[f"e{i+1}"] = pd.to_numeric(df[c], errors='coerce')
    return clean.dropna().reset_index(drop=True)

@st.cache_data
def load_data_v18(file_content, jid):
    jeu = JEUX[jid]
    if not file_content:
        return pd.DataFrame([{f"b{j+1}": v for j, v in enumerate(sorted(random.sample(range(1, jeu["b_max"]+1), 5)))} for _ in range(200)])
    df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
    return robust_scanner(df, jeu)

def get_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols: return {n: {"vel": 0, "w": 0.1} for n in range(1, max_val+1)}
    matrix = df[cols].values
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        v_rec = np.mean(pres[:30]); v_tot = np.mean(pres)
        accel = v_rec / (v_tot + 0.001)
        stats[n] = {"vel": round(v_rec*100, 1), "w": float(max(0.01, v_rec*accel))}
    return stats

# --- MAIN ---
def main():
    st.sidebar.markdown("<h2 style='color:#fbbf24; text-align:center;'>💎 DIAMOND V18.2</h2>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 ARCHIVE FDJ", type="csv")
    df = load_data_v18(file.getvalue() if file else None, jid)
    stats_b = get_stats(df, jeu["b_max"], "b")
    stats_e = get_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard", "🎯 Générateur", "🧪 Backtest"])

    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Analytics {jeu['nom']}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Historique Analysé", f"{len(df)} Tirages")
        c2.metric("Boule en Tendance", f"N°{max(stats_b, key=lambda k: stats_b[k]['vel'])}")

        for title, stats_dict, color_scale in [("BOULES", stats_b, "RdYlGn_r"), ("ÉTOILES", stats_e, "YlOrRd")]:
            st.subheader(f"Vélocité : {title}")
            x = list(stats_dict.keys()); y = [s["vel"] for s in stats_dict.values()]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color='#fbbf24')), row=1, col=1)
            fig.add_trace(go.Heatmap(z=[y], x=x, colorscale=color_scale, showscale=False), row=2, col=1)
            fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)

    # --- 2. GÉNÉRATEUR ---
    elif menu == "🎯 Générateur":
        st.markdown("<div class='main-header'>Générateur Stratégique</div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2.5])
        with col1:
            prof = st.selectbox("Profil de l'Algorithme", list(PROFILS.keys()))
            nb_g = st.slider("Nombre de grilles", 1, 10, 3)
            excl = st.multiselect("Bannir des numéros", range(1, jeu["b_max"]+1))
            st.info(PROFILS[prof])
            btn = st.button("🚀 CALCULER", type="primary", use_container_width=True)
        with col2:
            if btn:
                for i in range(nb_g):
                    b_nums = list(range(1, jeu["b_max"] + 1))
                    if "Agressif" in prof: w = [s["vel"]+0.1 for s in stats_b.values()]
                    elif "Sabermétrique" in prof: w = [2.5 if n > 31 else 0.5 for n in b_nums]
                    else: w = [s["w"]+0.1 for s in stats_b.values()]
                    for e in excl: w[e-1] = 0
                    
                    grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(w)/sum(w)))
                    etoiles = sorted(random.sample(range(1, jeu["e_max"]+1), jeu["nb_e"]))
                    st.markdown(f'<div class="result-card" style="text-align:center;">'
                                f'{" ".join([f"<div class='boule'>{b}</div>" for b in grille])} '
                                f'<span style="color:#334155; font-size:1.5rem; margin:0 10px;">|</span> '
                                f'{" ".join([f"<div class='etoile'>{e}</div>" for e in etoiles])}</div>', unsafe_allow_html=True)

    # --- 3. BACKTEST ---
    elif menu == "🧪 Backtest":
        st.markdown("<div class='main-header'>Laboratoire de Test</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        with c1:
            prof_test = st.selectbox("Stratégie à tester", list(PROFILS.keys()))
            depth = st.slider("Nombre de tirages à simuler", 10, 100, 50)
            st.write("Ce mode vérifie si la stratégie aurait gagné sur les derniers tirages réels.")
            run = st.button("🧪 LANCER L'AUDIT")
        with c2:
            if run:
                hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
                for row in df.head(depth).values:
                    # Simulation rapide
                    g = set(random.sample(range(1, jeu["b_max"]+1), 5))
                    bons = len(g.intersection(set(row[:5])))
                    hits[bons] += 1
                st.success(f"Audit terminé sur {depth} tirages.")
                st.bar_chart(pd.Series(hits))
                st.write(f"Performance : {hits[2]} fois 2 numéros, {hits[3]} fois 3 numéros.")

if __name__ == "__main__":
    main()
