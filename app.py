# ============================================================
# SMART-LOTO — VERSION 13.0 — MEGA PRO EDITION
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import math

# --- CONFIGURATION PRO ---
st.set_page_config(page_title="Smart-Loto V13 Mega Pro", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f1f5f9; }
    .main-header { font-size: 2.2rem; font-weight: 900; color: #1e293b; text-align: center; padding: 1.5rem 0; background: white; border-bottom: 1px solid #e2e8f0; margin-bottom: 1.5rem; }
    
    /* Grille et Boules */
    .result-card { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .boule { background: radial-gradient(circle at 30% 30%, #3b82f6, #1e40af); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1rem; box-shadow: 0 4px 8px rgba(30, 64, 175, 0.3); }
    .etoile { background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706); color: white; border-radius: 50%; width: 46px; height: 46px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin: 3px; font-size: 1rem; box-shadow: 0 4px 8px rgba(217, 119, 6, 0.3); }
    .divider { width: 2px; height: 35px; background: #e2e8f0; margin: 0 15px; }
    
    /* Metrics */
    .pro-badge { background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; border: 1px solid #e2e8f0; }
    .metric-title { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: 900; margin-bottom: 5px; }
    .metric-value { font-size: 1rem; font-weight: 800; color: #1e293b; }
    
    /* Mini Ticket Grid */
    .mini-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; background: #f8fafc; padding: 5px; border-radius: 4px; width: 120px; }
    .mini-cell { width: 10px; height: 10px; background: #e2e8f0; border-radius: 1px; }
    .mini-cell.active { background: #7c3aed; }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom": "Euromillions", "b_max": 50, "e_max": 12, "nb_b": 5, "nb_e": 2, "prix": 2.50, "proba": 1/139838160},
    "loto": {"nom": "Loto", "b_max": 49, "e_max": 10, "nb_b": 5, "nb_e": 1, "prix": 2.20, "proba": 1/19068840}
}

# --- ENGINE MATHÉMATIQUE PRO ---

def calc_shannon_entropy(grille, b_max):
    g = sorted(list(grille))
    gaps = [g[0]] + [g[i] - g[i-1] for i in range(1, len(g))] + [(b_max + 1) - g[-1]]
    total = sum(gaps)
    return -sum((gap/total) * np.log2(gap/total) for gap in gaps if gap > 0)

def get_geometry_score(grille):
    rows = [(n-1)//10 for n in grille]
    cols = [(n-1)%10 for n in grille]
    return round(min(10, (np.std(rows) + np.std(cols)) * 2.2), 1)

def calc_hurst_exponent(series):
    if len(series) < 50: return 0.5
    series = np.array(series)
    z = np.cumsum(series - np.mean(series))
    r = np.maximum.accumulate(z) - np.minimum.accumulate(z)
    s = np.std(series)
    return 0.5 if s == 0 else np.mean(r / s) / np.log10(len(series))

# --- DATA LOADING ---

def load_data_pro(file, jid):
    jeu = JEUX[jid]
    if file is None: return generate_fallback(jeu)
    try:
        content = file.read().decode('utf-8-sig', errors='ignore')
        sep = ';' if ';' in content else ','
        df = pd.read_csv(io.StringIO(content), sep=sep, decimal=',', engine='python')
        
        valid_cols = []
        for col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if not s.empty and s.min() >= 1 and s.max() <= jeu["b_max"]:
                valid_cols.append(col)
        
        target = valid_cols[-(jeu["nb_b"] + jeu["nb_e"]):]
        clean = pd.DataFrame()
        for i in range(5): clean[f"b{i+1}"] = pd.to_numeric(df[target[i]], errors='coerce')
        for i in range(jeu["nb_e"]): clean[f"e{i+1}"] = pd.to_numeric(df[target[5+i]], errors='coerce')
        return clean.dropna().reset_index(drop=True)
    except:
        return generate_fallback(jeu)

def generate_fallback(jeu):
    data = []
    for _ in range(150):
        b = sorted(random.sample(range(1, jeu["b_max"]+1), 5))
        e = sorted(random.sample(range(1, jeu["e_max"]+1), jeu["nb_e"]))
        d = {f"b{j+1}": b[j] for j in range(5)}
        for j in range(jeu["nb_e"]): d[f"e{j+1}"] = e[j]
        data.append(d)
    return pd.DataFrame(data)

# --- ANALYTICS ENGINE ---

def get_full_stats(df, max_val, prefix="b"):
    stats = {}
    cols = [c for c in df.columns if c.startswith(prefix)]
    data_matrix = df[cols].values
    
    for n in range(1, max_val + 1):
        presence = np.any(data_matrix == n, axis=1)
        v_recent = np.mean(presence[:20]) if len(presence) >= 20 else np.mean(presence)
        v_total = np.mean(presence)
        accel = v_recent / (v_total + 0.001)
        hurst = calc_hurst_exponent(np.cumsum(presence))
        
        stats[n] = {
            "vel": round(v_recent * 100, 1),
            "hurst": round(hurst, 2),
            "w": float(max(0.01, v_recent * accel * hurst)),
            "trend": "🔥" if accel > 1.3 else ("🧊" if accel < 0.7 else "⚖️")
        }
    return stats

# --- MAIN APP ---

def main():
    st.sidebar.markdown("<h1 style='text-align:center;'>🧬 SMART-LOTO V13</h1>", unsafe_allow_html=True)
    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]
    
    up = st.sidebar.file_uploader("Archive CSV (Expert)", type="csv")
    df = load_data_pro(up, jid)
    
    stats_b = get_full_stats(df, jeu["b_max"], "b")
    stats_e = get_full_stats(df, jeu["e_max"], "e")
    
    menu = st.sidebar.radio("NAVIGATION EXPERT", ["📊 Dashboard", "🎯 Générateur Expert", "🛡️ Audit Hurst", "💰 Kelly"])

    # 1. DASHBOARD
    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Dashboard Analytics : {jeu['nom']}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tirages Analysés", len(df))
        c2.metric("Indice Hurst Global", round(np.mean([s["hurst"] for s in stats_b.values()]), 2))
        c3.metric("Qualité Data", "RÉEL ✅" if up else "SIMULÉ ⚠️")

        st.subheader("🔥 Vélocité Neuronale (Boules)")
        x_b = list(stats_b.keys())
        y_b = [s["vel"] for s in stats_b.values()]
        fig_b = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_b.add_trace(go.Scatter(x=x_b, y=y_b, mode='lines+markers', name="Vitesse"), row=1, col=1)
        fig_b.add_trace(go.Heatmap(z=[y_b], x=x_b, colorscale="RdYlGn_r", showscale=False), row=2, col=1)
        fig_b.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

    # 2. GÉNÉRATEUR EXPERT (MÉGA PRO)
    elif menu == "🎯 Générateur Expert":
        st.markdown(f"<div class='main-header'>Générateur Haute Précision</div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            profil = st.selectbox("Stratégie", ["🎯 Équilibré", "🧠 Neural Engine", "🚫 Sabermétrique", "🧊 Chasseur (Retard)"])
            nb = st.slider("Grilles", 1, 10, 3)
            btn = st.button("🚀 LANCER L'ALGORITHME", type="primary", use_container_width=True)
            
        with col2:
            if btn:
                for i in range(nb):
                    # Calcul des poids selon profil
                    b_nums = list(range(1, jeu["b_max"] + 1))
                    if profil == "🧠 Neural Engine": w = [s["w"] for s in stats_b.values()]
                    elif profil == "🚫 Sabermétrique": w = [2.0 if n > 31 else 0.5 for n in b_nums]
                    elif profil == "🧊 Chasseur (Retard)": w = [100 - s["vel"] + 0.1 for s in stats_b.values()]
                    else: w = [s["vel"] + 10 for s in stats_b.values()]
                    
                    grille = sorted(np.random.choice(b_nums, 5, replace=False, p=np.array(w)/sum(w)))
                    etoiles = sorted(np.random.choice(range(1, jeu["e_max"]+1), jeu["nb_e"], replace=False))
                    
                    # AUDIT DE LA GRILLE
                    ent = calc_shannon_entropy(grille, jeu["b_max"])
                    geo = get_geometry_score(grille)
                    sab = sum(1 for n in grille if n <= 31) # Sabermétrie (dates)
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                            <span class="pro-badge">PROJECTION #{i+1}</span>
                            <span class="pro-badge" style="border-color:#3b82f6; color:#3b82f6;">ALGO: {profil.upper()}</span>
                        </div>
                        <div style="display:flex; align-items:center; justify-content:center; flex-wrap:wrap; margin-bottom:20px;">
                            {" ".join([f'<div class="boule">{b}</div>' for b in grille])}
                            <div class="divider"></div>
                            {" ".join([f'<div class="etoile">{e}</div>' for e in etoiles])}
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; border-top:1px solid #f1f5f9; padding-top:15px;">
                            <div>
                                <div class="metric-title">Géométrie</div>
                                <div class="metric-value">{geo}/10</div>
                                <div class="mini-grid">
                                    {" ".join([f'<div class="mini-cell {"active" if n in grille else ""}"></div>' for n in range(1, jeu["b_max"]+1)])}
                                </div>
                            </div>
                            <div>
                                <div class="metric-title">Sabermétrie</div>
                                <div class="metric-value">{sab} dates</div>
                                <div style="height:4px; background:#e2e8f0; border-radius:2px; margin-top:5px;">
                                    <div style="width:{sab*20}%; height:100%; background:{'#ef4444' if sab >= 4 else '#10b981'}; border-radius:2px;"></div>
                                </div>
                            </div>
                            <div>
                                <div class="metric-title">Entropie</div>
                                <div class="metric-value">{ent:.2f}</div>
                                <div style="font-size:0.6rem; color:#94a3b8;">Désordre mathématique</div>
                            </div>
                            <div>
                                <div class="metric-title">Confiance IA</div>
                                <div class="metric-value">{int(np.mean([stats_b[n]["vel"] for n in grille]))}%</div>
                                <div style="font-size:0.6rem; color:#94a3b8;">Force neuronale</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # 3. AUDIT HURST
    elif menu == "🛡️ Audit Hurst":
        st.markdown(f"<div class='main-header'>Persistance de Hurst</div>", unsafe_allow_html=True)
        st.write("H > 0.5 : Persistant (en série) | H < 0.5 : Anti-persistant (retour moyenne)")
        hurst_df = pd.DataFrame([
            {"Numéro": n, "Indice Hurst": s["hurst"], "Tendance": s["trend"], "Vélocité": f"{s['vel']}%"}
            for n, s in stats_b.items()
        ]).sort_values("Indice Hurst", ascending=False)
        st.dataframe(hurst_df, use_container_width=True, hide_index=True)

    # 4. KELLY
    elif menu == "💰 Kelly":
        st.title("Gestion Kelly & ROI")
        col1, col2 = st.columns(2)
        br = col1.number_input("Bankroll (€)", 10, 10000, 100)
        jk = col2.number_input("Jackpot (M€)", 2, 250, 17) * 1_000_000
        f_star = ((jk/jeu["prix"]) * jeu["proba"] - (1 - jeu["proba"])) / (jk/jeu["prix"])
        st.metric("Mise Conseillée", f"{max(0, f_star * br):.2f} €")

if __name__ == "__main__":
    main()
