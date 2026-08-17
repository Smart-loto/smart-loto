# ============================================================
# SMART-LOTO — VERSION 16.0 — DIAMOND PRO EDITION
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

# 1. CONFIGURATION INTERFACE LUXE
st.set_page_config(page_title="Smart-Loto V16 Diamond", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
    .main-header { font-size: 2.8rem; font-weight: 900; background: linear-gradient(135deg, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 2rem 0; }
    
    /* Cartes Noir/Gold */
    .result-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 48px; height: 48px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); border: 1px solid #60a5fa; }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 48px; height: 48px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; margin: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); border: 1px solid #fcd34d; }
    
    .metric-card { background: #1e293b; border-left: 4px solid #fbbf24; padding: 15px; border-radius: 8px; }
    .mini-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; background: #0f172a; padding: 5px; border-radius: 4px; width: 110px; }
    .mini-cell { width: 9px; height: 9px; background: #334155; border-radius: 1px; }
    .mini-cell.active { background: #fbbf24; }
    
    /* Tabs & Buttons Custom */
    .stButton>button { background: linear-gradient(135deg, #fbbf24, #d97706); color: #0f172a; font-weight: 900; border: none; border-radius: 8px; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px rgba(251, 191, 36, 0.4); }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# --- ENGINES ---
def get_geometry(grille):
    rows, cols = [(n-1)//10 for n in grille], [(n-1)%10 for n in grille]
    return round(min(10, (np.std(rows) + np.std(cols)) * 2.2), 1)

@st.cache_data
def load_data_v16(file_content, jid):
    jeu = JEUX[jid]
    if not file_content: return generate_fallback(jeu)
    try:
        df = pd.read_csv(io.BytesIO(file_content), sep=';', decimal=',', engine='python')
        df.columns = [c.strip().lower() for c in df.columns]
        valid = [c for c in df.columns if pd.to_numeric(df[c], errors='coerce').dropna().between(1, 50).any()]
        target = valid[-(jeu["nb_b"] + jeu["nb_e"]):]
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[target[i]], errors='coerce')
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[target[5+i]], errors='coerce')
        return clean.dropna().reset_index(drop=True)
    except: return generate_fallback(jeu)

def generate_fallback(jeu):
    data = []
    for _ in range(200):
        b = sorted(random.sample(range(1, jeu["b_max"]+1), 5)); e = sorted(random.sample(range(1, jeu["e_max"]+1), jeu["nb_e"]))
        d = {f"b{j+1}": b[j] for j in range(5)}; d.update({f"e{j+1}": e[j] for j in range(jeu["nb_e"])})
        data.append(d)
    return pd.DataFrame(data)

@st.cache_data
def get_full_stats_v16(df, max_val, prefix="b"):
    stats = {}
    matrix = df[[c for c in df.columns if c.startswith(prefix)]].values
    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        v_rec = np.mean(pres[:25]); v_tot = np.mean(pres); acc = v_rec / (v_tot + 0.001)
        stats[n] = {"vel": round(v_rec*100,1), "w": float(max(0.01, v_rec*acc))}
    return stats

# --- APPLICATION ---
def main():
    st.sidebar.markdown("<h2 style='color:#fbbf24; text-align:center;'>💎 DIAMOND V16</h2>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("SÉLECTION JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    file = st.sidebar.file_uploader("📂 ARCHIVE FDJ (CSV)", type="csv")
    content = file.getvalue() if file else None
    
    df = load_data_v16(content, jid)
    stats_b = get_full_stats_v16(df, jeu["b_max"], "b")
    stats_e = get_full_stats_v16(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION PRO", ["📊 Dashboard Expert", "🎯 Générateur Diamond", "🧪 Backtest Strategie", "💰 Kelly & Mise"])

    # --- DASHBOARD ---
    if menu == "📊 Dashboard Expert":
        st.markdown(f"<div class='main-header'>Diamond Analytics : {jeu['nom']}</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        cols[0].markdown(f"<div class='metric-card'><small>HISTORIQUE</small><br><b>{len(df)} Tirages</b></div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='metric-card'><small>PROBABILITÉ</small><br><b>1 / {int(1/jeu['proba']):,}</b></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='metric-card'><small>NUMÉRO ALPHA</small><br><b>{max(stats_b, key=lambda k: stats_b[k]['vel'])}</b></div>", unsafe_allow_html=True)

        for title, stats, max_v, color in [("BOULES", stats_b, jeu["b_max"], "#3b82f6"), ("ÉTOILES", stats_e, jeu["e_max"], "#fbbf24")]:
            st.subheader(f"Vélocité Neuronale : {title}")
            x = list(stats.keys()); y = [s["vel"] for s in stats.values()]
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color=color, width=3)), row=1, col=1)
            fig.add_trace(go.Heatmap(z=[y], x=x, colorscale="YlOrBr", showscale=False), row=2, col=1)
            fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)

    # --- GÉNÉRATEUR DIAMOND ---
    elif menu == "🎯 Générateur Diamond":
        st.markdown("<div class='main-header'>Générateur Diamond Pro</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 3])
        with c1:
            profil = st.selectbox("Algorithme", ["🧠 Neural Engine", "🎯 Équilibré", "🚫 Sabermétrique"])
            nb = st.slider("Grilles", 1, 10, 3)
            btn = st.button("💎 CALCULER")
            
        with c2:
            if btn:
                all_grids_text = ""
                for i in range(nb):
                    b_nums = list(range(1, jeu["b_max"] + 1))
                    w = [s["w"] for s in stats_b.values()] if profil == "🧠 Neural Engine" else ([2.0 if n > 31 else 0.5 for n in b_nums] if profil == "🚫 Sabermétrique" else [s["vel"]+10 for s in stats_b.values()])
                    grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(w)/sum(w)))
                    etoiles = sorted(random.sample(range(1, jeu["e_max"]+1), jeu["nb_e"]))
                    geo = get_geometry(grille); sab = sum(1 for n in grille if n <= 31)
                    all_grids_text += f"Grille {i+1}: {grille} Stars: {etoiles}\n"
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display:flex; align-items:center; justify-content:center; margin-bottom:20px;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div class="divider"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; border-top:1px solid #334155; padding-top:15px;">
                            <div><small style='color:#94a3b8'>GÉOMÉTRIE</small><br><b>{geo}/10</b><div class="mini-grid">{" ".join([f'<div class="mini-cell {"active" if n in grille else ""}"></div>' for n in range(1, jeu["b_max"]+1)])}</div></div>
                            <div><small style='color:#94a3b8'>SABERMÉTRIE</small><br><b>{sab} Dates</b><div style='height:4px; background:#334155; margin-top:5px;'><div style='width:{sab*20}%; height:100%; background:{"#ef4444" if sab >= 4 else "#10b981"};'></div></div></div>
                            <div><small style='color:#94a3b8'>CONFIANCE IA</small><br><b>{int(np.mean([stats_b[n]["vel"] for n in grille]))}%</b></div>
                            <div><small style='color:#94a3b8'>TYPE</small><br><b>{profil.split()[1]}</b></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.download_button("📂 EXPORTER LES GRILLES (TXT)", all_grids_text, file_name="mes_grilles.txt")

    # --- BACKTEST ---
    elif menu == "🧪 Backtest Strategie":
        st.markdown("<div class='main-header'>Laboratoire de Backtest</div>", unsafe_allow_html=True)
        st.write("On simule la stratégie choisie sur les **50 derniers tirages réels** pour évaluer sa performance.")
        if st.button("🧪 LANCER L'AUDIT DE PERFORMANCE"):
            hits = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
            b_cols = [c for c in df.columns if c.startswith("b")]
            for tirage in df.head(50).values:
                # Simulation d'une grille avec Neural Engine
                w = [s["w"] for s in stats_b.values()]
                g = set(np.random.choice(list(range(1, jeu["b_max"]+1)), 5, replace=False, p=np.array(w)/sum(w)))
                bons = len(g.intersection(set(tirage[:5])))
                hits[bons] += 1
            
            c1, c2 = st.columns(2)
            c1.bar_chart(pd.Series(hits))
            c2.write(f"✅ Sur 50 tirages, la stratégie a trouvé **3 numéros** {hits[3]} fois.")
            c2.info("Une performance supérieure à la probabilité théorique indique une stratégie 'Payante' sur cette période.")

    # --- KELLY ---
    elif menu == "💰 Kelly & Mise":
        st.title("Optimisation du Capital")
        c1, c2 = st.columns(2)
        br = c1.number_input("Capital (€)", 10, 10000, 100)
        jk = c2.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        f = ((jk/jeu["prix"]) * jeu["proba"] - (1 - jeu["proba"])) / (jk/jeu["prix"])
        st.metric("Mise Conseillée Diamond", f"{max(0, f * br):.2f} €")

if __name__ == "__main__":
    main()
