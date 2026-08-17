import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Smart-Loto V9.9", page_icon="🧬", layout="wide")

# STYLE CSS POUR LES BOULES ET LES GRILLES
st.markdown("""
<style>
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 42px; height: 42px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 0.9rem; }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 42px; height: 42px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 0.9rem; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .divider { width: 2px; height: 30px; background: #cbd5e1; margin: 0 12px; }
</style>
""", unsafe_allow_html=True)

# CONFIGURATION DES JEUX
JEUX = {
    "euromillions": {"nom": "Euromillions", "nb_b": 5, "max_b": 50, "nb_e": 2, "max_e": 12, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "nb_b": 5, "max_b": 49, "nb_e": 1, "max_e": 10, "prix": 2.20, "proba": 1/19068840}
}

# --- FONCTION DE SIMULATION (SI PAS DE FICHIER) ---
def get_simulated_data(jeu):
    data = []
    for _ in range(100):
        b = sorted(random.sample(range(1, jeu["max_b"]+1), 5))
        e = sorted(random.sample(range(1, jeu["max_e"]+1), jeu["nb_e"]))
        d = {f"b{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_e"]): d[f"e{j+1}"] = e[j]
        data.append(d)
    return pd.DataFrame(data)

# --- CHARGEMENT DU CSV (BLINDÉ) ---
def load_data(file, jeu):
    if file is None: return get_simulated_data(jeu)
    try:
        # On essaye de lire avec point-virgule (Standard FDJ)
        content = file.read().decode('utf-8-sig', errors='ignore')
        sep = ';' if ';' in content else ','
        df = pd.read_csv(io.StringIO(content), sep=sep, decimal=',', engine='python')
        
        # On extrait uniquement les colonnes qui contiennent des nombres
        df_num = df.select_dtypes(include=[np.number])
        if len(df_num.columns) < 5: return get_simulated_data(jeu)
        
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = df_num.iloc[:, i]
        for i in range(jeu["nb_e"]):
            if len(df_num.columns) > 5 + i:
                clean[f"e{i+1}"] = df_num.iloc[:, 5+i]
        return clean.dropna().head(500)
    except:
        return get_simulated_data(jeu)

# --- CALCUL DES STATISTIQUES ---
def get_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    for n in range(1, max_val + 1):
        # Présence sur les 25 derniers tirages
        pres = df.head(25).apply(lambda r: 1 if n in r[cols].values else 0, axis=1).tolist()
        v = sum(pres) / len(pres) if pres else 0
        stats[n] = {"vel": round(v*100, 1), "w": max(0.01, v)}
    return stats

# --- APPLICATION PRINCIPALE ---
def main():
    st.sidebar.title("🧬 SMART-LOTO V9.9")
    
    # Correction du bug AttributeError ici
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    up = st.sidebar.file_uploader("Fichier CSV FDJ", type="csv")
    df = load_data(up, jeu)
    
    stats_b = get_stats(df, jeu["max_b"], "b")
    stats_e = get_stats(df, jeu["max_e"], "e")
    
    menu = st.sidebar.radio("MENU", ["Analyse Graphique", "Générateur PRO"])

    if menu == "Analyse Graphique":
        st.title(f"Tableau de Bord : {jeu['nom']}")
        
        # --- GRAPH BOULES ---
        st.subheader("Vélocité Neuronale (Boules)")
        x_b = list(stats_b.keys())
        y_b = [s["vel"] for s in stats_b.values()]
        
        fig_b = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', name="Accélération"), row=1, col=1)
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig_b.update_layout(height=400, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

        # --- GRAPH ÉTOILES ---
        st.subheader("Vélocité Neuronale (Étoiles)")
        x_e = [f"E{n}" for n in stats_e.keys()]
        y_e = [s["vel"] for s in stats_e.values()]
        
        fig_e = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.6, 0.4])
        fig_e.add_trace(go.Scatter(x=x_e, y=y_e, mode='lines+markers', line=dict(color='orange')), row=1, col=1)
        fig_e.add_trace(go.Heatmap(z=[y_e], x=x_e, colorscale="YlOrRd", showscale=False), row=2, col=1)
        fig_e.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_e, use_container_width=True)

    elif menu == "Générateur PRO":
        st.title("🎯 Générateur Intelligent")
        nb = st.slider("Nombre de grilles", 1, 10, 3)
        
        if st.button("🚀 GÉNÉRER MAINTENANT", type="primary", use_container_width=True):
            for i in range(nb):
                # Tirage Boules
                b_nums = list(range(1, jeu["max_b"] + 1))
                b_w = [stats_b[n]["w"] for n in b_nums]
                grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(b_w)/sum(b_w)))
                
                # Tirage Étoiles
                e_nums = list(range(1, jeu["max_e"] + 1))
                e_w = [stats_e[n]["w"] for n in e_nums]
                etoiles = sorted(np.random.choice(e_nums, jeu["nb_e"], replace=False, p=np.array(e_w)/sum(e_w)))
                
                # AFFICHAGE UNITAIRE
                st.markdown(f"""
                <div class="result-card">
                    <div style="font-size:0.7rem; color:gray; margin-bottom:5px;">GRILLE PROJETÉE #{i+1}</div>
                    <div style="display:flex; align-items:center; justify-content:center;">
                        {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                        <div class="divider"></div>
                        {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
