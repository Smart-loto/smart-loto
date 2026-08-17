import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
import io

# 1. INITIALISATION IMMÉDIATE
st.set_page_config(page_title="Smart-Loto V9.7", page_icon="🧬", layout="wide")

# STYLE CSS MINIMALISTE ET ROBUSTE
st.markdown("""
<style>
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 45px; height: 45px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 5px; }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 45px; height: 45px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 5px; }
    .result-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; margin-bottom: 10px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# CONFIGURATION DES JEUX
JEUX = {
    "euromillions": {"nb_b": 5, "max_b": 50, "nb_e": 2, "max_e": 12, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nb_b": 5, "max_b": 49, "nb_e": 1, "max_e": 10, "prix": 2.20, "proba": 1/19068840}
}

# --- FONCTIONS DE SECOURS (SIMULATION) ---
def get_simulated_data(jeu):
    data = []
    for _ in range(100):
        b = sorted(random.sample(range(1, jeu["max_b"]+1), 5))
        e = sorted(random.sample(range(1, jeu["max_e"]+1), jeu["nb_e"]))
        row = {f"b{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_e"]): row[f"e{j+1}"] = e[j]
        data.append(row)
    return pd.DataFrame(data)

# --- CHARGEMENT ROBUSTE ---
def robust_load(uploaded_file, jeu):
    if uploaded_file is None: return get_simulated_data(jeu)
    try:
        # Test de lecture avec séparateur point-virgule (FDJ Standard)
        df = pd.read_csv(uploaded_file, sep=';', decimal=',', engine='python', on_bad_lines='skip')
        
        # On ne garde que les colonnes qui contiennent des chiffres
        df_numeric = df.select_dtypes(include=[np.number])
        
        # On essaye d'extraire les 5 premières colonnes pour les boules
        clean_df = pd.DataFrame()
        cols = df_numeric.columns
        
        # Extraction Boules
        for i in range(min(5, len(cols))):
            clean_df[f"b{i+1}"] = df_numeric[cols[i]]
            
        # Extraction Étoiles (après les 5 boules)
        for i in range(jeu["nb_e"]):
            if len(cols) > 5 + i:
                clean_df[f"e{i+1}"] = df_numeric[cols[5+i]]
            else:
                clean_df[f"e{i+1}"] = random.randint(1, jeu["max_e"])
        
        return clean_df.dropna().head(500)
    except:
        st.sidebar.warning("Fichier illisible. Mode simulation activé.")
        return get_simulated_data(jeu)

# --- CALCULS STATISTIQUES ---
def get_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    for n in range(1, max_val + 1):
        # Présence sur les 20 derniers tirages
        pres = df.head(20).apply(lambda r: 1 if n in r[cols].values else 0, axis=1).sum()
        stats[n] = {"vel": pres * 5, "weight": max(0.1, pres / 20.0)}
    return stats

# --- APPLICATION PRINCIPALE ---
def main():
    st.sidebar.title("🧬 SMART-LOTO V9.7")
    
    selected_jeu = st.sidebar.selectbox("JEU", ["euromillions", "loto"])
    jeu = JEUX[selected_jeu]
    
    file = st.sidebar.file_uploader("Fichier CSV FDJ", type="csv")
    
    # CHARGEMENT ET CALCULS
    df = robust_load(file, jeu)
    stats_b = get_stats(df, jeu["max_b"], "b")
    stats_e = get_stats(df, jeu["max_e"], "e")
    
    menu = st.sidebar.radio("MENU", ["Dashboard", "Générateur PRO"])

    if menu == "Dashboard":
        st.title(f"Analyse {selected_jeu.capitalize()}")
        
        # GRAPHIQUE BOULES
        st.subheader("Vélocité des Boules")
        x_b = list(stats_b.keys())
        y_b = [s["vel"] for s in stats_b.values()]
        
        fig_b = go.Figure()
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', name="Vélocité"))
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, y=["Heat"], colorscale="RdYlGn_r", showscale=False, yaxis="y2"))
        fig_b.update_layout(height=350, yaxis=dict(title="Accélération %"), y2axis=dict(overlaying='y', visible=False))
        st.plotly_chart(fig_b, use_container_width=True)

        # GRAPHIQUE ÉTOILES
        st.subheader("Vélocité des Étoiles")
        x_e = [f"E{n}" for n in stats_e.keys()]
        y_e = [s["vel"] for s in stats_e.values()]
        
        fig_e = go.Figure()
        fig_e.add_trace(go.Scatter(x=x_e, y=y_e, mode='lines+markers', line=dict(color="orange")))
        fig_e.add_trace(go.Heatmap(z=[y_e], x=x_e, y=["Heat"], colorscale="YlOrRd", showscale=False, yaxis="y2"))
        fig_e.update_layout(height=300, y2axis=dict(overlaying='y', visible=False))
        st.plotly_chart(fig_e, use_container_width=True)

    elif menu == "Générateur PRO":
        st.title("🎯 Générateur de Grilles")
        nb = st.slider("Nombre de grilles", 1, 10, 3)
        
        if st.button("🚀 GÉNÉRER", type="primary"):
            for i in range(nb):
                # Tirage Boules pondéré
                b_nums = list(range(1, jeu["max_b"] + 1))
                b_w = [stats_b[n]["weight"] for n in b_nums]
                grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(b_w)/sum(b_w)))
                
                # Tirage Étoiles
                e_nums = list(range(1, jeu["max_e"] + 1))
                e_w = [stats_e[n]["weight"] for n in e_nums]
                etoiles = sorted(np.random.choice(e_nums, jeu["nb_e"], replace=False, p=np.array(e_w)/sum(e_w)))
                
                # AFFICHAGE HORIZONTAL
                st.markdown(f"""
                <div class="result-card">
                    <div style="font-size:0.8rem; color:gray;">GRILLE #{i+1}</div>
                    <div style="display:flex; align-items:center; justify-content:center;">
                        {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                        <div style="width:2px; height:30px; background:#ccc; margin:0 15px;"></div>
                        {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
