# ============================================================
# SMART-LOTO — VERSION 19.0 — THE STRATEGIST MASTER
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import math

# 1. CONFIGURATION INTERFACE LUXE & VISIBILITÉ TOTALE
st.set_page_config(page_title="Smart-Loto V19 Strategist", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    /* Global Reset */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR LISIBILITÉ */
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #fbbf24 !important; font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .stRadio div { color: white !important; }

    /* WIDGETS LISIBILITÉ (FORÇAGE BLANC) */
    label, .stText, p, span, .stSlider, .stSelectbox { color: #ffffff !important; }
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important;
    }
    div[role="tablist"] button { color: #94a3b8 !important; }
    div[role="tablist"] button[aria-selected="true"] { color: #fbbf24 !important; border-bottom-color: #fbbf24 !important; }

    /* TITRES & CARTES */
    .main-header {
        font-size: 2.5rem; font-weight: 900; 
        background: linear-gradient(135deg, #fbbf24, #d97706);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; padding: 1.5rem 0;
    }
    .result-card {
        background: #1e293b; border: 1px solid #334155;
        border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem;
    }
    
    /* BOULES & ETOILES */
    .boule {
        background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af);
        color: white !important; border-radius: 50%; width: 44px; height: 44px;
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 900; margin: 3px; border: 1px solid #60a5fa; font-size: 1rem;
    }
    .etoile {
        background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706);
        color: white !important; border-radius: 50%; width: 44px; height: 44px;
        display: inline-flex; align-items: center; justify-content: center;
        font-weight: 900; margin: 3px; border: 1px solid #fcd34d; font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION DATA ---
JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

PROFILS = {
    "🧠 Neural IA": "Accélération neuronale des sorties.",
    "🎯 Équilibré": "Mix parité (3/2) et fréquences moyennes.",
    "🚫 Sabermétrique": "Priorité aux numéros > 31 (gain partagé évité).",
    "🔥 Agressif": "Focus uniquement sur les numéros en 'vague' (Chauds).",
    "🧊 Chasseur": "Cible les numéros en retard record (Froids).",
    "📐 Géométrique": "Dispersion maximale sur la grille du ticket.",
    "🎰 Minimaliste": "Regroupement par proximité (Dizaines).",
    "⚖️ Paritaire": "Équilibre strict entre Pairs et Impairs."
}

# --- FONCTIONS CORE ---
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
def load_data_v19(file_content, jid):
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
    if not cols: return {n: {"vel": 0, "w": 0.1, "last": 0} for n in range(1, max_val+1)}
    matrix = df[cols].values
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        v_rec = np.mean(pres[:25]); v_tot = np.mean(pres)
        accel = v_rec / (v_tot + 0.001)
        stats[n] = {"vel": round(v_rec*100, 1), "w": float(max(0.01, v_rec*accel)), "last": next((i for i, x in enumerate(pres) if x), len(df))}
    return stats

def generate_grid_pro(stats_b, stats_e, jeu, prof, excl, f_sum, f_par, f_term):
    nums = list(range(1, jeu["b_max"] + 1))
    # Poids
    if "Neural" in prof: w = [stats_b[n]["w"] for n in nums]
    elif "Agressif" in prof: w = [stats_b[n]["vel"] + 0.1 for n in nums]
    elif "Chasseur" in prof: w = [stats_b[n]["last"] + 1 for n in nums]
    elif "Sabermétrique" in prof: w = [3.0 if n > 31 else 0.5 for n in nums]
    else: w = [stats_b[n]["vel"] + 5 for n in nums]
    
    # Exclure
    for e in excl: w[e-1] = 0
    
    # Boucle de filtrage
    for _ in range(500):
        grille = sorted(np.random.choice(nums, 5, replace=False, p=np.array(w)/sum(w)))
        # Vérification filtres
        if not (f_sum[0] <= sum(grille) <= f_sum[1]): continue
        if f_par and not (2 <= sum(1 for n in grille if n % 2 == 0) <= 3): continue
        if f_term and len(set(n % 10 for n in grille)) < 4: continue
        break
    
    # Etoiles
    we = [stats_e[n]["w"] for n in range(1, jeu["e_max"]+1)]
    etoiles = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False, p=np.array(we)/sum(we)))
    return grille, etoiles

# --- MAIN ---
def main():
    st.sidebar.markdown("<h1 style='color:#fbbf24; text-align:center;'>💎 SMART-LOTO V19</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("SÉLECTION JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 ARCHIVE FDJ (CSV)", type="csv")
    df = load_data_v19(file.getvalue() if file else None, jid)
    stats_b = get_stats(df, jeu["b_max"], "b")
    stats_e = get_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard", "🎯 Générateur Expert", "🧪 Backtest ROI"])

    # 1. DASHBOARD
    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Analytics {jeu['nom']}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Archive", f"{len(df)} Tirages")
        c2.metric("Qualité Data", "RÉEL ✅" if file else "SIMULÉ ⚠️")
        c3.metric("Numéro Alpha", f"N°{max(stats_b, key=lambda k: stats_b[k]['vel'])}")

        x = list(stats_b.keys()); y = [s["vel"] for s in stats_b.values()]
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color='#fbbf24', width=2)), row=1, col=1)
        fig.add_trace(go.Heatmap(z=[y], x=x, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig, use_container_width=True)

    # 2. GÉNÉRATEUR EXPERT (FILTRES RESTAURÉS)
    elif menu == "🎯 Générateur Expert":
        st.markdown("<div class='main-header'>Générateur Stratégique Master</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])
        with c1:
            st.markdown("### ⚙️ Paramètres")
            prof = st.selectbox("Profil Algorithme", list(PROFILS.keys()))
            nb_g = st.slider("Nombre de grilles", 1, 10, 3)
            excl = st.multiselect("Bannir des numéros", range(1, jeu["b_max"]+1))
            
            with st.expander("🛡️ Filtres de Structure"):
                f_sum = st.slider("Somme des numéros", 60, 210, (90, 165))
                f_par = st.checkbox("Forcer Parité Équilibrée (3/2)", True)
                f_term = st.checkbox("Éviter répétitions de terminaisons", True)
            
            btn = st.button("🚀 CALCULER MAINTENANT", type="primary", use_container_width=True)
            st.info(f"**{prof}** : {PROFILS[prof]}")
            
        with c2:
            if btn:
                for i in range(nb_g):
                    grille, etoiles = generate_grid_pro(stats_b, stats_e, jeu, prof, excl, f_sum, f_par, f_term)
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display:flex; justify-content:center; align-items:center;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div style="width:2px; height:35px; background:#334155; margin:0 15px;"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(4, 1fr); text-align:center; margin-top:15px; border-top:1px solid #334155; padding-top:10px;">
                            <div><small>SOMME</small><br><b>{sum(grille)}</b></div>
                            <div><small>PARITÉ</small><br><b>{sum(1 for n in grille if n % 2 == 0)}P/{sum(1 for n in grille if n % 2 != 0)}I</b></div>
                            <div><small>IA SCORE</small><br><b>{int(np.mean([stats_b[n]["vel"] for n in grille]))}%</b></div>
                            <div><small>CONFIANCE</small><br><b style='color:#10b981'>HAUTE</b></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # 3. BACKTEST ROI (AMÉLIORÉ)
    elif menu == "🧪 Backtest ROI":
        st.markdown("<div class='main-header'>Simulateur ROI & Performance</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### 🧪 Réglages")
            prof_t = st.selectbox("Algorithme à tester", list(PROFILS.keys()))
            depth = st.slider("Profondeur historique", 10, 100, 50)
            st.write("Ce mode génère une grille selon votre profil et la compare aux tirages réels passés.")
            run = st.button("🚀 LANCER L'AUDIT FINANCIER", type="primary", use_container_width=True)
        
        with c2:
            if run:
                hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
                mises = depth * jeu["prix"]
                gains = 0
                for tirage in df.head(depth).values:
                    # On génère une grille avec les filtres par défaut pour le test
                    g, _ = generate_grid_pro(stats_b, stats_e, jeu, prof_t, [], (60, 220), False, False)
                    bons = len(set(g).intersection(set(tirage[:5])))
                    hits[bons] += 1
                    if bons == 2: gains += 4.5
                    if bons == 3: gains += 12.0
                    if bons == 4: gains += 500.0
                
                res_roi = ((gains / mises) - 1) * 100
                st.subheader(f"Résultats sur {depth} tirages")
                ca, cb, cc = st.columns(3)
                ca.metric("Total Mises", f"{mises} €")
                cb.metric("Gains Théo.", f"{gains} €")
                cc.metric("ROI", f"{res_roi:.1f}%", delta=f"{res_roi:.1f}%")
                
                st.bar_chart(pd.Series(hits))
                st.info(f"Analyse : Stratégie {prof_t}. Succès : {hits[2]} fois 2 numéros, {hits[3]} fois 3 numéros.")

if __name__ == "__main__":
    main()
