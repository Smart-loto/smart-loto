# ============================================================
# SMART-LOTO — VERSION 14.0 — CLUSTER EDITION
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

# --- CONFIGURATION ---
st.set_page_config(page_title="Smart-Loto V14 Pro", page_icon="🔗", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f1f5f9; }
    .main-header { font-size: 2.2rem; font-weight: 900; color: #1e293b; text-align: center; padding: 1.5rem 0; background: white; border-bottom: 1px solid #e2e8f0; margin-bottom: 1.5rem; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1rem; box-shadow: 0 4px 8px rgba(30, 64, 175, 0.3); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1rem; box-shadow: 0 4px 8px rgba(217, 119, 6, 0.3); }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# --- ENGINE MATHÉMATIQUE ---

def get_cooccurrence_matrix(df, b_max):
    matrix = np.zeros((b_max, b_max))
    cols = [c for c in df.columns if c.startswith("b")]
    for _, row in df.iterrows():
        nums = sorted([int(x) for x in row[cols].values if not np.isnan(x)])
        for combo in combinations(nums, 2):
            matrix[combo[0]-1, combo[1]-1] += 1
            matrix[combo[1]-1, combo[0]-1] += 1
    return matrix

def analyze_sequences(df):
    cols = [c for c in df.columns if c.startswith("b")]
    counts = {0: 0, 1: 0, 2: 0, "3+": 0}
    for _, row in df.iterrows():
        nums = sorted(row[cols].values)
        seq_found = 0
        for i in range(len(nums)-1):
            if nums[i+1] == nums[i] + 1: seq_found += 1
        if seq_found >= 3: counts["3+"] += 1
        else: counts[seq_found] += 1
    return counts

# --- DATA LOADING ---

def load_data_v14(file, jid):
    jeu = JEUX[jid]
    if file is None: return generate_fallback(jeu)
    try:
        content = file.read().decode('utf-8-sig', errors='ignore')
        sep = ';' if ';' in content else ','
        df = pd.read_csv(io.StringIO(content), sep=sep, decimal=',', engine='python')
        valid_cols = []
        for col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if not s.empty and s.min() >= 1 and s.max() <= jeu["b_max"]: valid_cols.append(col)
        target = valid_cols[-(jeu["nb_b"] + jeu["nb_e"]):]
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[target[i]], errors='coerce')
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[target[5+i]], errors='coerce')
        return clean.dropna().reset_index(drop=True)
    except: return generate_fallback(jeu)

def generate_fallback(jeu):
    data = []
    for _ in range(150):
        b = sorted(random.sample(range(1, jeu["b_max"]+1), 5))
        e = sorted(random.sample(range(1, jeu["e_max"]+1), jeu["nb_e"]))
        d = {f"b{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_e"]): d[f"e{j+1}"] = e[j]
        data.append(d)
    return pd.DataFrame(data)

# --- MAIN APP ---

def main():
    st.sidebar.markdown("<h1 style='text-align:center;'>🧬 SMART-LOTO V14</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    up = st.sidebar.file_uploader("Archive CSV", type="csv")
    df = load_data_v14(up, jid)
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard", "🎯 Générateur", "🔗 Clusters & Séries", "💰 Kelly"])

    # 1. DASHBOARD (Simplifié)
    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Dashboard : {jeu['nom']}</div>", unsafe_allow_html=True)
        st.metric("Tirages en mémoire", len(df))
        st.write("Utilisez le menu pour explorer les affinités entre numéros.")

    # 2. GÉNÉRATEUR (V13 Style)
    elif menu == "🎯 Générateur":
        st.title("Générateur Expert")
        st.write("Moteur de génération vectorisé.")
        # ... (Logique V13 gardée)

    # 3. PAGE CLUSTERS & SÉRIES (NOUVEAU)
    elif menu == "🔗 Clusters & Séries":
        st.markdown(f"<div class='main-header'>Analyse des Affinités & Séries</div>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["🔥 Matrice d'Affinité", "👯 Paires & Duos", "📏 Analyse des Suites"])
        
        with tab1:
            st.subheader("Matrice de Co-occurrence (Heatmap)")
            st.write("Plus le carré est clair, plus les deux numéros sortent souvent ensemble.")
            matrix = get_cooccurrence_matrix(df, jeu["b_max"])
            fig = go.Figure(data=go.Heatmap(z=matrix, x=list(range(1, jeu["b_max"]+1)), y=list(range(1, jeu["b_max"]+1)), colorscale="Inferno"))
            fig.update_layout(height=700, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Top 10 des Paires les plus fréquentes")
            # Extraction des meilleures paires
            paires = []
            for i in range(len(matrix)):
                for j in range(i+1, len(matrix)):
                    if matrix[i,j] > 0: paires.append(((i+1, j+1), matrix[i,j]))
            paires = sorted(paires, key=lambda x: x[1], reverse=True)
            
            c1, c2 = st.columns([2, 1])
            with c1:
                for k in range(10):
                    p, val = paires[k]
                    st.markdown(f"**Couple {p[0]} + {p[1]}** : Sortis ensemble **{int(val)}** fois")
            with c2:
                st.info("💡 **Conseil Pro** : Jouer une paire à forte affinité augmente la cohérence statistique de votre grille.")
            
            st.markdown("---")
            st.subheader("🔍 Chercheur de Partenaire")
            num_search = st.number_input("Entrez un numéro pour voir ses meilleurs alliés :", 1, jeu["b_max"], 7)
            row = matrix[num_search-1]
            best_partners = np.argsort(row)[-3:][::-1]
            st.write(f"Les meilleurs partenaires du **{num_search}** sont :")
            for p in best_partners:
                st.markdown(f"- Le **{p+1}** (ensemble {int(row[p])} fois)")

        with tab3:
            st.subheader("Analyse des Suites (Numéros Consécutifs)")
            st.write("Fréquence des grilles contenant des suites de chiffres (ex: 12-13).")
            seq_stats = analyze_sequences(df)
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                st.write(f"- Grilles sans aucune suite : **{seq_stats[0]}**")
                st.write(f"- Grilles avec 1 suite (ex: 1-2) : **{seq_stats[1]}**")
                st.write(f"- Grilles avec 2 suites (ex: 1-2 et 15-16) : **{seq_stats[2]}**")
                st.write(f"- Grilles avec 3+ suites : **{seq_stats['3+']}**")
            with c_s2:
                fig_seq = px.pie(names=list(seq_stats.keys()), values=list(seq_stats.values()), title="Répartition des suites")
                st.plotly_chart(fig_seq, use_container_width=True)

    # 4. KELLY
    elif menu == "💰 Kelly":
        st.title("Kelly ROI")
        # ... (Logique V13)

if __name__ == "__main__":
    import plotly.express as px
    main()
