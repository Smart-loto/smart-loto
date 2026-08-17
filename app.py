# ============================================================
# SMART-LOTO — VERSION 7.0.1 — SCIENTIFIC EDITION (FIX CSV)
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Smart-Loto V7 Pro", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: clamp(1.8rem, 5vw, 3rem); font-weight: 800; background: linear-gradient(135deg, #1e40af, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 20px 0; }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 55px; height: 55px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.3rem; font-weight: bold; margin: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 55px; height: 55px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.3rem; font-weight: bold; margin: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "emoji": "⭐", "boules_max": 50, "nb_boules": 5, "etoiles_max": 12, "nb_etoiles": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "emoji": "🎱", "boules_max": 49, "nb_boules": 5, "etoiles_max": 10, "nb_etoiles": 1, "prix": 2.20, "proba": 1/19068840}
}

# --- FONCTIONS SCIENTIFIQUES ---
def calc_hurst(series):
    if len(series) < 30: return 0.5
    series = np.array(series)
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(series[lag:], series[:-lag]))) for lag in lags]
    return np.polyfit(np.log(lags), np.log(tau), 1)[0] * 2.0

def get_cooccurrence_matrix(df, max_b):
    matrix = np.zeros((max_b, max_b))
    cols = [c for c in df.columns if "boule" in c]
    for _, row in df.iterrows():
        nums = [int(row[c]) for c in cols if pd.notnull(row[c])]
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                b1, b2 = int(nums[i]-1), int(nums[j]-1)
                if 0 <= b1 < max_b and 0 <= b2 < max_b:
                    matrix[b1][b2] += 1
                    matrix[b2][b1] += 1
    return matrix

# --- CHARGEUR DE DONNÉES (CORRIGÉ POUR FDJ) ---
@st.cache_data
def load_data(jid, uploaded_file):
    jeu = JEUX[jid]
    if uploaded_file is not None:
        try:
            # Lecture avec séparateurs spécifiques FDJ (Point-virgule et Virgule décimale)
            raw_df = pd.read_csv(uploaded_file, sep=';', decimal=',', engine='python', encoding='utf-8')
            
            # Nettoyage des noms de colonnes (suppression des espaces)
            raw_df.columns = [c.strip().lower() for c in raw_df.columns]
            
            # Recherche des colonnes de boules (ex: boule_1 ou n1)
            b_cols = []
            for i in range(1, 6):
                for pattern in [f'boule_{i}', f'n{i}', f'boule {i}']:
                    if pattern in raw_df.columns:
                        b_cols.append(pattern)
                        break
            
            # Recherche des colonnes d'étoiles
            e_cols = []
            for i in range(1, jeu["nb_etoiles"] + 1):
                for pattern in [f'etoile_{i}', f'e{i}', f'etoile {i}', f'numéro chance']:
                    if pattern in raw_df.columns:
                        e_cols.append(pattern)
                        break

            # Reconstruction du DataFrame propre
            df = pd.DataFrame()
            for i, col in enumerate(b_cols): df[f"boule_{i+1}"] = pd.to_numeric(raw_df[col], errors='coerce')
            for i, col in enumerate(e_cols): df[f"etoile_{i+1}"] = pd.to_numeric(raw_df[col], errors='coerce')
            
            df = df.dropna().reset_index(drop=True)
            if len(df) == 0: raise ValueError("Aucune donnée valide détectée.")
            
        except Exception as e:
            st.error(f"Erreur d'import : {str(e)}")
            df = generate_sim(jeu)
    else:
        df = generate_sim(jeu)

    # Calcul Stats
    stats = {"boules": {}, "matrix": get_cooccurrence_matrix(df, jeu["boules_max"])}
    b_cols = [c for c in df.columns if "boule" in c]
    
    for n in range(1, jeu["boules_max"] + 1):
        presence = df.apply(lambda r: 1 if n in r[b_cols].values else 0, axis=1).tolist()
        last_idx = next((i for i, x in enumerate(presence) if x == 1), len(df))
        stats["boules"][n] = {
            "chaleur": sum(presence[:20]) * 5,
            "ecart": last_idx,
            "hurst": calc_hurst(np.cumsum(presence))
        }
    return df, stats

def generate_sim(jeu):
    data = []
    for _ in range(200):
        b = sorted(random.sample(range(1, jeu["boules_max"]+1), 5))
        e = sorted(random.sample(range(1, jeu["etoiles_max"]+1), jeu["nb_etoiles"]))
        row = {f"boule_{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_etoiles"]): row[f"etoile_{j+1}"] = e[j]
        data.append(row)
    return pd.DataFrame(data)

# --- APP ---
def main():
    st.sidebar.title("🧬 Smart-Loto V7")
    jid = st.sidebar.selectbox("Jeu", list(JEUX.keys()), format_func=lambda x: JEUX[x]['nom'])
    jeu = JEUX[jid]
    
    # Zone d'upload
    up = st.sidebar.file_uploader("Importer CSV FDJ (Archive complète)", type="csv")
    if up: st.sidebar.success("Fichier détecté !")
    
    df, stats = load_data(jid, up)
    
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Générateur PRO", "Clusters", "Budget"])

    if menu == "Dashboard":
        st.markdown(f"<div class='main-header'>{jeu['nom']} - Science</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tirages", len(df))
        c2.metric("Source", "Fichier Réel" if up else "Simulation")
        c3.metric("Numéro le + chaud", max(stats["boules"], key=lambda k: stats["boules"][k]["chaleur"]))
        
        st.subheader("🔥 Température des numéros")
        fig = px.bar(x=list(stats["boules"].keys()), y=[s["chaleur"] for s in stats["boules"].values()], labels={'x':'Numéro', 'y':'Chaleur'})
        st.plotly_chart(fig, use_container_width=True)

    elif menu == "Générateur PRO":
        st.markdown("<div class='main-header'>🎯 Calculateur PRO</div>", unsafe_allow_html=True)
        
        if st.button("GÉNÉRER COMBINAISON OPTIMISÉE", type="primary", use_container_width=True):
            # Algorithme de sélection pondérée
            nums = list(range(1, jeu["boules_max"] + 1))
            w = [ (stats["boules"][n]["chaleur"] + 1) * stats["boules"][n]["hurst"] for n in nums ]
            grille = sorted(random.choices(nums, weights=w, k=5))
            etoiles = sorted(random.sample(range(1, jeu["etoiles_max"]+1), jeu["nb_etoiles"]))
            
            # Affichage
            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
            for b in grille: st.markdown(f"<div class='boule'>{b}</div>", unsafe_allow_html=True)
            st.markdown("<div style='display:inline-block; width:20px;'></div>", unsafe_allow_html=True)
            for e in etoiles: st.markdown(f"<div class='etoile'>{e}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Radar
            from __main__ import calc_shannon_entropy
            ent = calc_shannon_entropy(grille, jeu["boules_max"]) / 2.5
            heat = np.mean([stats["boules"][n]["chaleur"] for n in grille]) / 100
            
            fig = go.Figure(data=go.Scatterpolar(r=[heat, ent, 0.8, 0.5, heat], theta=['Chaleur','Entropie','Invisibilité','Retard','Chaleur'], fill='toself'))
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "Clusters":
        st.subheader("🔗 Corrélations entre numéros")
        fig = px.imshow(stats["matrix"], color_continuous_scale="Viridis")
        st.plotly_chart(fig, use_container_width=True)

    elif menu == "Budget":
        st.subheader("💰 Gestion de Bankroll (Kelly)")
        br = st.number_input("Bankroll (€)", 10, 1000, 100)
        jackpot = st.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        
        odds = jackpot / jeu["prix"]
        f = (odds * jeu["proba"] - (1-jeu["proba"])) / odds
        mise = max(0, f * br)
        st.metric("Mise suggérée", f"{mise:.2f} €")

def calc_shannon_entropy(gr, max_val):
    g = sorted(list(gr))
    gaps = [g[0]] + [g[i] - g[i-1] for i in range(1, len(g))] + [(max_val + 1) - g[-1]]
    total = sum(gaps)
    return -sum((gap/total) * np.log2(gap/total) for gap in gaps if gap > 0)

if __name__ == "__main__":
    main()
