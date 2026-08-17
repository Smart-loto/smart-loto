# ============================================================
# SMART-LOTO — VERSION 9.4 — LISIBILITÉ & PRÉCISION PRO
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
import plotly.express as px
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Smart-Loto V9.4 Pro", page_icon="🧬", layout="wide")

# --- CSS (Épuré et Pro) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 2.5rem; font-weight: 800; color: #1e293b; text-align: center; margin-bottom: 2rem; }
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    .draw-container { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 8px; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #f1f5f9; }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; box-shadow: 0 3px 5px rgba(30, 64, 175, 0.2); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; box-shadow: 0 3px 5px rgba(217, 119, 6, 0.2); }
    .divider { width: 2px; height: 30px; background: #e2e8f0; margin: 0 8px; }
    .metric-label { font-size: 0.75rem; font-weight: 600; color: #64748b; margin-bottom: 0.3rem; text-transform: uppercase; }
    .metric-value { font-size: 0.95rem; font-weight: 700; color: #1e293b; }
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
    f1, f2 = (5, 15) if is_stars else (10, 30)
    for n in range(1, max_val + 1):
        presence = df.apply(lambda r: 1 if n in r[cols].values else 0, axis=1).tolist()
        v1, v2 = sum(presence[:f1])/f1, sum(presence[:f2])/f2
        acc = v1 / (v2 + 0.01)
        engine_stats[n] = {
            "velocity": round(v1*100, 1), 
            "weight": max(0.01, v1 * acc),
            "trend": "🔥" if acc > 1.2 else ("🧊" if acc < 0.8 else "⚖️")
        }
    return engine_stats

@st.cache_data
def load_data(jid, uploaded_file):
    jeu = JEUX[jid]
    if uploaded_file:
        try:
            df_raw = pd.read_csv(uploaded_file, sep=';', decimal=',', engine='python')
            df_raw.columns = [c.strip().lower() for c in df_raw.columns]
            b_cols = [c for c in df_raw.columns if "boule" in c or "n" in c][:5]
            e_cols = [c for c in df_raw.columns if "etoile" in c or "numéro chance" in c][:jeu["nb_etoiles"]]
            df = pd.DataFrame()
            for i, c in enumerate(b_cols): df[f"boule_{i+1}"] = pd.to_numeric(df_raw[c], errors='coerce')
            for i, col in enumerate(e_cols): df[f"etoile_{i+1}"] = pd.to_numeric(df_raw[col], errors='coerce')
            df = df.dropna().reset_index(drop=True)
        except: df = generate_sim(jeu)
    else: df = generate_sim(jeu)
    return df

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
    st.sidebar.markdown("### 🧬 SMART-LOTO V9.4")
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]['nom'])
    jeu = JEUX[jid]
    
    up = st.sidebar.file_uploader("📥 CSV FDJ", type="csv")
    df = load_data(jid, up)
    
    stats_b = neural_velocity_engine(df, jeu["boules_max"])
    stats_e = neural_velocity_engine(df, jeu["etoiles_max"], is_stars=True)
    
    menu = st.sidebar.radio("MENU", ["Dashboard", "Neural Engine (Stats)", "Générateur PRO", "Kelly & Bankroll"])

    if menu == "Dashboard":
        st.markdown(f"<div class='main-header'>Analyse {jeu['nom']}</div>", unsafe_allow_html=True)
        
        st.subheader("🔥 Heatmap de Vélocité : Boules")
        z_b = [[stats_b[n]["velocity"] for n in stats_b]]
        fig_b = go.Figure(data=go.Heatmap(z=z_b, x=list(stats_b.keys()), colorscale="RdYlGn_r"))
        fig_b.update_layout(height=180, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig_b, use_container_width=True)
        
        st.subheader("⭐ Heatmap de Vélocité : Étoiles")
        z_e = [[stats_e[n]["velocity"] for n in stats_e]]
        fig_e = go.Figure(data=go.Heatmap(z=z_e, x=[f"E{n}" for n in stats_e.keys()], colorscale="YlOrRd"))
        fig_e.update_layout(height=150, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig_e, use_container_width=True)

    elif menu == "Neural Engine (Stats)":
        st.markdown(f"<h2 style='text-align:center;'>🧠 Neural Engine Projection</h2>", unsafe_allow_html=True)
        st.write("Analyse détaillée de l'accélération des sorties. Plus le poids IA est élevé, plus le numéro est en phase émergente.")
        
        col_t1, col_t2 = st.tabs(["📊 Stats Boules", "⭐ Stats Étoiles"])
        
        with col_t1:
            df_b = pd.DataFrame([{"N°": n, "Vélocité": f"{s['velocity']}%", "Tendance": s["trend"], "Poids IA": round(s["weight"], 4)} 
                                 for n, s in stats_b.items()]).sort_values("Poids IA", ascending=False)
            st.dataframe(df_b, use_container_width=True, hide_index=True)
            
        with col_t2:
            df_e = pd.DataFrame([{"Étoile": n, "Vélocité": f"{s['velocity']}%", "Tendance": s["trend"], "Poids IA": round(s["weight"], 4)} 
                                 for n, s in stats_e.items()]).sort_values("Poids IA", ascending=False)
            st.dataframe(df_e, use_container_width=True, hide_index=True)

    elif menu == "Générateur PRO":
        st.markdown(f"<h2 style='text-align:center;'>🎯 Générateur PRO</h2>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 3])
        with c1:
            strategy = st.radio("Stratégie", ["Neural Engine", "Sabermetric", "Équilibré"])
            nb_grids = st.slider("Grilles à générer", 1, 10, 3)
            generate = st.button("🚀 CALCULER", use_container_width=True, type="primary")
            
        with c2:
            if generate:
                nums = list(range(1, jeu["boules_max"] + 1))
                if strategy == "Neural Engine": b_weights = [stats_b[n]["weight"] for n in nums]
                elif strategy == "Sabermetric": b_weights = [1.5 if n > 31 else 0.5 for n in nums]
                else: b_weights = [stats_b[n]["velocity"] + 1 for n in nums]
                
                e_nums = list(range(1, jeu["etoiles_max"] + 1))
                e_weights = [stats_e[n]["weight"] for n in e_nums]
                
                for i in range(nb_grids):
                    grille = sorted(np.random.choice(nums, 5, replace=False, p=np.array(b_weights)/sum(b_weights)))
                    etoiles = sorted(np.random.choice(e_nums, jeu["nb_etoiles"], replace=False, p=np.array(e_weights)/sum(e_weights)))
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="font-weight:800; color:#94a3b8; font-size:0.7rem; margin-bottom:0.8rem;">PROJECTION #{i+1}</div>
                        <div class="draw-container">
                            {"".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div class="divider"></div>
                            {"".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    elif menu == "Kelly & Bankroll":
        st.markdown("<h2 style='text-align:center;'>💰 Gestion Kelly</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        bankroll = col1.number_input("Budget (€)", 10, 10000, 100)
        jackpot = col2.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        f = ((jackpot/jeu["prix"]) * jeu["proba"] - (1-jeu["proba"])) / (jackpot/jeu["prix"])
        st.metric("Conseil de mise", f"{max(0, f * bankroll):.2f} €")

if __name__ == "__main__":
    main()
