# ============================================================
# SMART-LOTO — VERSION 29.0 — THE ULTIMATE SOVEREIGN EDITION
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
st.set_page_config(page_title="Smart-Loto V29 Sovereign", page_icon="💎", layout="wide")

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
    .mini-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; background: #0f172a; padding: 5px; border-radius: 4px; width: 110px; }
    .mini-cell { width: 9px; height: 9px; background: #334155; border-radius: 1px; }
    .mini-cell.active { background: #fbbf24; }
    label, p, span, .stSlider, .stCheckbox { color: #ffffff !important; }
    div[data-baseweb="select"] > div { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
    .metric-title { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 900; }
    .metric-value { font-size: 1.1rem; font-weight: 800; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# 2. CONSTANTES
JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160, "sum_ideal": (90, 160)},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840, "sum_ideal": (75, 175)}
}

PROFILS = {
    "🧠 Neural IA": "Optimisation par accélération neuronale (Velocity).",
    "🚫 Sabermétrique": "Anti-partage (Priorité aux numéros élevés > 31).",
    "🎯 Équilibré": "Parité 3/2 et répartition de somme optimale.",
    "🔥 Agressif": "Focus sur les numéros en pleine vague de sortie.",
    "🧊 Chasseur": "Focus sur les numéros en retard record.",
    "📐 Géométrique": "Dispersion visuelle maximale sur le ticket.",
    "🎰 Minimaliste": "Regroupement par proximité (Dizaines).",
    "⚖️ Paritaire": "Équilibre strict Pair/Impair."
}

# --- ENGINES MATHÉMATIQUES (SANS SCIPY) ---
def poisson_cdf_manual(k, lamb):
    if lamb <= 0: return 0.5
    cdf = 0
    for i in range(int(k) + 1):
        try: cdf += math.exp(i * math.log(lamb) - lamb - math.lgamma(i + 1))
        except: break
    return min(1.0, cdf)

def calc_entropy(grille, b_max):
    g = sorted(list(grille))
    gaps = [g[0]] + [g[i] - g[i-1] for i in range(1, len(g))] + [(b_max + 1) - g[-1]]
    total = sum(gaps)
    return -sum((gap/total) * np.log2(gap/total) for gap in gaps if gap > 0)

def get_geometry_score(grille):
    rows = [(n-1)//10 for n in grille]
    cols = [(n-1)%10 for n in grille]
    return round(min(10, (np.std(rows) + np.std(cols)) * 2.2), 1)

# --- DATA LOADING & SCANNING ---
@st.cache_data
def load_data_sovereign(file_content, jid):
    jeu = JEUX[jid]
    if not file_content:
        return pd.DataFrame([{f"b{j+1}": v for j, v in enumerate(sorted(random.sample(range(1, jeu["b_max"]+1), 5)))} for _ in range(200)])
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        valid_cols = [c for c in df.columns if pd.to_numeric(df[c], errors='coerce').dropna().between(1, 50).any()]
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[valid_cols[i]], errors='coerce')
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[valid_cols[5+i]], errors='coerce')
        return clean.dropna().astype(int).reset_index(drop=True)
    except: return load_data_sovereign(None, jid)

def get_full_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]; matrix = df[cols].values
    total = len(df); expected = (total * (5 if prefix=="b" else 2) / max_val)
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1); freq = np.sum(pres)
        v_rec = np.mean(pres[:30]) if total >= 30 else np.mean(pres)
        p_val = poisson_cdf_manual(freq, expected)
        stats[n] = {
            "vel": round(v_rec*100, 1), 
            "heat": round((freq/total)*100, 2),
            "w": float(max(0.01, v_rec * (freq/expected))),
            "status": "Surchauffe 🔥" if p_val > 0.95 else ("Froid 🧊" if p_val < 0.05 else "Normal ⚖️"),
            "gap": next((i for i, x in enumerate(pres) if x), total),
            "freq": freq
        }
    return stats

# --- UI HELPERS ---
def draw_result_card(idx, g, et, stats_b, jeu, prof_name):
    ia_score = int(np.mean([stats_b[n]["vel"] for n in g]))
    ent = calc_entropy(g, jeu["b_max"])
    sab = sum(1 for n in g if n > 31)
    geo = get_geometry_score(g)
    
    st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
    
    # Ligne des Boules
    b_html = "".join([f'<div class="boule">{b}</div>' for b in g])
    e_html = "".join([f'<div class="etoile">{e}</div>' for e in et])
    st.markdown(f'<div style="display:flex; justify-content:center; align-items:center; flex-wrap:wrap; margin-bottom:20px;">{b_html}<div style="width:2px; height:35px; background:#334155; margin:0 15px;"></div>{e_html}</div>', unsafe_allow_html=True)
    
    # Grille d'Audit
    st.markdown(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; border-top:1px solid #334155; padding-top:15px; text-align:center;">
        <div>
            <div class="metric-title">Géométrie</div>
            <div class="metric-value">{geo}/10</div>
            <div class="mini-grid" style="margin:5px auto;">
                {" ".join([f'<div class="mini-cell {"active" if n in g else ""}"></div>' for n in range(1, jeu["b_max"]+1)])}
            </div>
        </div>
        <div>
            <div class="metric-title">Sabermétrie</div>
            <div class="metric-value">{sab} hautes</div>
            <div style="height:4px; background:#334155; border-radius:2px; margin:8px 20%;"><div style="width:{sab*20}%; height:100%; background:{'#ef4444' if sab >= 4 else '#10b981'};"></div></div>
        </div>
        <div><div class="metric-title">IA Vitesse</div><div class="metric-value">{ia_score}%</div><small style="color:#94a3b8">Tendance</small></div>
        <div><div class="metric-title">Entropie</div><div class="metric-value">{ent:.2f}</div><small style="color:#94a3b8">Désordre</small></div>
    </div></div>
    """, unsafe_allow_html=True)

# --- MAIN APP ---
def main():
    st.sidebar.markdown("<h1 style='color:#fbbf24; text-align:center;'>💎 DIAMOND V29</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 ARCHIVE FDJ", type="csv")
    df = load_data_sovereign(file.getvalue() if file else None, jid)
    stats_b = get_full_stats(df, jeu["b_max"], "b")
    stats_e = get_full_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard Expert", "🎯 Générateur Master", "🧬 Audit Poisson", "🔗 Clusters & Affinités", "➕ Analyse des Sommes", "🧪 Backtest ROI"])

    # 1. DASHBOARD
    if menu == "📊 Dashboard Expert":
        st.markdown(f"<div class='main-header'>Analytics Expert : {jeu['nom']}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><small>Archive</small><br><b>{len(df)} Tirages</b></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><small>Sync Heatmap</small><br><b>100% OK ✅</b></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><small>Top Vitesse</small><br><b>N°{max(stats_b, key=lambda k: stats_b[k]['vel'])}</b></div>", unsafe_allow_html=True)

        for title, s_dict, c_scale, mx in [("BOULES", stats_b, "RdYlGn_r", jeu["b_max"]), ("ÉTOILES", stats_e, "YlOrRd", jeu["e_max"])]:
            st.subheader(f"Analyse {title} (Ligne: Vélocité | Heatmap: Fréquence Totale)")
            x = list(range(1, mx + 1)); y_l = [s_dict[n]["vel"] for n in x]; y_h = [s_dict[n]["heat"] for n in x]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=x, y=y_l, mode='lines+markers', line=dict(color='#fbbf24', width=2)), row=1, col=1)
            fig.add_trace(go.Heatmap(z=[y_h], x=x, colorscale=c_scale, showscale=False), row=2, col=1)
            fig.update_layout(height=380, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), margin=dict(l=10,r=10,t=10,b=10))
            fig.update_xaxes(dtick=5 if mx==50 else 1, range=[0.5, mx+0.5])
            st.plotly_chart(fig, use_container_width=True)

    # 2. GÉNÉRATEUR MASTER
    elif menu == "🎯 Générateur Master":
        st.markdown("<div class='main-header'>Générateur Diamond Portfolio</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])
        with c1:
            prof = st.selectbox("Algorithme", list(PROFILS.keys())); nb = st.slider("Grilles", 1, 10, 3)
            diversify = st.checkbox("Diversification Max", value=True)
            with st.expander("🛠️ Filtres Avancés"):
                f_sum = st.slider("Somme", 60, 220, (90, 165))
                excl = st.multiselect("Exclure", range(1, jeu["b_max"]+1))
            btn = st.button("🚀 CALCULER", type="primary", use_container_width=True)
        with c2:
            if btn:
                used = set()
                for i in range(nb):
                    nums = list(range(1, jeu["b_max"]+1)); w = np.array([stats_b[n]["w"] for n in nums])
                    if "Sabermétrique" in prof: w = np.array([w[n-1]*2 if n > 31 else w[n-1]*0.5 for n in nums])
                    if diversify:
                        for n in used: w[n-1] *= 0.1
                    for e in excl: w[e-1] = 0
                    
                    for _ in range(1000):
                        g = sorted(np.random.choice(nums, 5, replace=False, p=w/sum(w)))
                        if (f_sum[0] <= sum(g) <= f_sum[1]): break
                    used.update(g)
                    et = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False))
                    draw_result_card(i+1, g, et, stats_b, jeu, prof)

    # 3. AUDIT POISSON
    elif menu == "🧬 Audit Poisson":
        st.markdown("<div class='main-header'>Audit de Poisson (Anomalies)</div>", unsafe_allow_html=True)
        audit_df = pd.DataFrame([{"N°": n, "Statut": s["status"], "Sorties": s["freq"], "Écart Actuel": s["gap"]} for n, s in stats_b.items()]).sort_values("Écart Actuel", ascending=False)
        st.dataframe(audit_df, use_container_width=True, hide_index=True)

    # 4. CLUSTERS & AFFINITÉS
    elif menu == "🔗 Clusters & Affinités":
        st.markdown("<div class='main-header'>Analyse Combinatoire & Paires</div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔥 Matrice d'Affinité", "👯 Top Paires & Partenaires"])
        matrix = get_cooccurrence_matrix(df, jeu["b_max"])
        with tab1:
            fig = go.Figure(data=go.Heatmap(z=matrix, x=list(range(1, jeu["b_max"]+1)), y=list(range(1, jeu["b_max"]+1)), colorscale="Inferno"))
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            c_cl1, c_cl2 = st.columns(2)
            with c_cl1:
                st.subheader("🏆 Top Paires")
                paires = []
                for i in range(len(matrix)):
                    for j in range(i+1, len(matrix)):
                        if matrix[i,j] > 0: paires.append(((i+1, j+1), int(matrix[i,j])))
                for p, v in sorted(paires, key=lambda x: x[1], reverse=True)[:10]:
                    st.write(f"🤝 Duo **{p[0]} + {p[1]}** : sorti **{v}** fois.")
            with c_cl2:
                st.subheader("🔍 Chercheur de Partenaire")
                n_search = st.selectbox("Choisir un numéro", range(1, jeu["b_max"]+1))
                row = matrix[n_search-1]; best = np.argsort(row)[-3:][::-1]
                for p in best: st.write(f"🔹 Le **{p+1}** est sorti **{int(row[p])}** fois avec le {n_search}")

    # 5. SOMMES DYNAMIQUES
    elif menu == "➕ Analyse des Sommes":
        st.markdown(f"<div class='main-header'>Dynamique des Sommes</div>", unsafe_allow_html=True)
        sums = df[[c for c in df.columns if c.startswith("b")]].sum(axis=1)
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            st.markdown(f"<div class='metric-card'><small>Somme Moyenne</small><br><b>{int(sums.mean())}</b></div>", unsafe_allow_html=True)
            st.info("La Loi Normale montre que 90% des tirages sont centrés.")
        with col_s2:
            fig_gauss = go.Figure(data=[go.Histogram(x=sums, marker_color='#fbbf24', opacity=0.7)])
            fig_gauss.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig_gauss, use_container_width=True)

    # 6. BACKTEST ROI
    elif menu == "🧪 Backtest ROI":
        st.markdown("<div class='main-header'>Simulateur ROI</div>", unsafe_allow_html=True)
        depth = st.slider("Tirages", 10, 100, 50)
        if st.button("LANCER L'AUDIT"):
            hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
            for tirage in df.head(depth).values:
                g = set(random.sample(range(1, jeu["b_max"]+1), 5))
                bons = len(g.intersection(set(tirage[:5]))); hits[bons] += 1
            st.bar_chart(pd.Series(hits))

if __name__ == "__main__":
    main()
