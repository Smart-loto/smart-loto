import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# 1. CONFIGURATION INITIALE
st.set_page_config(page_title="Smart-Loto V12.1 Pro", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    .main-header { font-size: 2.5rem; font-weight: 900; color: #1e293b; text-align: center; padding: 1.5rem 0; background: white; border-bottom: 1px solid #e2e8f0; margin-bottom: 2rem; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1.1rem; box-shadow: 0 4px 8px rgba(30, 64, 175, 0.3); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1.1rem; box-shadow: 0 4px 8px rgba(217, 119, 6, 0.3); }
    .divider { width: 2px; height: 35px; background: #e2e8f0; margin: 0 12px; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# --- FONCTION DE SIMULATION (FALLBACK) ---
def get_simulation(jeu):
    data = []
    for _ in range(200):
        b = sorted(random.sample(range(1, jeu["b_max"]+1), 5))
        e = sorted(random.sample(range(1, jeu["e_max"]+1), jeu["nb_e"]))
        d = {f"b{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_e"]): d[f"e{j+1}"] = e[j]
        data.append(d)
    return pd.DataFrame(data)

# --- CHARGEMENT ROBUSTE SANS CACHE BLOQUANT ---
def load_data_safe(file, jid):
    jeu = JEUX[jid]
    if file is None: return get_simulation(jeu)
    try:
        df = pd.read_csv(file, sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Identification des colonnes numériques par valeurs
        cols_valides = []
        for col in df.columns:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if not series.empty and series.min() >= 1 and series.max() <= jeu["b_max"]:
                cols_valides.append(col)
        
        total_attendus = jeu["nb_b"] + jeu["nb_e"]
        target = cols_valides[-total_attendus:]
        
        if len(target) < total_attendus: return get_simulation(jeu)
        
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[target[i]], errors='coerce')
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[target[5+i]], errors='coerce')
        
        return clean.dropna().reset_index(drop=True)
    except:
        return get_simulation(jeu)

# --- CALCUL STATS VECTORISÉ ---
def get_stats_fast(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols: return {n: {"vel": 0, "w": 0.1} for n in range(1, max_val+1)}
    
    data_matrix = df[cols].values
    for n in range(1, max_val + 1):
        presence = np.any(data_matrix == n, axis=1)
        v_recent = np.mean(presence[:20]) if len(presence) >= 20 else np.mean(presence)
        v_total = np.mean(presence)
        accel = v_recent / (v_total + 0.001)
        stats[n] = {"vel": round(v_recent * 100, 1), "w": float(max(0.01, v_recent * accel))}
    return stats

# --- MAIN APP ---
def main():
    st.sidebar.markdown("<h1 style='text-align:center;'>🧬 SMART-LOTO V12.1</h1>", unsafe_allow_html=True)
    
    jid = st.sidebar.selectbox("CHOIX DU JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 Charger Archive FDJ (CSV)", type="csv")
    
    # CHARGEMENT DES DONNÉES
    df = load_data_safe(file, jid)
    stats_b = get_stats_fast(df, jeu["b_max"], "b")
    stats_e = get_stats_fast(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard Analytics", "🎯 Générateur Expert", "💰 Kelly Bankroll"])

    # 1. PAGE DASHBOARD
    if menu == "📊 Dashboard Analytics":
        st.markdown(f"<div class='main-header'>Analyse Expert : {jeu['nom']}</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tirages en mémoire", len(df))
        c2.metric("Source", "RÉEL ✅" if file else "SIMULATION ⚠️")
        c3.metric("Numéro Pivot", max(stats_b, key=lambda k: stats_b[k]["vel"]))

        # Graphique Boules
        st.subheader("Vitesse Neuronale (Boules)")
        x_b = list(stats_b.keys())
        y_b = [s["vel"] for s in stats_b.values()]
        fig_b = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', name="Vitesse"), row=1, col=1)
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig_b.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

        # Graphique Étoiles
        st.subheader("Vitesse Neuronale (Étoiles)")
        x_e = list(stats_e.keys())
        y_e = [s["vel"] for s in stats_e.values()]
        fig_e = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.4])
        fig_e.add_trace(go.Scatter(x=x_e, y=y_e, mode='lines+markers', line=dict(color='orange')), row=1, col=1)
        fig_e.add_trace(go.Heatmap(z=[y_e], x=x_e, colorscale="YlOrRd", showscale=False), row=2, col=1)
        fig_e.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_e, use_container_width=True)

    # 2. PAGE GÉNÉRATEUR
    elif menu == "🎯 Générateur Expert":
        st.markdown(f"<div class='main-header'>Générateur Intelligent</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 3])
        with c1:
            profil = st.selectbox("Stratégie IA", ["🎯 Équilibré", "🧠 Neural Engine", "🚫 Sabermétrique"])
            nb = st.slider("Nombre de grilles", 1, 10, 3)
            btn = st.button("🚀 GÉNÉRER", type="primary", use_container_width=True)
            
        with c2:
            if btn:
                for i in range(nb):
                    # Boules
                    nums = list(range(1, jeu["b_max"] + 1))
                    if "Neural" in profil: w = [s["w"] for s in stats_b.values()]
                    elif "Sabermétrique" in profil: w = [1.5 if n > 31 else 0.5 for n in nums]
                    else: w = [s["vel"] + 10 for s in stats_b.values()]
                    
                    grille = sorted(np.random.choice(nums, 5, replace=False, p=np.array(w)/sum(w)))
                    
                    # Étoiles
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

    # 3. PAGE KELLY
    elif menu == "💰 Kelly Bankroll":
        st.title("Calculateur de Mise Kelly")
        col1, col2 = st.columns(2)
        br = col1.number_input("Capital (€)", 10, 10000, 100)
        jk = col2.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        # Formule Kelly simplifiée
        odds = jk / jeu["prix"]
        f_star = ((odds * jeu["proba"]) - (1 - jeu["proba"])) / odds
        st.metric("Mise conseillée", f"{max(0, f_star * br):.2f} €")

if __name__ == "__main__":
    main()
