import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import io
import math

# 1. CONFIGURATION INTERFACE PRO
st.set_page_config(page_title="Smart-Loto V11 Infinity Pro", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    .main-header { font-size: clamp(1.8rem, 5vw, 2.8rem); font-weight: 900; color: #1e293b; text-align: center; padding: 1.5rem 0; background: white; border-bottom: 1px solid #e2e8f0; margin-bottom: 2rem; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1.1rem; box-shadow: 0 4px 8px rgba(30, 64, 175, 0.3); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1.1rem; box-shadow: 0 4px 8px rgba(217, 119, 6, 0.3); }
    .divider { width: 2px; height: 35px; background: #e2e8f0; margin: 0 12px; }
    .stat-box { background: #fff; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 12px; text-align: center; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# 2. MOTEUR DE LECTURE INFINITY (LECTURE INTÉGRALE SANS BRIDAGE)
def infinity_load_csv(file, jeu):
    if file is None: return generate_fallback_data(jeu)
    try:
        # Lecture complète
        df = pd.read_csv(file, sep=';', decimal=',', engine='python', on_bad_lines='skip')
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Identification intelligente et séquentielle des colonnes
        # On cherche des colonnes numériques. Les boules et étoiles sont généralement côte à côte.
        valid_cols = []
        for col in df.columns:
            series = pd.to_numeric(df[col], errors='coerce')
            if series.notna().sum() > len(df) * 0.5: # Si la colonne est remplie à + de 50%
                if series.min() >= 1 and series.max() <= jeu["b_max"]:
                    valid_cols.append(col)
        
        # Sur un fichier FDJ, on attend 5 boules + nb_e étoiles = total_expected
        total_expected = jeu["nb_b"] + jeu["nb_e"]
        
        # On prend les 'total_expected' dernières colonnes valides qui se suivent
        # Souvent les fichiers FDJ ont des colonnes techniques avant les résultats.
        target_cols = valid_cols[-total_expected:] if len(valid_cols) >= total_expected else valid_cols
        
        clean_df = pd.DataFrame()
        # Les 5 premières sont les boules
        for i in range(min(5, len(target_cols))):
            clean_df[f"b{i+1}"] = pd.to_numeric(df[target_cols[i]], errors='coerce')
        # Les suivantes sont les étoiles
        for i in range(jeu["nb_e"]):
            idx = 5 + i
            if len(target_cols) > idx:
                clean_df[f"e{i+1}"] = pd.to_numeric(df[target_cols[idx]], errors='coerce')
            else:
                # Sécurité si les étoiles manquent dans le CSV
                clean_df[f"e{i+1}"] = np.random.randint(1, jeu["e_max"] + 1, size=len(df))

        return clean_df.dropna().reset_index(drop=True)
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
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

# 3. CALCULS STATS PRO
def get_pro_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols: return {n: {"vel": 0, "w": 0.1, "trend": "⚖️"} for n in range(1, max_val+1)}
    
    for n in range(1, max_val + 1):
        # On calcule sur TOUTE la longueur du DF pour la vélocité
        presence = df.apply(lambda r: 1 if n in r[cols].values else 0, axis=1).tolist()
        
        # Vélocité courte (20) vs Historique Total
        v_recent = sum(presence[:20]) / 20
        v_total = sum(presence) / len(presence)
        
        accel = v_recent / (v_total + 0.001)
        
        stats[n] = {
            "vel": round(v_recent * 100, 1),
            "w": max(0.01, v_recent * accel),
            "trend": "🔥" if accel > 1.3 else ("🧊" if accel < 0.7 else "⚖️")
        }
    return stats

# 4. INTERFACE
def main():
    st.sidebar.markdown("<h1 style='text-align:center;'>🎱 SMART-LOTO V11</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    up = st.sidebar.file_uploader("Archive CSV (Intégrale)", type="csv")
    df = infinity_load_csv(up, jeu)
    
    stats_b = get_pro_stats(df, jeu["b_max"], "b")
    stats_e = get_pro_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION", ["📊 Dashboard Analytics", "🎯 Générateur Expert", "💰 Kelly Bankroll", "📖 Aide"])

    if menu == "📊 Dashboard Analytics":
        st.markdown(f"<div class='main-header'>Analyse Infinity : {jeu['nom']}</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='stat-box'><small>TIRAGES ANALYSÉS</small><br><b>{len(df)}</b></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='stat-box'><small>MODE DE LECTURE</small><br><b>{'RÉEL ✅' if up else 'SIMULÉ ⚠️'}</b></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='stat-box'><small>BOULE LA PLUS CHAUDE</small><br><b>{max(stats_b, key=lambda k: stats_b[k]['vel'])}</b></div>", unsafe_allow_html=True)

        # GRAPH BOULES
        st.subheader("Accélération Neuronale (Boules 1-50)")
        x_b = list(stats_b.keys())
        y_b = [s["vel"] for s in stats_b.values()]
        fig_b = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', name="Vitesse"), row=1, col=1)
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig_b.update_layout(height=400, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

        # GRAPH ÉTOILES
        st.subheader("Accélération Neuronale (Étoiles)")
        x_e = list(stats_e.keys())
        y_e = [s["vel"] for s in stats_e.values()]
        fig_e = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.4])
        fig_e.add_trace(go.Scatter(x=x_e, y=y_e, mode='lines+markers', line=dict(color='orange')), row=1, col=1)
        fig_e.add_trace(go.Heatmap(z=[y_e], x=x_e, colorscale="YlOrRd", showscale=False), row=2, col=1)
        fig_e.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_e, use_container_width=True)

    elif menu == "🎯 Générateur Expert":
        st.markdown("<div class='main-header'>Générateur Haute Précision V11</div>", unsafe_allow_html=True)
        
        c_p1, c_p2 = st.columns([1, 3])
        with c_p1:
            profil = st.selectbox("Stratégie", ["🎯 Équilibré", "🔥 Agressif", "🧊 Chasseur", "🧠 Neural Engine", "🚫 Sabermétrique"])
            nb = st.slider("Grilles", 1, 10, 3)
            btn = st.button("🚀 GÉNÉRER", type="primary", use_container_width=True)
        
        with c_p2:
            if btn:
                for i in range(nb):
                    # Calcul des poids
                    b_nums = list(range(1, jeu["b_max"] + 1))
                    if "Agressif" in profil: w = [s["vel"] + 0.1 for s in stats_b.values()]
                    elif "Chasseur" in profil: w = [100 - s["vel"] + 0.1 for s in stats_b.values()]
                    elif "Neural" in profil: w = [s["w"] for s in stats_b.values()]
                    elif "Sabermétrique" in profil: w = [2.0 if n > 31 else 0.5 for n in b_nums]
                    else: w = [s["vel"] + 10 for s in stats_b.values()]
                    
                    grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(w)/sum(w)))
                    
                    e_nums = list(range(1, jeu["e_max"] + 1))
                    we = [s["w"] for s in stats_e.values()]
                    etoiles = sorted(np.random.choice(e_nums, jeu["nb_e"], replace=False, p=np.array(we)/sum(we)))
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="font-size:0.7rem; color:#94a3b8; font-weight:bold; margin-bottom:8px;">COMBINAISON #{i+1} | {profil}</div>
                        <div style="display:flex; align-items:center; justify-content:center; flex-wrap:wrap;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div class="divider"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    elif menu == "💰 Kelly Bankroll":
        st.title("Gestion Kelly & ROI")
        c1, c2 = st.columns(2)
        br = c1.number_input("Capital (€)", 10, 10000, 100)
        jk = c2.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        f_star = ((jk/jeu["prix"]) * jeu["proba"] - (1 - jeu["proba"])) / (jk/jeu["prix"])
        st.metric("Mise Conseillée", f"{max(0, f_star * br):.2f} €", delta=f"{math.floor(max(0, f_star * br)/jeu['prix'])} grilles")

if __name__ == "__main__":
    main()
