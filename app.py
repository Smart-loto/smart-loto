# ============================================================
# SMART-LOTO — VERSION 9.6 — ULTRA-STABLE EDITION
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Smart-Loto V9.6 Pro", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 2.5rem; font-weight: 800; color: #1e293b; text-align: center; margin-bottom: 2rem; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    .draw-container { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 8px; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #f1f5f9; }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; }
    .divider { width: 2px; height: 30px; background: #e2e8f0; margin: 0 8px; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "emoji": "⭐", "boules_max": 50, "nb_boules": 5, "etoiles_max": 12, "nb_etoiles": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "emoji": "🎱", "boules_max": 49, "nb_boules": 5, "etoiles_max": 10, "nb_etoiles": 1, "prix": 2.20, "proba": 1/19068840}
}

# --- ENGINE ---
def neural_velocity_engine(df, max_val, is_stars=False):
    engine_stats = {}
    cols = [c for c in df.columns if ("etoile" if is_stars else "boule") in c]
    if not cols: return {n: {"velocity": 0, "weight": 0.1, "trend": "⚖️"} for n in range(1, max_val + 1)}
    
    f1, f2 = (5, 15) if is_stars else (10, 30)
    for n in range(1, max_val + 1):
        presence = df.apply(lambda r: 1 if n in r[cols].values else 0, axis=1).tolist()
        v1, v2 = sum(presence[:f1])/max(1,f1), sum(presence[:f2])/max(1,f2)
        acc = v1 / (v2 + 0.01)
        engine_stats[n] = {"velocity": round(v1*100, 1), "weight": max(0.01, v1 * acc), "trend": "🔥" if acc > 1.2 else ("🧊" if acc < 0.8 else "⚖️")}
    return engine_stats

@st.cache_data
def load_data(jid, uploaded_file):
    jeu = JEUX[jid]
    if uploaded_file is not None:
        try:
            df_raw = pd.read_csv(uploaded_file, sep=';', decimal=',', engine='python')
            df_raw.columns = [c.strip().lower() for c in df_raw.columns]
            
            # Recherche flexible des colonnes
            b_cols = [c for c in df_raw.columns if any(x in c for x in ["boule", "n1", "n2", "n3", "n4", "n5"])]
            e_cols = [c for c in df_raw.columns if any(x in c for x in ["etoile", "chance", "e1", "e2"])]
            
            df = pd.DataFrame()
            for i in range(min(5, len(b_cols))): df[f"boule_{i+1}"] = pd.to_numeric(df_raw[b_cols[i]], errors='coerce')
            for i in range(min(jeu["nb_etoiles"], len(e_cols))): df[f"etoile_{i+1}"] = pd.to_numeric(df_raw[e_cols[i]], errors='coerce')
            
            df = df.dropna().reset_index(drop=True)
            if df.empty: return generate_sim(jeu)
            return df
        except:
            return generate_sim(jeu)
    return generate_sim(jeu)

def generate_sim(jeu):
    data = []
    for _ in range(200):
        b = sorted(random.sample(range(1, jeu["boules_max"]+1), 5))
        e = sorted(random.sample(range(1, jeu["etoiles_max"]+1), jeu["nb_etoiles"]))
        row = {f"boule_{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_etoiles"]): row[f"etoile_{j+1}"] = e[j]
        data.append(row)
    return pd.DataFrame(data)

# --- MAIN ---
def main():
    # 1. SIDEBAR TOUJOURS VISIBLE
    st.sidebar.markdown("### 🧬 SMART-LOTO V9.6")
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]['nom'])
    jeu = JEUX[jid]
    
    up = st.sidebar.file_uploader("📥 CSV FDJ", type="csv")
    
    # Menu placé avant le chargement des données pour garantir sa visibilité
    menu = st.sidebar.radio("MENU", ["Dashboard", "Neural Stats", "Générateur PRO", "Kelly & Bankroll"])
    
    # 2. CHARGEMENT DES DONNÉES
    df = load_data(jid, up)
    
    try:
        stats_b = neural_velocity_engine(df, jeu["boules_max"])
        stats_e = neural_velocity_engine(df, jeu["etoiles_max"], is_stars=True)
    except:
        st.error("Erreur de calcul des statistiques. Utilisation de données temporaires.")
        stats_b = {n: {"velocity": 0, "weight": 1, "trend": "⚖️"} for n in range(1, jeu["boules_max"]+1)}
        stats_e = {n: {"velocity": 0, "weight": 1, "trend": "⚖️"} for n in range(1, jeu["etoiles_max"]+1)}

    # 3. PAGES
    if menu == "Dashboard":
        st.markdown(f"<div class='main-header'>Analyse {jeu['nom']}</div>", unsafe_allow_html=True)
        
        st.subheader("📊 Vélocité Neuronale : Boules")
        nums = list(stats_b.keys())
        vels = [s["velocity"] for s in stats_b.values()]
        fig_line_b = go.Figure()
        fig_line_b.add_trace(go.Scatter(x=nums, y=vels, mode='lines+markers', line=dict(color='#1e40af')))
        fig_line_b.update_layout(height=250, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig_line_b, use_container_width=True)
        st.plotly_chart(go.Figure(data=go.Heatmap(z=[vels], x=nums, colorscale="RdYlGn_r", showscale=False)).update_layout(height=80, margin=dict(l=0,r=0,b=0,t=0)), use_container_width=True)

        st.subheader("⭐ Vélocité Neuronale : Étoiles")
        e_nums = list(stats_e.keys())
        e_vels = [s["velocity"] for s in stats_e.values()]
        fig_line_e = go.Figure().add_trace(go.Scatter(x=[f"E{n}" for n in e_nums], y=e_vels, mode='lines+markers', line=dict(color='#d97706')))
        fig_line_e.update_layout(height=200, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig_line_e, use_container_width=True)
        st.plotly_chart(go.Figure(data=go.Heatmap(z=[e_vels], x=[f"E{n}" for n in e_nums], colorscale="YlOrRd", showscale=False)).update_layout(height=80, margin=dict(l=0,r=0,b=0,t=0)), use_container_width=True)

    elif menu == "Neural Stats":
        st.markdown("<h2 style='text-align:center;'>🧠 Neural Stats</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Boules", "Étoiles"])
        with t1: st.dataframe(pd.DataFrame([{"N°": n, "Vélocité": f"{s['velocity']}%", "Tendance": s["trend"]} for n, s in stats_b.items()]), use_container_width=True, hide_index=True)
        with t2: st.dataframe(pd.DataFrame([{"Étoile": n, "Vélocité": f"{s['velocity']}%", "Tendance": s["trend"]} for n, s in stats_e.items()]), use_container_width=True, hide_index=True)

    elif menu == "Générateur PRO":
        st.markdown("<h2 style='text-align:center;'>🎯 Générateur PRO</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 3])
        with c1:
            strategy = st.radio("Stratégie", ["Neural Engine", "Sabermetric", "Équilibré"])
            nb_grids = st.slider("Grilles", 1, 10, 3)
            btn = st.button("🚀 CALCULER", use_container_width=True, type="primary")
        with c2:
            if btn:
                for i in range(nb_grids):
                    nums = list(range(1, jeu["boules_max"] + 1))
                    b_weights = [stats_b[n]["weight"] for n in nums]
                    grille = sorted(np.random.choice(nums, 5, replace=False, p=np.array(b_weights)/sum(b_weights)))
                    
                    e_nums = list(range(1, jeu["etoiles_max"] + 1))
                    e_weights = [stats_e[n]["weight"] for n in e_nums]
                    etoiles = sorted(np.random.choice(e_nums, jeu["nb_etoiles"], replace=False, p=np.array(e_weights)/sum(e_weights)))
                    
                    st.markdown(f'<div class="result-card"><div class="draw-container">{"".join([f'<div class="boule">{b}</div>' for b in grille])}<div class="divider"></div>{"".join([f'<div class="etoile">{e}</div>' for e in etoiles])}</div></div>', unsafe_allow_html=True)

    elif menu == "Kelly & Bankroll":
        st.markdown("<h2 style='text-align:center;'>💰 Kelly</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        br = c1.number_input("Budget (€)", 10, 10000, 100)
        jk = c2.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        f = ((jk/jeu["prix"]) * jeu["proba"] - (1-jeu["proba"])) / (jk/jeu["prix"])
        st.metric("Conseil de mise", f"{max(0, f * br):.2f} €")

if __name__ == "__main__":
    main()
