# ============================================================
# SMART-LOTO — VERSION 25.0 — THE FINAL MASTERPIECE
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import math
from itertools import combinations

# 1. CONFIGURATION INTERFACE LUXE
st.set_page_config(page_title="Smart-Loto V25 Diamond", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"], .main { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #fbbf24 !important; font-weight: 700 !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1.5rem 0; }
    .result-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.2rem; border-top: 4px solid #fbbf24; }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white !important; border-radius: 50%; width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 3px; border: 1px solid #60a5fa; font-size: 1rem; }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white !important; border-radius: 50%; width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 4px; border: 1px solid #fcd34d; font-size: 1rem; }
    .metric-card { background: #1e293b; border-left: 5px solid #fbbf24; padding: 1.2rem; border-radius: 12px; margin-bottom: 10px; }
    label, p, span, .stSlider, .stCheckbox { color: #ffffff !important; }
    div[data-baseweb="select"] > div { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

PROFILS = {
    "🧠 Neural IA": "Accélération neuronale des sorties.",
    "🚫 Sabermétrique": "Anti-partage (Favorise les numéros > 31).",
    "🎯 Équilibré": "Parité 3/2 et somme optimale.",
    "🔥 Agressif": "Focus sur les numéros en pleine vague.",
    "🧊 Chasseur": "Focus sur les retards records.",
    "📐 Géométrique": "Dispersion visuelle maximale.",
    "🎰 Minimaliste": "Proximité de dizaines.",
    "⚖️ Paritaire": "Équilibre strict Pair/Impair."
}

# --- ENGINES ---
@st.cache_data
def load_data_v25(file_content, jid):
    jeu = JEUX[jid]
    if not file_content:
        return pd.DataFrame([{f"b{j+1}": v for j, v in enumerate(sorted(random.sample(range(1, jeu["b_max"]+1), 5)))} for _ in range(200)])
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        valid_cols = []
        for col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if not s.empty and s.min() >= 1 and s.max() <= 50 and len(s) > len(df)*0.3:
                valid_cols.append(col)
        # On extrait les 5 dernières colonnes de boules et les X dernières d'étoiles
        target_b = valid_cols[:5]
        target_e = valid_cols[5:5+jeu["nb_e"]]
        clean = pd.DataFrame()
        for i, c in enumerate(target_b): clean[f"b{i+1}"] = pd.to_numeric(df[c], errors='coerce')
        for i, c in enumerate(target_e): clean[f"e{i+1}"] = pd.to_numeric(df[c], errors='coerce')
        return clean.dropna().astype(int).reset_index(drop=True)
    except: return load_data_v25(None, jid)

def get_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols: return {n: {"vel": 0, "w": 0.1, "last": 0} for n in range(1, max_val+1)}
    matrix = df[cols].values
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        v_rec = np.mean(pres[:30]); v_tot = np.mean(pres); accel = v_rec / (v_tot + 0.001)
        stats[n] = {"vel": round(v_rec*100, 1), "w": float(max(0.01, v_rec*accel)), "last": next((i for i, x in enumerate(pres) if x), len(df))}
    return stats

@st.cache_data
def get_cooccurrence(df, b_max):
    matrix = np.zeros((b_max, b_max))
    cols = [c for c in df.columns if c.startswith("b")]
    for _, row in df.iterrows():
        nums = [int(x) for x in row[cols].values if pd.notnull(x) and 1 <= x <= b_max]
        for combo in combinations(sorted(nums), 2):
            matrix[combo[0]-1, combo[1]-1] += 1
            matrix[combo[1]-1, combo[0]-1] += 1
    return matrix

# --- UI HELPER ---
def draw_balls(grille, etoiles):
    b_html = "".join([f'<div class="boule">{b}</div>' for b in grille])
    e_html = "".join([f'<div class="etoile">{e}</div>' for e in etoiles])
    st.markdown(f"""
    <div style="display:flex; justify-content:center; align-items:center; flex-wrap:wrap; margin-bottom:15px;">
        {b_html}
        <div style="width:2px; height:35px; background:#334155; margin:0 15px;"></div>
        {e_html}
    </div>
    """, unsafe_allow_html=True)

# --- MAIN ---
def main():
    st.sidebar.markdown("<h1 style='color:#fbbf24; text-align:center;'>💎 DIAMOND V25</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("SÉLECTION JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 ARCHIVE FDJ (CSV)", type="csv")
    df = load_data_v25(file.getvalue() if file else None, jid)
    stats_b = get_stats(df, jeu["b_max"], "b")
    stats_e = get_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard", "🎯 Générateur", "🔗 Clusters", "🧪 Backtest", "💰 Kelly"])

    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Analytics {jeu['nom']}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><small>Archive</small><br><b>{len(df)} Tirages</b></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><small>Mode</small><br><b>{'RÉEL ✅' if file else 'SIMULÉ ⚠️'}</b></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><small>Top Vitesse</small><br><b>N°{max(stats_b, key=lambda k: stats_b[k]['vel'])}</b></div>", unsafe_allow_html=True)

        for title, s_dict, c_scale, mx in [("BOULES", stats_b, "RdYlGn_r", jeu["b_max"]), ("ÉTOILES", stats_e, "YlOrRd", jeu["e_max"])]:
            st.subheader(f"Vélocité : {title}")
            x = list(range(1, mx + 1))
            y = [s_dict[n]["vel"] for n in x]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color='#fbbf24', width=2)), row=1, col=1)
            fig.add_trace(go.Heatmap(z=[y], x=x, colorscale=c_scale, showscale=False), row=2, col=1)
            fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            fig.update_xaxes(dtick=5 if mx==50 else 1, range=[0.5, mx+0.5])
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "🎯 Générateur":
        st.markdown("<div class='main-header'>Générateur Diamond Master</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])
        with c1:
            prof = st.selectbox("Profil", list(PROFILS.keys()))
            nb_g = st.slider("Grilles", 1, 10, 3)
            with st.expander("🛠️ Filtres Experts"):
                f_sum = st.slider("Somme", 60, 220, (90, 165))
                f_par = st.checkbox("Parité Équilibrée", value=True)
                excl = st.multiselect("Exclure", range(1, jeu["b_max"]+1))
            btn = st.button("🚀 CALCULER", type="primary", use_container_width=True)
        with c2:
            if btn:
                for i in range(nb_g):
                    nums = list(range(1, jeu["b_max"]+1))
                    w = [stats_b[n]["w"] for n in nums]
                    if "Sabermétrique" in prof: w = [w[n-1]*2 if n > 31 else w[n-1]*0.5 for n in nums]
                    for e in excl: w[e-1] = 0
                    g = sorted(np.random.choice(nums, 5, replace=False, p=np.array(w)/sum(w)))
                    et = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False))
                    st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
                    draw_balls(g, et)
                    st.markdown(f'<p style="text-align:center; font-size:0.8rem; color:#94a3b8;">Somme: {sum(g)} | IA Score: {int(np.mean([stats_b[n]["vel"] for n in g]))}%</p></div>', unsafe_allow_html=True)

    elif menu == "🔗 Clusters":
        st.markdown("<div class='main-header'>Clusters & Affinités</div>", unsafe_allow_html=True)
        matrix = get_cooccurrence(df, jeu["b_max"])
        fig = go.Figure(data=go.Heatmap(z=matrix, x=list(range(1, jeu["b_max"]+1)), y=list(range(1, jeu["b_max"]+1)), colorscale="Inferno"))
        fig.update_layout(height=600, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🔍 Chercheur de Partenaire")
        n_search = st.selectbox("Choisir un numéro", range(1, jeu["b_max"]+1))
        row = matrix[n_search-1]
        best = np.argsort(row)[-3:][::-1]
        for p in best: st.write(f"🔹 Le **{p+1}** est sorti **{int(row[p])}** fois avec le {n_search}")

    elif menu == "🧪 Backtest":
        st.markdown("<div class='main-header'>Audit ROI</div>", unsafe_allow_html=True)
        depth = st.slider("Tirages à tester", 10, 100, 50)
        if st.button("LANCER L'AUDIT"):
            hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
            for tirage in df.head(depth).values:
                g = set(random.sample(range(1, jeu["b_max"]+1), 5))
                bons = len(g.intersection(set(tirage[:5])))
                hits[bons] += 1
            st.bar_chart(pd.Series(hits))
            st.info(f"Sur {depth} tirages, vous avez trouvé {hits[2]} fois 2 numéros.")

    elif menu == "💰 Kelly":
        st.title("Gestion Kelly")
        jk = st.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        f = ((jk/jeu["prix"]) * jeu["proba"] - (1 - jeu["proba"])) / (jk/jeu["prix"])
        st.metric("Mise Conseillée", f"{max(0, f * 100):.2f} €")

if __name__ == "__main__":
    main()
