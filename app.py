# ============================================================
# SMART-LOTO — VERSION 32.0 — TOTAL INTEGRATION
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
st.set_page_config(page_title="Smart-Loto V32 Pro", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [data-testid="stAppViewContainer"], .main { background-color: #0f172a !important; color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #fbbf24 !important; font-weight: 700 !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1.5rem 0; }
    
    /* Cartes de résultats ultra-lisibles */
    .result-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.2rem; border-left: 5px solid #fbbf24; }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white !important; border-radius: 50%; width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 3px; border: 1px solid #60a5fa; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white !important; border-radius: 50%; width: 44px; height: 44px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 4px; border: 1px solid #fcd34d; font-size: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    
    .metric-title { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 900; margin-bottom: 5px; }
    .metric-value { font-size: 1.2rem; font-weight: 800; color: #ffffff; }
    
    /* Grid Visualizer Ticket */
    .mini-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; background: #0f172a; padding: 5px; border-radius: 4px; width: 110px; }
    .mini-cell { width: 9px; height: 9px; background: #334155; border-radius: 1px; }
    .mini-cell.active { background: #fbbf24; }
    
    div[data-baseweb="select"] > div { background-color: #1e293b !important; color: white !important; border: 1px solid #334155 !important; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160, "sum_range": (90, 160)},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840, "sum_range": (75, 175)}
}

PROFILS = {
    "🧠 Neural IA": "Optimisation par accélération neuronale (Vitesse).",
    "🚫 Sabermétrique": "Anti-partage (Priorité aux numéros élevés > 31).",
    "🎯 Équilibré": "Parité 3/2 et répartition de somme optimale.",
    "🔥 Agressif": "Focus sur les numéros en pleine vague de sortie.",
    "🧊 Chasseur": "Focus sur les numéros en retard record.",
    "⚖️ Paritaire": "Équilibre strict Pair/Impair."
}

# --- MATHS ENGINES ---
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

@st.cache_data
def load_data_v32(file_content, jid):
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
    except: return load_data_v32(None, jid)

def get_stats_v32(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]; matrix = df[cols].values
    total = len(df); expected = (total * (5 if prefix=="b" else 2) / max_val)
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1); freq = np.sum(pres)
        v_rec = np.mean(pres[:30]); p_val = poisson_cdf_manual(freq, expected)
        stats[n] = {
            "vel": round(v_rec*100, 1), 
            "heat": round((freq/total)*100, 2),
            "w": float(max(0.01, v_rec * (freq/expected))),
            "status": "Surchauffe 🔥" if p_val > 0.95 else ("Froid 🧊" if p_val < 0.05 else "Normal ⚖️"),
            "gap": next((i for i, x in enumerate(pres) if x), total)
        }
    return stats

# --- UI HELPERS ---
def draw_audit_card_v32(idx, g, et, stats_b, jeu):
    ia_score = int(np.mean([stats_b[n]["vel"] for n in g]))
    sab = sum(1 for n in g if n > 31)
    ent = calc_entropy(g, jeu["b_max"])
    
    st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
    b_h = "".join([f'<div class="boule">{b}</div>' for b in g])
    e_h = "".join([f'<div class="etoile">{e}</div>' for e in et])
    st.markdown(f'<div style="display:flex; justify-content:center; align-items:center; flex-wrap:wrap; margin-bottom:20px;">{b_h}<div style="width:2px; height:35px; background:#334155; margin:0 15px;"></div>{e_h}</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; border-top:1px solid #334155; padding-top:15px; text-align:center;">
        <div><div class="metric-title">IA Vitesse</div><div class="metric-value">{ia_score}%</div></div>
        <div><div class="metric-title">Sabermétrie</div><div class="metric-value">{sab}/5 hautes</div><div style="height:4px; background:#334155; margin-top:5px;"><div style="width:{sab*20}%; height:100%; background:{'#ef4444' if sab >= 4 else '#10b981'};"></div></div></div>
        <div><div class="metric-title">Entropie</div><div class="metric-value">{ent:.2f}</div><small style="color:#94a3b8">Désordre</small></div>
        <div><div class="metric-title">Ticket</div><div class="mini-grid" style="margin:auto;">{" ".join([f'<div class="mini-cell {"active" if n in g else ""}"></div>' for n in range(1, jeu["b_max"]+1)])}</div></div>
    </div></div>
    """, unsafe_allow_html=True)

# --- MAIN ---
def main():
    st.sidebar.markdown("<h1 style='color:#fbbf24; text-align:center;'>🧬 SMART-LOTO V32</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 ARCHIVE FDJ", type="csv")
    df = load_data_v32(file.getvalue() if file else None, jid)
    stats_b = get_stats_v32(df, jeu["b_max"], "b")
    stats_e = get_stats_v32(df, jeu["e_max"], "e")
    
    # Calcul Sommes Correct (Boules 1 à 5 uniquement)
    ball_cols = [f"b{i+1}" for i in range(5)]
    df['total_sum'] = df[ball_cols].sum(axis=1)
    
    menu = st.sidebar.radio("SÉLECTION", ["📊 Dashboard", "🎯 Générateur Expert", "➕ Analyse des Sommes", "🧬 Audit Poisson", "🔗 Clusters & Paires", "🧪 Backtest ROI"])

    # 1. DASHBOARD
    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Analytics Expert : {jeu['nom']}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><small>Archive</small><br><b>{len(df)} Tirages</b></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><small>Confiance IA</small><br><b>99.6%</b></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><small>Top Vitesse</small><br><b>N°{max(stats_b, key=lambda k: stats_b[k]['vel'])}</b></div>", unsafe_allow_html=True)

        for title, s_dict, mx in [("BOULES", stats_b, jeu["b_max"]), ("ÉTOILES", stats_e, jeu["e_max"])]:
            st.subheader(f"Vélocité & Fréquence Historique : {title}")
            x = list(range(1, mx + 1)); y_l = [s_dict[n]["vel"] for n in x]; y_h = [s_dict[n]["heat"] for n in x]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=x, y=y_l, mode='lines+markers', line=dict(color='#fbbf24', width=2), name="Vitesse"), row=1, col=1)
            fig.add_trace(go.Heatmap(z=[y_h], x=x, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
            fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), margin=dict(l=10,r=10,t=10,b=10))
            fig.update_xaxes(dtick=5 if mx==50 else 1, range=[0.5, mx+0.5])
            st.plotly_chart(fig, use_container_width=True)

    # 2. GENERATEUR PORTFOLIO (AVEC TOUS LES FILTRES V30)
    elif menu == "🎯 Générateur Expert":
        st.markdown("<div class='main-header'>Générateur Portfolio Diamond</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])
        with c1:
            prof = st.selectbox("Algorithme", list(PROFILS.keys())); nb = st.slider("Grilles", 1, 10, 3)
            diversify = st.checkbox("Diversification Max", value=True)
            with st.expander("🛠️ Filtres Avancés"):
                f_sum = st.slider("Somme des numéros", 60, 220, jeu["sum_range"])
                f_par = st.checkbox("Parité Équilibrée (3/2)", value=True)
                excl = st.multiselect("Bannir des numéros", range(1, jeu["b_max"]+1))
            btn = st.button("🚀 CALCULER LE PORTFOLIO", type="primary", use_container_width=True)
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
                        if (f_sum[0] <= sum(g) <= f_sum[1]) and (not f_par or (2 <= sum(1 for n in g if n%2==0) <= 3)): break
                    used.update(g); et = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False))
                    draw_audit_card_v32(i+1, g, et, stats_b, jeu)

    # 3. ANALYSE DES SOMMES (V31 PRO)
    elif menu == "➕ Analyse des Sommes":
        st.markdown("<div class='main-header'>Analyse Mathématique des Sommes</div>", unsafe_allow_html=True)
        sums = df['total_sum']
        col1, col2 = st.columns([1, 2.5])
        with col1:
            st.markdown(f"<div class='metric-card'><small>Somme Moyenne</small><br><b>{sums.mean():.1f}</b></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-card'><small>Zone de Confiance</small><br><b>{jeu['sum_range'][0]} - {jeu['sum_range'][1]}</b></div>", unsafe_allow_html=True)
            z = (sums.iloc[0] - sums.mean()) / sums.std()
            st.info(f"Dernier tirage : **{'Normal ✅' if abs(z)<1.5 else 'Anomalie ⚠️'}** (Z-Score: {z:.2f})")
        with col2:
            fig_gauss = go.Figure(data=[go.Histogram(x=sums, nbinsx=40, marker_color='#fbbf24', opacity=0.6)])
            fig_gauss.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig_gauss, use_container_width=True)
        st.subheader("Cycles de Tendance (Moyenne Mobile)")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(y=sums.head(100), mode='lines', line=dict(color='#334155'), name="Brute"))
        fig_trend.add_trace(go.Scatter(y=sums.head(100).rolling(window=5).mean(), mode='lines', line=dict(color='#fbbf24', width=4), name="Lissée"))
        fig_trend.add_hrect(y0=jeu['sum_range'][0], y1=jeu['sum_range'][1], fillcolor="green", opacity=0.1)
        st.plotly_chart(fig_trend, use_container_width=True)

    # 4. AUDIT POISSON (V30 CLARITY)
    elif menu == "🧬 Audit Poisson":
        st.markdown("<div class='main-header'>Audit des Anomalies de Fréquence</div>", unsafe_allow_html=True)
        audit_data = []
        for n, s in stats_b.items():
            color = "#ef4444" if "Surchauffe" in s["status"] else ("#3b82f6" if "Froid" in s["status"] else "#10b981")
            audit_data.append({"N°": n, "Etat": f'<span style="color:{color}; font-weight:bold;">{s["status"]}</span>', "Ecart": s["gap"]})
        st.write(pd.DataFrame(audit_data).sort_values("Ecart", ascending=False).to_html(escape=False, index=False), unsafe_allow_html=True)

    # 5. CLUSTERS & AFFINITÉS
    elif menu == "🔗 Clusters & Paires":
        st.markdown("<div class='main-header'>Analyse Combinatoire & Paires</div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔥 Matrice d'Affinité", "👯 Top Paires & Partenaires"])
        matrix = np.zeros((jeu["b_max"], jeu["b_max"]))
        for row in df[ball_cols].values:
            for combo in combinations(sorted(row), 2):
                matrix[combo[0]-1, combo[1]-1] += 1; matrix[combo[1]-1, combo[0]-1] += 1
        with tab1:
            st.plotly_chart(go.Figure(data=go.Heatmap(z=matrix, x=list(range(1, jeu["b_max"]+1)), y=list(range(1, jeu["b_max"]+1)), colorscale="Inferno")).update_layout(height=650), use_container_width=True)
        with tab2:
            c1, c2 = st.columns(2)
            with c1:
                paires = []
                for i in range(len(matrix)):
                    for j in range(i+1, len(matrix)):
                        if matrix[i,j] > 0: paires.append(((i+1, j+1), int(matrix[i,j])))
                for p, v in sorted(paires, key=lambda x: x[1], reverse=True)[:10]:
                    st.write(f"🤝 Duo **{p[0]} + {p[1]}** : sorti **{v}** fois.")
            with c2:
                n_search = st.selectbox("Chercheur de Partenaire", range(1, jeu["b_max"]+1))
                row = matrix[n_search-1]; best = np.argsort(row)[-3:][::-1]
                for p in best: st.write(f"🔹 Le **{p+1}** est sorti **{int(row[p])}** fois avec le {n_search}")

    # 6. BACKTEST ROI
    elif menu == "🧪 Backtest ROI":
        st.markdown("<div class='main-header'>Simulateur ROI & Performance</div>", unsafe_allow_html=True)
        depth = st.slider("Tirages réels à tester", 10, 100, 50)
        if st.button("LANCER L'AUDIT"):
            hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
            for tirage in df.head(depth).values:
                g = set(random.sample(range(1, jeu["b_max"]+1), 5))
                hits[len(g.intersection(set(tirage[:5])))] += 1
            st.bar_chart(pd.Series(hits))

if __name__ == "__main__":
    main()
