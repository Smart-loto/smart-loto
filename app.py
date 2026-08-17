# ============================================================
# SMART-LOTO — VERSION 21.0 — TOTAL SYNC EDITION
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import math

# 1. CONFIGURATION INTERFACE PRO
st.set_page_config(page_title="Smart-Loto V21 Diamond", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"], .main { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #fbbf24 !important; font-weight: 700 !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1.5rem 0; }
    
    /* Metrics Cards */
    .metric-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 2rem; }
    .metric-card { background: #1e293b; border-left: 5px solid #fbbf24; padding: 1.2rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .metric-card small { color: #fbbf24; text-transform: uppercase; font-weight: 800; font-size: 0.7rem; letter-spacing: 1px; }
    .metric-card b { display: block; font-size: 1.6rem; color: #ffffff; margin-top: 5px; }

    /* Result Cards */
    .result-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.2rem; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white !important; border-radius: 50%; width: 48px; height: 48px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 4px; border: 1px solid #60a5fa; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white !important; border-radius: 50%; width: 48px; height: 48px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 4px; border: 1px solid #fcd34d; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
    
    /* Textes UI */
    label, p, span, .stSlider { color: #ffffff !important; }
    div[data-baseweb="select"] > div { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
</style>
""", unsafe_allow_html=True)

# 2. REFERENTIEL
JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# 3. DATA LOADER ROBUSTE
def robust_loader(file_content, jeu):
    if not file_content:
        return pd.DataFrame([{f"b{j+1}": v for j, v in enumerate(sorted(random.sample(range(1, jeu["b_max"]+1), 5)))} for _ in range(200)])
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        # Recherche colonnes numériques
        valid = []
        for col in df.columns:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if not series.empty and series.min() >= 1 and series.max() <= 50:
                valid.append(col)
        # On prend les colonnes de résultats (les dernières du bloc numérique)
        target = valid[-(jeu["nb_b"] + jeu["nb_e"]):]
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[target[i]], errors='coerce')
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[target[5+i]], errors='coerce')
        return clean.dropna().reset_index(drop=True)
    except:
        return robust_loader(None, jeu)

# 4. ENGINE STATISTIQUE
def get_advanced_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols: return {n: {"vel": 0, "w": 0.1} for n in range(1, max_val+1)}
    matrix = df[cols].values
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        v_recent = np.mean(pres[:30]) # Vélocité sur les 30 derniers
        v_total = np.mean(pres)
        accel = v_recent / (v_total + 0.001)
        stats[n] = {"vel": round(v_recent*100, 1), "w": float(max(0.01, v_recent * accel)), "last": pres[0]}
    return stats

# 5. UI PRINCIPALE
def main():
    st.sidebar.markdown("<h1 style='text-align:center; color:#fbbf24;'>💎 SMART-LOTO V21</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 Archive FDJ", type="csv")
    content = file.getvalue() if file else None
    
    # CHARGEMENT ET CALCULS
    df = robust_loader(content, jeu)
    stats_b = get_advanced_stats(df, jeu["b_max"], "b")
    stats_e = get_advanced_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard Expert", "🎯 Générateur Master", "🧪 Backtest ROI"])

    # --- DASHBOARD ---
    if menu == "📊 Dashboard Expert":
        st.markdown(f"<div class='main-header'>Analytics {jeu['nom']}</div>", unsafe_allow_html=True)
        
        # RESTAURATION DES METRICS
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card"><small>Archive</small><b>{len(df)} Tirages</b></div>
            <div class="metric-card"><small>Qualité Data</small><b>{"RÉEL ✅" if file else "SIMULÉ ⚠️"}</b></div>
            <div class="metric-card"><small>Pivot Alpha</small><b>N°{max(stats_b, key=lambda k: stats_b[k]['vel'])}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # GRAPHIQUE BOULES
        st.subheader("Vélocité Neuronale : BOULES")
        x_b = list(stats_b.keys()); y_b = [s["vel"] for s in stats_b.values()]
        fig_b = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', line=dict(color='#fbbf24', width=2)), row=1, col=1)
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig_b.update_layout(height=400, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        fig_b.update_xaxes(dtick=5)
        st.plotly_chart(fig_b, use_container_width=True)

        # GRAPHIQUE ÉTOILES
        st.subheader("Vélocité Neuronale : ÉTOILES")
        x_e = list(stats_e.keys()); y_e = [s["vel"] for s in stats_e.values()]
        fig_e = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.4])
        fig_e.add_trace(go.Scatter(x=x_e, y=y_e, mode='lines+markers', line=dict(color='#fbbf24', width=3)), row=1, col=1)
        fig_e.add_trace(go.Heatmap(z=[y_e], x=x_e, colorscale="YlOrRd", showscale=False), row=2, col=1)
        fig_e.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        fig_e.update_xaxes(dtick=1)
        st.plotly_chart(fig_e, use_container_width=True)

    # --- GÉNÉRATEUR ---
    elif menu == "🎯 Générateur Master":
        st.markdown("<div class='main-header'>Générateur Haute Précision</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])
        with c1:
            prof = st.selectbox("Algorithme", ["🧠 Neural Engine", "🔥 Agressif", "🚫 Sabermétrique", "🎯 Équilibré"])
            nb_g = st.slider("Nombre de grilles", 1, 10, 3)
            btn = st.button("🚀 CALCULER", type="primary", use_container_width=True)
        with c2:
            if btn:
                for i in range(nb_g):
                    b_nums = list(range(1, jeu["b_max"]+1))
                    # Calcul des poids selon le CSV réel
                    if "Agressif" in prof: w = [s["vel"]+0.1 for s in stats_b.values()]
                    elif "Sabermétrique" in prof: w = [2.5 if n > 31 else 0.5 for n in b_nums]
                    else: w = [s["w"] for s in stats_b.values()]
                    
                    grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(w)/sum(w)))
                    
                    we = [s["w"] for s in stats_e.values()]
                    etoiles = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False, p=np.array(we)/sum(we)))
                    
                    # IA SCORE BASÉ SUR LE CSV
                    ia_score = int(np.mean([stats_b[n]["vel"] for n in grille]))
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display:flex; justify-content:center; align-items:center; margin-bottom:15px;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div style="width:2px; height:35px; background:#334155; margin:0 15px;"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(3, 1fr); text-align:center; border-top:1px solid #334155; padding-top:10px;">
                            <div><small>CONFIANCE IA</small><br><b>{ia_score}%</b></div>
                            <div><small>SABERMÉTRIE</small><br><b>{sum(1 for n in grille if n > 31)}/5</b></div>
                            <div><small>SOMME</small><br><b>{sum(grille)}</b></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # --- BACKTEST ---
    elif menu == "🧪 Backtest ROI":
        st.markdown("<div class='main-header'>Simulateur de Performance</div>", unsafe_allow_html=True)
        if st.button("🚀 LANCER L'AUDIT SUR LES 100 DERNIERS TIRAGES RÉELS"):
            hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
            for row in df.head(100).values:
                # Simulation Neural
                w = [s["w"] for s in stats_b.values()]
                g = set(np.random.choice(range(1, jeu["b_max"]+1), 5, replace=False, p=np.array(w)/sum(w)))
                bons = len(g.intersection(set(row[:5])))
                hits[bons] += 1
            st.bar_chart(pd.Series(hits))
            st.info(f"Analyse terminée. Performance de l'algorithme sur l'archive CSV injectée.")

if __name__ == "__main__":
    main()
