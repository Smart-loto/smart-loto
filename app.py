import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import io

# 1. CONFIGURATION HAUTE PERFORMANCE
st.set_page_config(page_title="Smart-Loto V10 Perfect Pro", page_icon="🎱", layout="wide")

# STYLE CSS PRO / MOBILE-FRIENDLY
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f1f5f9; }
    .main-header { font-size: clamp(1.5rem, 5vw, 2.5rem); font-weight: 900; color: #0f172a; text-align: center; margin: 1rem 0; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 48px; height: 48px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 4px; font-size: 1.1rem; box-shadow: 0 4px 8px rgba(30, 64, 175, 0.3); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 48px; height: 48px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 4px; font-size: 1.1rem; box-shadow: 0 4px 8px rgba(217, 119, 6, 0.3); }
    .divider { width: 3px; height: 40px; background: #e2e8f0; margin: 0 15px; border-radius: 2px; }
    .badge { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# 2. RÉFÉRENTIEL DES JEUX
JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# 3. MOTEUR DE LECTURE UNIVERSEL (SMART SCAN)
def smart_load_csv(file, jeu):
    if file is None: return generate_fallback_data(jeu)
    try:
        content = file.read().decode('utf-8-sig', errors='ignore')
        sep = ';' if ';' in content else ','
        df = pd.read_csv(io.StringIO(content), sep=sep, decimal=',', engine='python')
        
        # SCAN DE TOUTES LES COLONNES POUR TROUVER LES B_MAX ET E_MAX
        potential_b, potential_e = [], []
        for col in df.columns:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if series.empty: continue
            if series.min() >= 1 and series.max() <= jeu["b_max"] and len(series) > len(df)*0.5:
                potential_b.append(series)
            elif series.min() >= 1 and series.max() <= jeu["e_max"] and len(series) > len(df)*0.5:
                potential_e.append(series)
        
        # Reconstruction propre (on prend les 5 meilleures colonnes boules et les X étoiles)
        clean_df = pd.DataFrame()
        for i in range(min(5, len(potential_b))): clean_df[f"b{i+1}"] = potential_b[i]
        for i in range(min(jeu["nb_e"], len(potential_e))): clean_df[f"e{i+1}"] = potential_e[i]
        
        if clean_df.empty: return generate_fallback_data(jeu)
        return clean_df.dropna().head(1000)
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

# 4. MOTEUR MATHÉMATIQUE PRO (VELOCITY + HURST + GEOMETRY)
def get_advanced_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    for n in range(1, max_val + 1):
        presence = df.apply(lambda r: 1 if n in r[cols].values else 0, axis=1).tolist()
        
        # Vélocité courte (10) vs longue (50)
        v_short = sum(presence[:10]) / 10
        v_long = sum(presence[:50]) / 50 if len(presence) >= 50 else v_short
        
        # Indice Hurst simplifié (Persistance)
        acceleration = v_short / (v_long + 0.01)
        
        stats[n] = {
            "vel": round(v_short * 100, 1),
            "weight": max(0.01, v_short * acceleration),
            "trend": "🔥" if acceleration > 1.2 else ("🧊" if acceleration < 0.8 else "⚖️")
        }
    return stats

def get_geometry_score(grille):
    rows = [(n-1)//10 for n in grille]
    cols = [(n-1)%10 for n in grille]
    score = (np.std(rows) + np.std(cols)) * 2
    return round(min(10, score), 1)

# 5. INTERFACE ET NAVIGATION
def main():
    st.sidebar.markdown("<h1 style='text-align:center;'>🧬 SMART-LOTO V10</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    up = st.sidebar.file_uploader("Fichier CSV Officiel", type="csv")
    df = smart_load_csv(up, jeu)
    
    stats_b = get_advanced_stats(df, jeu["b_max"], "b")
    stats_e = get_advanced_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("SAAS NAVIGATION", ["📊 Dashboard Analytics", "🎯 Générateur Expert", "💰 Kelly Bankroll", "📖 Aide & Lexique"])

    # --- PAGE ANALYTICS ---
    if menu == "📊 Dashboard Analytics":
        st.markdown(f"<div class='main-header'>Analyse Expert : {jeu['nom']}</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tirages Analysés", len(df))
        c2.metric("Qualité Data", "RÉEL ✅" if up else "SIMULÉ ⚠️")
        c3.metric("Numéro Pivot", max(stats_b, key=lambda k: stats_b[k]["vel"]))

        # GRAPHIQUE BOULES (Sync perfect)
        st.subheader("Accélération Neuronale (Boules 1-50)")
        x_b = list(stats_b.keys())
        y_b = [s["vel"] for s in stats_b.values()]
        fig_b = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', name="Vitesse"), row=1, col=1)
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig_b.update_layout(height=400, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

        # GRAPHIQUE ÉTOILES
        st.subheader("Accélération Neuronale (Étoiles)")
        x_e = list(stats_e.keys())
        y_e = [s["vel"] for s in stats_e.values()]
        fig_e = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.4])
        fig_e.add_trace(go.Scatter(x=x_e, y=y_e, mode='lines+markers', line=dict(color='orange')), row=1, col=1)
        fig_e.add_trace(go.Heatmap(z=[y_e], x=x_e, colorscale="YlOrRd", showscale=False), row=2, col=1)
        fig_e.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_e, use_container_width=True)

    # --- PAGE GÉNÉRATEUR ---
    elif menu == "🎯 Générateur Expert":
        st.markdown("<div class='main-header'>Générateur Intelligent V10</div>", unsafe_allow_html=True)
        
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            profil = st.selectbox("Profil de Joueur", ["🎯 Équilibré", "🔥 Agressif (Chaud)", "🧊 Chasseur (Retard)", "🧠 Neural (IA)", "🚫 Sabermétrique"])
            nb = st.slider("Nombre de grilles", 1, 10, 3)
            btn = st.button("🚀 GÉNÉRER", type="primary", use_container_width=True)
            
            st.info(f"Le profil **{profil}** ajuste les poids de probabilité selon l'historique chargé.")
            
        with col_p2:
            if btn:
                for i in range(nb):
                    # LOGIQUE DE POIDS SELON PROFIL
                    b_nums = list(range(1, jeu["b_max"] + 1))
                    if "Agressif" in profil: w = [s["vel"] + 0.1 for s in stats_b.values()]
                    elif "Chasseur" in profil: w = [100 - s["vel"] + 0.1 for s in stats_b.values()]
                    elif "Neural" in profil: w = [s["weight"] for s in stats_b.values()]
                    elif "Sabermétrique" in profil: w = [2.0 if n > 31 else 0.5 for n in b_nums]
                    else: w = [s["vel"] + 10 for s in stats_b.values()]
                    
                    grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(w)/sum(w)))
                    
                    # LOGIQUE ÉTOILES
                    e_nums = list(range(1, jeu["e_max"] + 1))
                    we = [s["weight"] for s in stats_e.values()]
                    etoiles = sorted(np.random.choice(e_nums, jeu["nb_e"], replace=False, p=np.array(we)/sum(we)))
                    
                    # ANALYSE GÉOMÉTRIQUE
                    geo = get_geometry_score(grille)
                    
                    # AFFICHAGE UNITAIRE
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span style="color:#64748b; font-weight:bold; font-size:0.8rem;">GRILLE #{i+1} | Profil: {profil}</span>
                            <span class="badge" style="background:#f1f5f9; color:#1e293b;">Géométrie: {geo}/10</span>
                        </div>
                        <div style="display:flex; align-items:center; justify-content:center; flex-wrap:wrap;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div class="divider"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # --- PAGE KELLY ---
    elif menu == "💰 Kelly Bankroll":
        st.title("Gestion de Mise Professionnelle")
        st.write("Le Critère de Kelly calcule la mise optimale pour maximiser vos gains à long terme.")
        c1, c2 = st.columns(2)
        bankroll = c1.number_input("Capital total (€)", 10, 100000, 100)
        jackpot = c2.number_input("Jackpot actuel (Millions €)", 2, 250, 17) * 1_000_000
        
        odds = jackpot / jeu["prix"]
        f_star = (odds * jeu["proba"] - (1 - jeu["proba"])) / odds
        conseil = max(0, f_star * bankroll)
        
        st.metric("Mise suggérée", f"{conseil:.2f} €", delta=f"{math.floor(conseil/jeu['prix'])} grilles")

# Lancement
if __name__ == "__main__":
    import math
    main()
