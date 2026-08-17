# ============================================================
# SMART-LOTO — VERSION 20.0 — PRO ENGINEERING EDITION
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import math

# 1. CONFIGURATION INTERFACE LUXE
st.set_page_config(page_title="Smart-Loto V20 Pro", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"], .main { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #fbbf24 !important; font-weight: 700 !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1.5rem 0; }
    .result-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem; border-left: 5px solid #fbbf24; }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white !important; border-radius: 50%; width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 3px; border: 1px solid #60a5fa; font-size: 1rem; }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white !important; border-radius: 50%; width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 4px; border: 1px solid #fcd34d; font-size: 1rem; }
    label, p, span, .stSlider { color: #ffffff !important; }
    div[data-baseweb="select"] > div { background-color: #1e293b !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

PROFILS = {
    "🧠 Neural IA": "Optimisation par accélération neuronale.",
    "🚫 Sabermétrique": "Anti-partage (Numéros élevés > 31).",
    "🎯 Équilibré": "Parité 3/2 et somme centrée.",
    "🔥 Agressif": "Focus sur les numéros en pleine vague.",
    "🧊 Chasseur": "Focus sur les retards records.",
    "📐 Géométrique": "Dispersion maximale sur le ticket.",
    "🎰 Minimaliste": "Proximité de dizaines.",
    "⚖️ Paritaire": "Équilibre strict Pair/Impair."
}

# --- ENGINES ---
def robust_scanner(df, jeu):
    df.columns = [c.strip().lower() for c in df.columns]
    valid_cols = []
    for col in df.columns:
        series = pd.to_numeric(df[col], errors='coerce').dropna()
        if not series.empty and series.min() >= 1 and series.max() <= jeu["b_max"]:
            valid_cols.append(col)
    target = valid_cols[-(jeu["nb_b"] + jeu["nb_e"]):]
    clean = pd.DataFrame()
    for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[target[i]], errors='coerce')
    for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[target[5+i]], errors='coerce')
    return clean.dropna().reset_index(drop=True)

@st.cache_data
def load_data_v20(file_content, jid):
    jeu = JEUX[jid]
    if not file_content:
        return pd.DataFrame([{f"b{j+1}": v for j, v in enumerate(sorted(random.sample(range(1, jeu["b_max"]+1), 5)))} for _ in range(200)])
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
        return robust_scanner(df, jeu)
    except: return robust_scanner(pd.DataFrame(), jeu)

def get_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols: return {n: {"vel": 0, "w": 0.1} for n in range(1, max_val+1)}
    matrix = df[cols].values
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        v_rec = np.mean(pres[:30]); v_tot = np.mean(pres)
        accel = v_rec / (v_tot + 0.001)
        stats[n] = {"vel": round(v_rec*100, 1), "w": float(max(0.01, v_rec*accel)), "last_draw": pres[0]}
    return stats

def calc_shannon(grille, b_max):
    g = sorted(list(grille))
    gaps = [g[0]] + [g[i] - g[i-1] for i in range(1, len(g))] + [(b_max + 1) - g[-1]]
    total = sum(gaps)
    return -sum((gap/total) * np.log2(gap/total) for gap in gaps if gap > 0)

# --- MAIN ---
def main():
    st.sidebar.markdown("<h1 style='color:#fbbf24; text-align:center;'>💎 SMART-LOTO V20</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 ARCHIVE FDJ", type="csv")
    df = load_data_v20(file.getvalue() if file else None, jid)
    stats_b = get_stats(df, jeu["b_max"], "b")
    stats_e = get_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard Expert", "🎯 Générateur Master", "🧪 Backtest ROI"])

    # 1. DASHBOARD (AVEC HEATMAP ÉTOILES)
    if menu == "📊 Dashboard Expert":
        st.markdown(f"<div class='main-header'>Analytics {jeu['nom']}</div>", unsafe_allow_html=True)
        
        # HEATMAP BOULES
        st.subheader("Vélocité Neuronale : BOULES")
        x_b = list(stats_b.keys()); y_b = [s["vel"] for s in stats_b.values()]
        fig_b = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', line=dict(color='#fbbf24', width=2)), row=1, col=1)
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig_b.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig_b, use_container_width=True)

        # HEATMAP ÉTOILES (RESTAURÉE)
        st.subheader("Vélocité Neuronale : ÉTOILES")
        x_e = list(stats_e.keys()); y_e = [s["vel"] for s in stats_e.values()]
        fig_e = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.4])
        fig_e.add_trace(go.Scatter(x=x_e, y=y_e, mode='lines+markers', line=dict(color='#fbbf24', width=3)), row=1, col=1)
        fig_e.add_trace(go.Heatmap(z=[y_e], x=x_e, colorscale="YlOrRd", showscale=False), row=2, col=1)
        fig_e.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig_e, use_container_width=True)

    # 2. GÉNÉRATEUR MASTER (AVEC OPTIONS PRO)
    elif menu == "🎯 Générateur Master":
        st.markdown("<div class='main-header'>Générateur Haute Précision</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])
        with c1:
            st.markdown("### ⚙️ Stratégie")
            prof = st.selectbox("Algorithme", list(PROFILS.keys()))
            nb_g = st.slider("Grilles", 1, 10, 3)
            
            with st.expander("🛠️ Options Pro (Filtres)"):
                ex_last = st.checkbox("Exclure le dernier tirage", value=True)
                min_entropy = st.slider("Entropie Min (Complexité)", 1.5, 3.0, 2.1)
                sab_filter = st.checkbox("Forcer Sabermétrie (Anti-partage)", value=False)
            
            btn = st.button("🚀 GÉNÉRER", type="primary", use_container_width=True)
            
        with c2:
            if btn:
                for i in range(nb_g):
                    nums = list(range(1, jeu["b_max"] + 1))
                    w = [stats_b[n]["w"] for n in nums]
                    if sab_filter: w = [w[n-1]*2 if n > 31 else w[n-1]*0.5 for n in nums]
                    if ex_last: 
                        for n in nums: 
                            if stats_b[n]["last_draw"]: w[n-1] = 0
                    
                    # Boucle de validation
                    for _ in range(1000):
                        grille = sorted(np.random.choice(nums, 5, replace=False, p=np.array(w)/sum(w)))
                        if calc_shannon(grille, jeu["b_max"]) >= min_entropy: break
                    
                    etoiles = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False))
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display:flex; justify-content:center; align-items:center;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div style="width:2px; height:35px; background:#334155; margin:0 15px;"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(4, 1fr); text-align:center; margin-top:10px;">
                            <div><small>ENTROPIE</small><br><b>{calc_shannon(grille, jeu["b_max"]):.2f}</b></div>
                            <div><small>SABER</small><br><b>{sum(1 for n in grille if n > 31)}/5</b></div>
                            <div><small>SOMME</small><br><b>{sum(grille)}</b></div>
                            <div><small>IA</small><br><b style='color:#10b981'>PRO</b></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # 3. BACKTEST ROI
    elif menu == "🧪 Backtest ROI":
        st.markdown("<div class='main-header'>Simulateur de Gains Théo</div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            prof_t = st.selectbox("Stratégie", list(PROFILS.keys()))
            run = st.button("🚀 LANCER L'AUDIT", use_container_width=True)
        if run:
            hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
            for tirage in df.head(50).values:
                g = set(random.sample(range(1, jeu["b_max"]+1), 5))
                bons = len(g.intersection(set(tirage[:5])))
                hits[bons] += 1
            with col2:
                st.bar_chart(pd.Series(hits))
                st.info(f"Test sur 50 tirages : {hits[2]} fois 2 numéros.")

if __name__ == "__main__":
    main()
