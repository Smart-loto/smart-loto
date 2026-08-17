import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import math
from itertools import combinations

# 1. CONFIGURATION INTERFACE PRO
st.set_page_config(page_title="Smart-Loto V15 Pro", page_icon="🧬", layout="wide")

# CSS PREMIUM SÉCURISÉ
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    .main-header { font-size: 2.5rem; font-weight: 900; color: #1e293b; text-align: center; padding: 1.5rem 0; background: white; border-bottom: 1px solid #e2e8f0; margin-bottom: 2rem; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1rem; box-shadow: 0 4px 8px rgba(30, 64, 175, 0.3); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1rem; box-shadow: 0 4px 8px rgba(217, 119, 6, 0.3); }
    .divider { width: 2px; height: 40px; background: #e2e8f0; margin: 0 15px; }
    .metric-title { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 900; }
    .metric-value { font-size: 1rem; font-weight: 800; color: #1e293b; }
    .mini-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; background: #f1f5f9; padding: 4px; border-radius: 4px; width: 110px; }
    .mini-cell { width: 9px; height: 9px; background: #cbd5e1; border-radius: 1px; }
    .mini-cell.active { background: #7c3aed; }
</style>
""", unsafe_allow_html=True)

# 2. RÉFÉRENTIELS
JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# 3. MOTEURS DE CALCUL (VECTORISÉS)
def calc_entropy(grille, b_max):
    g = sorted(list(grille))
    gaps = [g[0]] + [g[i] - g[i-1] for i in range(1, len(g))] + [(b_max + 1) - g[-1]]
    total = sum(gaps)
    return -sum((gap/total) * np.log2(gap/total) for gap in gaps if gap > 0)

def get_geometry(grille):
    rows = [(n-1)//10 for n in grille]
    cols = [(n-1)%10 for n in grille]
    return round(min(10, (np.std(rows) + np.std(cols)) * 2.2), 1)

# 4. DATA ENGINE (INFINITY LOADER)
@st.cache_data
def load_data_pro(file_content, jid):
    jeu = JEUX[jid]
    if file_content is None: return generate_fallback(jeu)
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Identification intelligente des colonnes numériques
        valid_cols = []
        for col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if not s.empty and s.min() >= 1 and s.max() <= jeu["b_max"] and len(s) > len(df)*0.4:
                valid_cols.append(col)
        
        # On prend les colonnes de fin (souvent les résultats FDJ)
        target = valid_cols[-(jeu["nb_b"] + jeu["nb_e"]):]
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[target[i]], errors='coerce')
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[target[5+i]], errors='coerce')
        return clean.dropna().reset_index(drop=True)
    except:
        return generate_fallback(jeu)

def generate_fallback(jeu):
    data = []
    for _ in range(200):
        b = sorted(random.sample(range(1, jeu["b_max"]+1), 5))
        e = sorted(random.sample(range(1, jeu["e_max"]+1), jeu["nb_e"]))
        d = {f"b{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_e"]): d[f"e{j+1}"] = e[j]
        data.append(d)
    return pd.DataFrame(data)

# 5. ANALYTICS ENGINE
@st.cache_data
def get_stats_pro(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    matrix = df[cols].values
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        v_rec = np.mean(pres[:25]) if len(pres) >= 25 else np.mean(pres)
        v_tot = np.mean(pres)
        accel = v_rec / (v_tot + 0.001)
        stats[n] = {"vel": round(v_rec*100,1), "w": max(0.01, v_rec*accel)}
    return stats

def get_cooccurrence(df, b_max):
    matrix = np.zeros((b_max, b_max))
    cols = [c for c in df.columns if c.startswith("b")]
    for _, row in df.iterrows():
        nums = [int(x) for x in row[cols].values if not np.isnan(x)]
        for combo in combinations(sorted(nums), 2):
            matrix[combo[0]-1, combo[1]-1] += 1
            matrix[combo[1]-1, combo[0]-1] += 1
    return matrix

# 6. APPLICATION
def main():
    st.sidebar.markdown("<h1 style='text-align:center;'>🧬 SMART-LOTO V15</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("Archive CSV", type="csv")
    content = file.getvalue() if file else None
    
    df = load_data_pro(content, jid)
    stats_b = get_stats_pro(df, jeu["b_max"], "b")
    stats_e = get_stats_pro(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard", "🎯 Générateur Expert", "🔗 Clusters & Paires", "💰 Kelly Bankroll"])

    # --- PAGE DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Dashboard Analytics : {jeu['nom']}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tirages Analysés", len(df))
        c2.metric("Source", "RÉEL ✅" if file else "SIMULÉ ⚠️")
        c3.metric("Boule Pivot", max(stats_b, key=lambda k: stats_b[k]["vel"]))

        # Graphiques Subplots
        for title, stats, max_v, color in [("Boules", stats_b, jeu["b_max"], "#1e40af"), ("Étoiles", stats_e, jeu["e_max"], "#d97706")]:
            st.subheader(f"Vélocité Neuronale : {title}")
            x = list(stats.keys())
            y = [s["vel"] for s in stats.values()]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color=color)), row=1, col=1)
            fig.add_trace(go.Heatmap(z=[y], x=x, colorscale="RdYlGn_r" if title=="Boules" else "YlOrRd", showscale=False), row=2, col=1)
            fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # --- PAGE GÉNÉRATEUR ---
    elif menu == "🎯 Générateur Expert":
        st.markdown(f"<div class='main-header'>Générateur Haute Précision</div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            profil = st.selectbox("Stratégie IA", ["🎯 Équilibré", "🧠 Neural Engine", "🚫 Sabermétrique", "🧊 Chasseur (Retard)"])
            nb = st.slider("Nombre de grilles", 1, 10, 3)
            btn = st.button("🚀 GÉNÉRER", type="primary", use_container_width=True)
            
        with col2:
            if btn:
                for i in range(nb):
                    b_nums = list(range(1, jeu["b_max"] + 1))
                    if profil == "🧠 Neural Engine": w = [s["w"] for s in stats_b.values()]
                    elif profil == "🚫 Sabermétrique": w = [2.0 if n > 31 else 0.5 for n in b_nums]
                    elif profil == "🧊 Chasseur (Retard)": w = [100 - s["vel"] + 0.1 for s in stats_b.values()]
                    else: w = [s["vel"] + 10 for s in stats_b.values()]
                    
                    grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(w)/sum(w)))
                    etoiles = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False))
                    
                    # Audits
                    ent, geo, sab = calc_entropy(grille, jeu["b_max"]), get_geometry(grille), sum(1 for n in grille if n <= 31)
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display:flex; align-items:center; justify-content:center; flex-wrap:wrap; margin-bottom:20px;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div class="divider"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; border-top:1px solid #f1f5f9; padding-top:15px;">
                            <div><div class="metric-title">Géométrie</div><div class="metric-value">{geo}/10</div><div class="mini-grid">{" ".join([f'<div class="mini-cell {"active" if n in grille else ""}"></div>' for n in range(1, jeu["b_max"]+1)])}</div></div>
                            <div><div class="metric-title">Sabermétrie</div><div class="metric-value">{sab} dates</div><div style="height:4px; background:#e2e8f0; margin-top:5px;"><div style="width:{sab*20}%; height:100%; background:{'#ef4444' if sab >= 4 else '#10b981'};"></div></div></div>
                            <div><div class="metric-title">Entropie</div><div class="metric-value">{ent:.2f}</div></div>
                            <div><div class="metric-title">Confiance IA</div><div class="metric-value">{int(np.mean([stats_b[n]["vel"] for n in grille]))}%</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # --- PAGE CLUSTERS ---
    elif menu == "🔗 Clusters & Paires":
        st.markdown(f"<div class='main-header'>Affinités & Corrélations</div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔥 Matrice d'Affinité", "👯 Top Paires"])
        with tab1:
            matrix = get_cooccurrence(df, jeu["b_max"])
            fig = go.Figure(data=go.Heatmap(z=matrix, colorscale="Inferno"))
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        with tab2:
            paires = []
            for i in range(len(matrix)):
                for j in range(i+1, len(matrix)):
                    if matrix[i,j] > 0: paires.append(((i+1, j+1), int(matrix[i,j])))
            paires = sorted(paires, key=lambda x: x[1], reverse=True)[:15]
            for p, v in paires:
                st.write(f"🤝 Duo **{p[0]} + {p[1]}** : sorti **{v}** fois ensemble.")

    # --- PAGE KELLY ---
    elif menu == "💰 Kelly Bankroll":
        st.title("Gestion de Mise Kelly")
        br = st.number_input("Bankroll (€)", 10, 10000, 100)
        jk = st.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        f_star = ((jk/jeu["prix"]) * jeu["proba"] - (1 - jeu["proba"])) / (jk/jeu["prix"])
        st.metric("Mise Conseillée", f"{max(0, f_star * br):.2f} €")

if __name__ == "__main__":
    main()
