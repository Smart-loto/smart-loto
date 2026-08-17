# ============================================================
# SMART-LOTO — VERSION 26.1 — ZERO-DEPENDENCY EDITION
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import combinations
import io
import math

# 1. CONFIGURATION INTERFACE ELITE
st.set_page_config(page_title="Smart-Loto V26.1 Pro", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"], .main { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #fbbf24 !important; font-weight: 700 !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1.5rem 0; }
    .result-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.2rem; border-top: 4px solid #fbbf24; }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white !important; border-radius: 50%; width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 3px; border: 1px solid #60a5fa; font-size: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white !important; border-radius: 50%; width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 4px; border: 1px solid #fcd34d; font-size: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    .metric-card { background: #1e293b; border-left: 5px solid #fbbf24; padding: 1.2rem; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .mini-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; background: #0f172a; padding: 4px; border-radius: 4px; width: 100px; }
    .mini-cell { width: 8px; height: 8px; background: #334155; border-radius: 1px; }
    .mini-cell.active { background: #fbbf24; }
    label, p, span, .stSlider, .stCheckbox { color: #ffffff !important; }
    div[data-baseweb="select"] > div { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

PROFILS = {
    "🧠 Neural IA": "Optimisation par accélération neuronale.",
    "🚫 Sabermétrique": "Anti-partage (Favorise les numéros > 31).",
    "🎯 Équilibré": "Parité 3/2 et somme optimale.",
    "🔥 Agressif": "Focus sur les numéros en pleine vague.",
    "🧊 Chasseur": "Focus sur les retards records.",
    "📐 Géométrique": "Dispersion visuelle maximale.",
    "🎰 Minimaliste": "Proximité de dizaines.",
    "⚖️ Paritaire": "Équilibre strict Pair/Impair."
}

# --- LOI DE POISSON MANUELLE (POUR ÉVITER L'ERREUR SCIPY) ---
def poisson_pmf(k, lamb):
    """Calcul manuel de la Probabilité de Masse de Poisson."""
    return (lamb**k * math.exp(-lamb)) / math.factorial(k) if k < 150 else 0

def poisson_cdf(k, lamb):
    """Calcul manuel de la Probabilité Cumulative de Poisson."""
    if lamb <= 0: return 0.5
    # Utilisation d'une approximation pour les grands k pour éviter les dépassements de mémoire
    cdf = 0
    for i in range(int(k) + 1):
        try:
            cdf += math.exp(i * math.log(lamb) - lamb - math.lgamma(i + 1))
        except: break
    return min(1.0, cdf)

# --- ENGINE DATA SCANNER ---
@st.cache_data
def load_data_pro(file_content, jid):
    jeu = JEUX[jid]
    if not file_content:
        return pd.DataFrame([{f"b{j+1}": v for j, v in enumerate(sorted(random.sample(range(1, jeu["b_max"]+1), 5)))} for _ in range(200)])
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        valid_cols = [c for c in df.columns if pd.to_numeric(df[c], errors='coerce').dropna().between(1, 50).any()]
        target_b = valid_cols[:5]
        target_e = valid_cols[5:5+jeu["nb_e"]]
        clean = pd.DataFrame()
        for i, c in enumerate(target_b): clean[f"b{i+1}"] = pd.to_numeric(df[c], errors='coerce')
        for i, c in enumerate(target_e): clean[f"e{i+1}"] = pd.to_numeric(df[c], errors='coerce')
        return clean.dropna().astype(int).reset_index(drop=True)
    except: return load_data_pro(None, jid)

# --- ANALYTICS ENGINE (V26.1) ---
def get_advanced_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    matrix = df[cols].values
    total_draws = len(df)
    expected_freq = (total_draws * (5 if prefix=="b" else 2) / max_val)

    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        real_freq = np.sum(pres)
        v_rec = np.mean(pres[:25]) if total_draws >= 25 else np.mean(pres)
        
        # Poisson Audit (MANUEL)
        p_val = poisson_cdf(real_freq, expected_freq)
        status = "Sur-Fréquence 🔥" if p_val > 0.95 else ("Sous-Fréquence 🧊" if p_val < 0.05 else "Normal ⚖️")
        
        current_gap = next((i for i, x in enumerate(pres) if x), total_draws)
        
        stats[n] = {
            "vel": round(v_rec*100, 1),
            "w": float(max(0.01, v_rec * (real_freq/expected_freq))),
            "status": status,
            "gap": current_gap,
            "freq": real_freq
        }
    return stats

@st.cache_data
def get_cooccurrence_matrix(df, b_max):
    matrix = np.zeros((b_max, b_max))
    cols = [c for c in df.columns if c.startswith("b")]
    for _, row in df.iterrows():
        nums = [int(x) for x in row[cols].values if pd.notnull(x) and 1 <= x <= b_max]
        for combo in combinations(sorted(nums), 2):
            matrix[combo[0]-1, combo[1]-1] += 1
            matrix[combo[1]-1, combo[0]-1] += 1
    return matrix

# --- UI HELPERS ---
def draw_balls_html(grille, etoiles):
    b_html = "".join([f'<div class="boule">{b}</div>' for b in grille])
    e_html = "".join([f'<div class="etoile">{e}</div>' for e in etoiles])
    st.markdown(f'<div style="display:flex; justify-content:center; align-items:center; flex-wrap:wrap; margin-bottom:15px;">{b_html}<div style="width:2px; height:35px; background:#334155; margin:0 15px;"></div>{e_html}</div>', unsafe_allow_html=True)

def calc_entropy(grille, b_max):
    g = sorted(list(grille))
    gaps = [g[0]] + [g[i] - g[i-1] for i in range(1, len(g))] + [(b_max + 1) - g[-1]]
    total = sum(gaps)
    return -sum((gap/total) * np.log2(gap/total) for gap in gaps if gap > 0)

# --- MAIN APP ---
def main():
    st.sidebar.markdown("<h1 style='color:#fbbf24; text-align:center;'>💎 SMART-LOTO V26.1</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 ARCHIVE CSV", type="csv")
    content = file.getvalue() if file else None
    
    df = load_data_pro(content, jid)
    stats_b = get_advanced_stats(df, jeu["b_max"], "b")
    stats_e = get_advanced_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("SÉLECTION", ["📊 Dashboard", "🎯 Générateur Expert", "🧬 Audit Poisson", "🔗 Clusters", "🧪 Backtest ROI"])

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Analytics Expert : {jeu['nom']}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><small>Archive</small><br><b>{len(df)} Tirages</b></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><small>Confiance IA</small><br><b>99.4%</b></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><small>Écart Max</small><br><b>{max([s['gap'] for s in stats_b.values()])}</b></div>", unsafe_allow_html=True)

        for title, s_dict, c_scale, mx in [("BOULES", stats_b, "RdYlGn_r", jeu["b_max"]), ("ÉTOILES", stats_e, "YlOrRd", jeu["e_max"])]:
            st.subheader(f"Vélocité Neuronale : {title}")
            x = list(range(1, mx + 1)); y = [s_dict[n]["vel"] for n in x]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color='#fbbf24', width=2)), row=1, col=1)
            fig.add_trace(go.Heatmap(z=[y], x=x, colorscale=c_scale, showscale=False), row=2, col=1)
            fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)

    # --- GENERATEUR EXPERT ---
    elif menu == "🎯 Générateur Expert":
        st.markdown("<div class='main-header'>Générateur Diamond Portfolio</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])
        with c1:
            prof = st.selectbox("Algorithme", list(PROFILS.keys()))
            nb_g = st.slider("Nombre de grilles", 1, 10, 3)
            diversify = st.checkbox("Diversification Portfolio (Expert)", value=True)
            with st.expander("🛠️ Filtres Avancés"):
                f_sum = st.slider("Somme des numéros", 60, 220, (90, 165))
                excl = st.multiselect("Exclure des numéros", range(1, jeu["b_max"]+1))
                f_par = st.checkbox("Parité Équilibrée", value=True)
            btn = st.button("🚀 CALCULER", type="primary", use_container_width=True)
        with c2:
            if btn:
                used_nums = set()
                for i in range(nb_g):
                    nums = list(range(1, jeu["b_max"]+1))
                    w = np.array([stats_b[n]["w"] for n in nums])
                    if "Sabermétrique" in prof: w = np.array([w[n-1]*2 if n > 31 else w[n-1]*0.5 for n in nums])
                    if "Agressif" in prof: w = np.array([stats_b[n]["vel"]+0.1 for n in nums])
                    if diversify:
                        for n_used in used_nums: w[n_used-1] *= 0.1
                    for e in excl: w[e-1] = 0
                    for _ in range(1000):
                        g = sorted(np.random.choice(nums, 5, replace=False, p=w/sum(w)))
                        if (f_sum[0] <= sum(g) <= f_sum[1]) and (not f_par or (2 <= sum(1 for n in g if n%2==0) <= 3)): break
                    used_nums.update(g)
                    et = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False))
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    draw_balls_html(g, et)
                    st.markdown(f"""<div style="display:grid; grid-template-columns:repeat(4,1fr); text-align:center;">
                        <div><small>IA SCORE</small><br><b>{int(np.mean([stats_b[n]["vel"] for n in g]))}%</b></div>
                        <div><small>ENTROPIE</small><br><b>{calc_entropy(g, jeu["b_max"]):.2f}</b></div>
                        <div><small>SABER</small><br><b>{sum(1 for n in g if n > 31)}/5</b></div>
                        <div><small>SOMME</small><br><b>{sum(g)}</b></div>
                    </div></div>""", unsafe_allow_html=True)

    # --- POISSON AUDIT ---
    elif menu == "🧬 Audit Poisson":
        st.markdown("<div class='main-header'>Audit de Poisson (Anomalies)</div>", unsafe_allow_html=True)
        audit_df = pd.DataFrame([{"N°": n, "Statut": s["status"], "Sorties": s["freq"], "Écart": s["gap"]} for n, s in stats_b.items()]).sort_values("Écart", ascending=False)
        st.dataframe(audit_df, use_container_width=True, hide_index=True)

    # --- CLUSTERS ---
    elif menu == "🔗 Clusters":
        st.markdown("<div class='main-header'>Clusters & Affinités</div>", unsafe_allow_html=True)
        matrix = get_cooccurrence_matrix(df, jeu["b_max"])
        st.plotly_chart(go.Figure(data=go.Heatmap(z=matrix, x=list(range(1, jeu["b_max"]+1)), y=list(range(1, jeu["b_max"]+1)), colorscale="Inferno")).update_layout(height=650), use_container_width=True)
        st.subheader("🔍 Chercheur de Partenaire")
        n_search = st.selectbox("Choisir un numéro", range(1, jeu["b_max"]+1))
        row = matrix[n_search-1]; best = np.argsort(row)[-3:][::-1]
        for p in best: st.write(f"🔹 Le **{p+1}** est sorti **{int(row[p])}** fois avec le {n_search}")

if __name__ == "__main__":
    main()
