import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import math

# 1. CONFIGURATION INTERFACE
st.set_page_config(page_title="Smart-Loto V12 Turbo", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    .main-header { font-size: 2.5rem; font-weight: 900; color: #1e293b; text-align: center; padding: 1rem 0; background: white; border-bottom: 1px solid #e2e8f0; margin-bottom: 2rem; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1.1rem; }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1.1rem; }
    .divider { width: 2px; height: 35px; background: #e2e8f0; margin: 0 12px; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# 2. CHARGEMENT VECTORISÉ ET CACHÉ
@st.cache_data(show_spinner=False)
def load_data_turbo(file_content, jid):
    jeu = JEUX[jid]
    if file_content is None:
        return generate_fallback_data(jeu)
    
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Identification ultra-rapide des colonnes numériques
        cols_num = df.select_dtypes(include=[np.number]).columns
        valid_cols = []
        for c in cols_num:
            if df[c].dropna().between(1, jeu["b_max"]).all() or df[c].dropna().mean() < jeu["b_max"]:
                valid_cols.append(c)
        
        total_req = jeu["nb_b"] + jeu["nb_e"]
        target = valid_cols[-total_req:]
        
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = df[target[i]]
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = df[target[5+i]]
        
        return clean.dropna().reset_index(drop=True)
    except:
        return generate_fallback_data(jeu)

def generate_fallback_data(jeu):
    data = []
    for _ in range(150):
        b = sorted(random.sample(range(1, jeu["b_max"]+1), 5))
        e = sorted(random.sample(range(1, jeu["e_max"]+1), jeu["nb_e"]))
        d = {f"b{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_e"]): d[f"e{j+1}"] = e[j]
        data.append(d)
    return pd.DataFrame(data)

# 3. CALCUL STATS VECTORISÉ (VITESSE ÉCLAIR)
@st.cache_data(show_spinner=False)
def get_stats_turbo(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    data_matrix = df[cols].values # Passage en NumPy pour la vitesse
    
    for n in range(1, max_val + 1):
        # On vérifie la présence sur toute la matrice d'un coup (Vectorisé)
        presence = np.any(data_matrix == n, axis=1)
        
        v_recent = np.mean(presence[:20]) if len(presence) >= 20 else np.mean(presence)
        v_total = np.mean(presence)
        
        accel = v_recent / (v_total + 0.001)
        
        stats[n] = {
            "vel": round(v_recent * 100, 1),
            "w": float(max(0.01, v_recent * accel)),
            "trend": "🔥" if accel > 1.3 else ("🧊" if accel < 0.7 else "⚖️")
        }
    return stats

# 4. INTERFACE
def main():
    st.sidebar.markdown("<h1 style='text-align:center;'>⚡ SMART-LOTO V12</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("Archive CSV", type="csv")
    
    # On lit le contenu du fichier une seule fois
    file_content = file.getvalue() if file else None
    
    # Calculs optimisés
    df = load_data_turbo(file_content, jid)
    stats_b = get_stats_turbo(df, jeu["b_max"], "b")
    stats_e = get_stats_turbo(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard", "🎯 Générateur", "💰 Kelly"])

    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Dashboard : {jeu['nom']}</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Tirages", len(df))
        col2.metric("Statut", "RÉEL ✅" if file else "SIMULÉ ⚠️")
        col3.metric("Numéro Top", max(stats_b, key=lambda k: stats_b[k]["vel"]))

        # Graphiques Subplots (Stable)
        x_b = list(stats_b.keys())
        y_b = [s["vel"] for s in stats_b.values()]
        fig_b = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', name="Vitesse"), row=1, col=1)
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig_b.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

        x_e = list(stats_e.keys())
        y_e = [s["vel"] for s in stats_e.values()]
        fig_e = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.4])
        fig_e.add_trace(go.Scatter(x=x_e, y=y_e, mode='lines+markers', line=dict(color='orange')), row=1, col=1)
        fig_e.add_trace(go.Heatmap(z=[y_e], x=x_e, colorscale="YlOrRd", showscale=False), row=2, col=1)
        fig_e.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_e, use_container_width=True)

    elif menu == "🎯 Générateur":
        st.markdown(f"<div class='main-header'>Générateur Expert</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 3])
        with c1:
            profil = st.selectbox("Stratégie", ["🎯 Équilibré", "🧠 Neural Engine", "🚫 Sabermétrique"])
            nb = st.slider("Grilles", 1, 10, 3)
            btn = st.button("🚀 CALCULER", type="primary", use_container_width=True)
        
        with c2:
            if btn:
                for i in range(nb):
                    b_nums = list(range(1, jeu["b_max"] + 1))
                    if "Neural" in profil: w = [s["w"] for s in stats_b.values()]
                    elif "Sabermétrique" in profil: w = [2.0 if n > 31 else 0.5 for n in b_nums]
                    else: w = [s["vel"] + 10 for s in stats_b.values()]
                    
                    grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(w)/sum(w)))
                    
                    e_nums = list(range(1, jeu["e_max"] + 1))
                    we = [s["w"] for s in stats_e.values()]
                    etoiles = sorted(np.random.choice(e_nums, jeu["nb_e"], replace=False, p=np.array(we)/sum(we)))
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display:flex; align-items:center; justify-content:center; flex-wrap:wrap;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div class="divider"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    elif menu == "💰 Kelly":
        st.title("Kelly Bankroll")
        br = st.number_input("Capital (€)", 10, 10000, 100)
        jk = st.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        f_star = ((jk/jeu["prix"]) * jeu["proba"] - (1 - jeu["proba"])) / (jk/jeu["prix"])
        st.metric("Mise Conseillée", f"{max(0, f_star * br):.2f} €")

if __name__ == "__main__":
    main()
