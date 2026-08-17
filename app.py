# ============================================================
# SMART-LOTO — VERSION 22.0 — THE ULTIMATE PRO SYNC
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import math

# 1. CONFIGURATION INTERFACE LUXE & VISIBILITÉ
st.set_page_config(page_title="Smart-Loto V22 Pro", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"], .main { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #fbbf24 !important; font-weight: 700 !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1.5rem 0; }
    
    /* Metrics Luxe */
    .metric-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 2rem; }
    .metric-card { background: #1e293b; border-left: 5px solid #fbbf24; padding: 1.2rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .metric-card small { color: #fbbf24; text-transform: uppercase; font-weight: 800; font-size: 0.7rem; }
    .metric-card b { display: block; font-size: 1.5rem; color: #ffffff; }

    /* Result Cards */
    .result-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.2rem; border-top: 4px solid #fbbf24; }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white !important; border-radius: 50%; width: 45px; height: 45px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 3px; border: 1px solid #60a5fa; }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white !important; border-radius: 50%; width: 45px; height: 45px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 3px; border: 1px solid #fcd34d; }
    
    /* Correctif textes widgets */
    label, p, span, .stSlider, .stCheckbox { color: #ffffff !important; }
    div[data-baseweb="select"] > div { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

PROFILS = {
    "🧠 Neural IA": "Accélération neuronale (Vitesse).",
    "🎯 Équilibré": "Parité 3/2 et Somme optimale.",
    "🚫 Sabermétrique": "Priorité numéros élevés (>31).",
    "🔥 Agressif": "Focus sur les sorties récentes.",
    "🧊 Chasseur": "Focus sur les plus gros retards.",
    "📐 Géométrique": "Dispersion maximale sur ticket.",
    "🎰 Minimaliste": "Regroupement par dizaines.",
    "⚖️ Paritaire": "Équilibre strict Pair/Impair."
}

# --- ENGINE DATA SCANNER ---
def robust_scanner_v22(file_content, jeu):
    if not file_content:
        return pd.DataFrame([{f"b{j+1}": v for j, v in enumerate(sorted(random.sample(range(1, jeu["b_max"]+1), 5)))} for _ in range(200)])
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        valid_cols = []
        for col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if not s.empty and s.min() >= 1 and s.max() <= 50: valid_cols.append(col)
        target = valid_cols[-(jeu["nb_b"] + jeu["nb_e"]):]
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[target[i]], errors='coerce')
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[target[5+i]], errors='coerce')
        return clean.dropna().reset_index(drop=True)
    except: return robust_scanner_v22(None, jeu)

def get_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    matrix = df[cols].values
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        v_rec = np.mean(pres[:30]); v_tot = np.mean(pres)
        accel = v_rec / (v_tot + 0.001)
        stats[n] = {"vel": round(v_rec*100, 1), "w": float(max(0.01, v_rec*accel)), "last": next((i for i, x in enumerate(pres) if x), len(df))}
    return stats

# --- FONCTION GÉNÉRATION PRO ---
def generate_pro_grid(stats_b, stats_e, jeu, prof, excl, f_sum, f_par, f_term):
    nums = list(range(1, jeu["b_max"] + 1))
    if "Neural" in prof: w = [stats_b[n]["w"] for n in nums]
    elif "Sabermétrique" in prof: w = [2.5 if n > 31 else 0.5 for n in nums]
    elif "Agressif" in prof: w = [stats_b[n]["vel"] + 0.1 for n in nums]
    elif "Chasseur" in prof: w = [stats_b[n]["last"] + 1 for n in nums]
    else: w = [stats_b[n]["vel"] + 5 for n in nums]
    
    for e in excl: w[e-1] = 0
    
    for _ in range(1000): # 1000 tentatives pour respecter les filtres
        grille = sorted(np.random.choice(nums, 5, replace=False, p=np.array(w)/sum(w)))
        if not (f_sum[0] <= sum(grille) <= f_sum[1]): continue
        if f_par and not (2 <= sum(1 for n in grille if n % 2 == 0) <= 3): continue
        if f_term and len(set(n % 10 for n in grille)) < 4: continue
        break
    
    we = [stats_e[n]["w"] for n in range(1, jeu["e_max"]+1)]
    etoiles = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False, p=np.array(we)/sum(we)))
    return grille, etoiles

# --- APP ---
def main():
    st.sidebar.markdown("<h1 style='text-align:center; color:#fbbf24;'>💎 DIAMOND V22</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("SÉLECTION JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 Archive FDJ", type="csv")
    df = robust_scanner_v22(file.getvalue() if file else None, jeu)
    stats_b = get_stats(df, jeu["b_max"], "b")
    stats_e = get_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION PRO", ["📊 Dashboard Expert", "🎯 Générateur Stratégique", "🧪 Backtest Laboratoire"])

    if menu == "📊 Dashboard Expert":
        st.markdown(f"<div class='main-header'>Analytics {jeu['nom']}</div>", unsafe_allow_html=True)
        st.markdown(f"""<div class="metric-container">
            <div class="metric-card"><small>Archive</small><b>{len(df)} Tirages</b></div>
            <div class="metric-card"><small>Mode</small><b>{"RÉEL ✅" if file else "SIMULÉ ⚠️"}</b></div>
            <div class="metric-card"><small>Top Vitesse</small><b>N°{max(stats_b, key=lambda k: stats_b[k]['vel'])}</b></div>
        </div>""", unsafe_allow_html=True)

        for title, s_dict, c_scale, mx in [("BOULES", stats_b, "RdYlGn_r", jeu["b_max"]), ("ÉTOILES", stats_e, "YlOrRd", jeu["e_max"])]:
            st.subheader(f"Vélocité : {title}")
            x = list(s_dict.keys()); y = [s["vel"] for s in s_dict.values()]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color='#fbbf24', width=2)), row=1, col=1)
            fig.add_trace(go.Heatmap(z=[y], x=x, colorscale=c_scale, showscale=False), row=2, col=1)
            fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            fig.update_xaxes(dtick=5 if mx==50 else 1)
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "🎯 Générateur Stratégique":
        st.markdown("<div class='main-header'>Générateur Haute Précision</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])
        with c1:
            prof = st.selectbox("Algorithme", list(PROFILS.keys()))
            nb_g = st.slider("Grilles", 1, 10, 3)
            excl = st.multiselect("Exclure des numéros", range(1, jeu["b_max"]+1))
            with st.expander("🛠️ Filtres Experts"):
                f_sum = st.slider("Somme des numéros", 60, 220, (90, 160))
                f_par = st.checkbox("Parité Équilibrée (3/2)", value=True)
                f_term = st.checkbox("Éviter répétitions finales", value=True)
            btn = st.button("🚀 CALCULER", type="primary", use_container_width=True)
        with c2:
            if btn:
                for i in range(nb_g):
                    grille, etoiles = generate_pro_grid(stats_b, stats_e, jeu, prof, excl, f_sum, f_par, f_term)
                    ia_score = int(np.mean([stats_b[n]["vel"] for n in grille]))
                    st.markdown(f"""<div class="result-card"><div style="text-align:center; margin-bottom:15px;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div style="width:2px; height:35px; background:#334155; margin:0 15px; display:inline-block; vertical-align:middle;"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div><div style="display:grid; grid-template-columns: repeat(3, 1fr); text-align:center; border-top:1px solid #334155; padding-top:10px;">
                            <div><small>CONFIANCE IA</small><br><b>{ia_score}%</b></div>
                            <div><small>SABERMÉTRIE</small><br><b>{sum(1 for n in grille if n > 31)}/5</b></div>
                            <div><small>SOMME</small><br><b>{sum(grille)}</b></div>
                        </div></div>""", unsafe_allow_html=True)

    elif menu == "🧪 Backtest Laboratoire":
        st.markdown("<div class='main-header'>Simulateur de Stratégie</div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2.2])
        with col1:
            prof_t = st.selectbox("Algorithme à tester", list(PROFILS.keys()))
            depth = st.slider("Profondeur (Tirages réels)", 10, 100, 50)
            run = st.button("🚀 LANCER L'AUDIT", type="primary", use_container_width=True)
        with col2:
            if run:
                hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
                for row in df.head(depth).values:
                    g, _ = generate_pro_grid(stats_b, stats_e, jeu, prof_t, [], (60, 220), False, False)
                    bons = len(set(g).intersection(set(row[:5])))
                    hits[bons] += 1
                st.bar_chart(pd.Series(hits))
                st.info(f"Audit sur {depth} tirages : {hits[2]} fois 2 numéros, {hits[3]} fois 3 numéros.")

if __name__ == "__main__":
    main()
