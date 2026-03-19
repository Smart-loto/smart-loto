# ============================================================
# SMART-LOTO — PROTOTYPE FONCTIONNEL V1.0
# Fichier : app.py
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart-Loto — Analyse Intelligente",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1e40af, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 10px 0;
    }
    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }
    .boule {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white;
        border-radius: 50%;
        width: 65px;
        height: 65px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        font-weight: bold;
        margin: 5px;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.4);
    }
    .etoile {
        background: linear-gradient(135deg, #f59e0b, #fbbf24);
        color: white;
        border-radius: 50%;
        width: 65px;
        height: 65px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        font-weight: bold;
        margin: 5px;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
    }
    .grille-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 25px;
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-radius: 20px;
        margin: 15px 0;
        border: 2px solid #e2e8f0;
    }
    .score-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
    }
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .footer-disclaimer {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 12px;
        padding: 15px;
        margin-top: 30px;
        text-align: center;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {
        "nom": "Euromillions",
        "emoji": "⭐",
        "boules_max": 50,
        "nb_boules": 5,
        "etoiles_max": 12,
        "nb_etoiles": 2,
        "prix": 2.50,
        "somme_min": 90,
        "somme_max": 160,
        "jours": ["Mardi", "Vendredi"]
    },
    "loto": {
        "nom": "Loto",
        "emoji": "🎱",
        "boules_max": 49,
        "nb_boules": 5,
        "etoiles_max": None,
        "nb_etoiles": 0,
        "prix": 2.20,
        "somme_min": 60,
        "somme_max": 180,
        "jours": ["Lundi", "Mercredi", "Samedi"]
    }
}


# ============================================================
# GÉNÉRATION DE DONNÉES HISTORIQUES SIMULÉES
# ============================================================

@st.cache_data
def generer_historique(jeu_id: str, nb_tirages: int = 500) -> pd.DataFrame:
    """
    Génère un historique réaliste de tirages.
    Dans la vraie app, ces données viendront de la FDJ.
    """
    random.seed(42)
    np.random.seed(42)

    jeu = JEUX[jeu_id]
    tirages = []
    date_courante = datetime.now()

    for i in range(nb_tirages):
        boules = sorted(random.sample(range(1, jeu["boules_max"] + 1), jeu["nb_boules"]))
        etoiles = sorted(random.sample(range(1, jeu["etoiles_max"] + 1), jeu["nb_etoiles"])) if jeu["nb_etoiles"] > 0 else []

        tirage = {
            "date": date_courante - timedelta(days=i * 3.5),
            "boule_1": boules[0],
            "boule_2": boules[1],
            "boule_3": boules[2],
            "boule_4": boules[3],
            "boule_5": boules[4],
        }

        if etoiles:
            tirage["etoile_1"] = etoiles[0]
            tirage["etoile_2"] = etoiles[1]

        tirages.append(tirage)

    df = pd.DataFrame(tirages)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.sort_values("date", ascending=False).reset_index(drop=True)


# ============================================================
# MOTEUR STATISTIQUE
# ============================================================

@st.cache_data
def calculer_stats(df: pd.DataFrame, jeu_id: str) -> dict:
    """
    Calcule toutes les statistiques pour chaque numéro.
    """
    jeu = JEUX[jeu_id]
    stats = {}

    cols_boules = [f"boule_{i}" for i in range(1, 6)]

    tous_numeros = []
    for col in cols_boules:
        tous_numeros.extend(df[col].tolist())

    df_20 = df.head(20)
    numeros_20 = []
    for col in cols_boules:
        numeros_20.extend(df_20[col].tolist())

    date_12m = datetime.now().date() - timedelta(days=365)
    df_12m = df[df["date"] >= date_12m]
    numeros_12m = []
    for col in cols_boules:
        numeros_12m.extend(df_12m[col].tolist())

    freq_totale = Counter(tous_numeros)
    freq_20 = Counter(numeros_20)
    freq_12m = Counter(numeros_12m)

    for numero in range(1, jeu["boules_max"] + 1):
        ecart = 0
        for idx, row in df.iterrows():
            boules_tirage = [row[col] for col in cols_boules]
            if numero in boules_tirage:
                break
            ecart += 1

        positions = []
        for idx, row in df.iterrows():
            boules_tirage = [row[col] for col in cols_boules]
            if numero in boules_tirage:
                positions.append(idx)

        ecarts_historiques = []
        for i in range(len(positions) - 1):
            ecarts_historiques.append(positions[i + 1] - positions[i])

        ecart_moyen = np.mean(ecarts_historiques) if ecarts_historiques else 10
        ecart_max = max(ecarts_historiques) if ecarts_historiques else ecart

        forme_norm = (freq_20.get(numero, 0) / 20) * 100
        freq_theorique_12m = (len(df_12m) * 5) / jeu["boules_max"]
        freq_norm = (freq_12m.get(numero, 0) / max(freq_theorique_12m, 1)) * 50
        ecart_penalty = max(0, 30 - (ecart * 2))
        indice_chaleur = min(100, max(0, 0.40 * forme_norm + 0.35 * freq_norm + 0.25 * ecart_penalty))

        stats[numero] = {
            "numero": numero,
            "ecart_actuel": ecart,
            "ecart_moyen": round(ecart_moyen, 1),
            "ecart_max": ecart_max,
            "frequence_totale": freq_totale.get(numero, 0),
            "frequence_20t": freq_20.get(numero, 0),
            "frequence_12m": freq_12m.get(numero, 0),
            "indice_chaleur": round(indice_chaleur, 1)
        }

    stats_etoiles = {}
    if jeu["nb_etoiles"] > 0:
        cols_etoiles = ["etoile_1", "etoile_2"]
        tous_etoiles = []
        for col in cols_etoiles:
            tous_etoiles.extend(df[col].tolist())

        etoiles_20 = []
        for col in cols_etoiles:
            etoiles_20.extend(df_20[col].tolist())

        freq_etoiles = Counter(tous_etoiles)
        freq_etoiles_20 = Counter(etoiles_20)

        for numero in range(1, jeu["etoiles_max"] + 1):
            ecart = 0
            for idx, row in df.iterrows():
                etoiles_tirage = [row[col] for col in cols_etoiles]
                if numero in etoiles_tirage:
                    break
                ecart += 1

            stats_etoiles[numero] = {
                "numero": numero,
                "ecart_actuel": ecart,
                "frequence_totale": freq_etoiles.get(numero, 0),
                "frequence_20t": freq_etoiles_20.get(numero, 0),
            }

    paires = Counter()
    for idx, row in df.iterrows():
        boules = sorted([row[col] for col in cols_boules])
        for i in range(len(boules)):
            for j in range(i + 1, len(boules)):
                paires[(int(boules[i]), int(boules[j]))] += 1

    top_paires = paires.most_common(10)

    return {
        "boules": stats,
        "etoiles": stats_etoiles,
        "paires": top_paires
    }


# ============================================================
# SCORE DE ROBUSTESSE
# ============================================================

def score_robustesse(grille: list, etoiles: list, stats: dict) -> dict:
    scores = {}

    nb_pairs = sum(1 for n in grille if n % 2 == 0)
    ratio = nb_pairs / len(grille)
    if 0.3 <= ratio <= 0.7:
        scores["⚖️ Parité"] = 25
    elif 0.2 <= ratio <= 0.8:
        scores["⚖️ Parité"] = 15
    else:
        scores["⚖️ Parité"] = 5

    dizaines = Counter(n // 10 for n in grille)
    nb_diz = len(dizaines)
    max_conc = max(dizaines.values())
    if nb_diz >= 4 and max_conc <= 2:
        scores["📊 Dizaines"] = 20
    elif nb_diz >= 3 and max_conc <= 3:
        scores["📊 Dizaines"] = 15
    else:
        scores["📊 Dizaines"] = 5

    somme = sum(grille)
    z = abs(somme - 127.5) / 35
    if z <= 0.5:
        scores["➕ Somme"] = 20
    elif z <= 1.0:
        scores["➕ Somme"] = 15
    elif z <= 1.5:
        scores["➕ Somme"] = 10
    else:
        scores["➕ Somme"] = 3

    ecarts = [stats["boules"][n]["ecart_actuel"] for n in grille if n in stats["boules"]]
    if len(set(ecarts)) > 1:
        ecart_std = float(np.std(ecarts))
        if ecart_std > 5:
            scores["🔀 Diversité"] = 15
        elif ecart_std > 3:
            scores["🔀 Diversité"] = 10
        else:
            scores["🔀 Diversité"] = 5
    else:
        scores["🔀 Diversité"] = 5

    g = sorted(grille)
    has_suite = any(g[i+1] == g[i]+1 and g[i+2] == g[i]+2 for i in range(len(g)-2))
    scores["🚫 Anti-suite"] = 2 if has_suite else 10

    if etoiles and len(etoiles) == 2:
        ecart_e = abs(etoiles[0] - etoiles[1])
        scores["⭐ Étoiles"] = 10 if ecart_e >= 3 else (6 if ecart_e >= 2 else 2)
    else:
        scores["⭐ Étoiles"] = 10

    total = sum(scores.values())
    return {"total": total, "detail": scores}


# ============================================================
# GÉNÉRATEUR DE GRILLES
# ============================================================

def generer_grille(
    jeu_id: str,
    stats: dict,
    mode: str = "aleatoire",
    filtre_parite: bool = False,
    filtre_somme: bool = False,
    filtre_dizaines: bool = False,
    filtre_anti_suite: bool = False,
    chasseur_ecart: int = 0,
    numeros_forces: list = None,
    ecart_etoiles_min: int = 0,
    max_tentatives: int = 1000
) -> dict:

    jeu = JEUX[jeu_id]

    for tentative in range(max_tentatives):
        if mode == "chaud":
            pool = sorted(stats["boules"].keys(),
                         key=lambda x: stats["boules"][x]["indice_chaleur"],
                         reverse=True)[:20]
        elif mode == "froid":
            pool = sorted(stats["boules"].keys(),
                         key=lambda x: stats["boules"][x]["ecart_actuel"],
                         reverse=True)[:20]
        elif mode == "top":
            pool = sorted(stats["boules"].keys(),
                         key=lambda x: stats["boules"][x]["frequence_12m"],
                         reverse=True)[:15]
        elif mode == "hybride":
            numeros_list = list(stats["boules"].keys())
            poids = [stats["boules"][n]["indice_chaleur"] ** 1.5 + 5 for n in numeros_list]
            total_poids = sum(poids)
            probs = [p / total_poids for p in poids]
            pool = list(np.random.choice(numeros_list, size=min(25, len(numeros_list)),
                                         replace=False, p=probs))
        else:
            pool = list(range(1, jeu["boules_max"] + 1))

        if chasseur_ecart > 0:
            pool = [n for n in pool if stats["boules"][n]["ecart_actuel"] >= chasseur_ecart]

        nb_a_generer = jeu["nb_boules"]
        forces = list(numeros_forces or [])
        forces = [f for f in forces if 1 <= f <= jeu["boules_max"]]

        pool_disponible = [n for n in pool if n not in forces]
        nb_manquant = nb_a_generer - len(forces)

        if nb_manquant > len(pool_disponible):
            pool_disponible = [n for n in range(1, jeu["boules_max"] + 1) if n not in forces]

        if nb_manquant > 0:
            choisis = random.sample(pool_disponible, min(nb_manquant, len(pool_disponible)))
        else:
            choisis = []

        grille = sorted(forces + choisis)[:nb_a_generer]

        etoiles = []
        if jeu["nb_etoiles"] > 0:
            for _ in range(100):
                etoiles = sorted(random.sample(range(1, jeu["etoiles_max"] + 1), jeu["nb_etoiles"]))
                if ecart_etoiles_min > 0 and len(etoiles) == 2:
                    if abs(etoiles[0] - etoiles[1]) >= ecart_etoiles_min:
                        break
                else:
                    break

        valide = True

        if filtre_parite:
            nb_pairs = sum(1 for n in grille if n % 2 == 0)
            if nb_pairs == 0 or nb_pairs == len(grille):
                valide = False

        if filtre_somme:
            somme = sum(grille)
            if not (jeu["somme_min"] <= somme <= jeu["somme_max"]):
                valide = False

        if filtre_dizaines:
            diz = Counter(n // 10 for n in grille)
            if max(diz.values()) > 3:
                valide = False

        if filtre_anti_suite:
            g = sorted(grille)
            for i in range(len(g) - 2):
                if g[i+1] == g[i]+1 and g[i+2] == g[i]+2:
                    valide = False
                    break

        if valide:
            score = score_robustesse(grille, etoiles, stats)
            return {
                "grille": grille,
                "etoiles": etoiles,
                "score": score,
                "tentatives": tentative + 1,
                "mode": mode
            }

    grille = sorted(random.sample(range(1, jeu["boules_max"] + 1), jeu["nb_boules"]))
    etoiles = sorted(random.sample(range(1, jeu["etoiles_max"] + 1), jeu["nb_etoiles"])) if jeu["nb_etoiles"] > 0 else []
    score = score_robustesse(grille, etoiles, stats)
    return {"grille": grille, "etoiles": etoiles, "score": score, "tentatives": max_tentatives, "mode": "fallback"}


# ============================================================
# MINI BACKTESTING
# ============================================================

def mini_backtest(df, jeu_id, stats, mode, nb_tirages_test=50, grilles_par_tirage=1):
    jeu = JEUX[jeu_id]
    cols_boules = [f"boule_{i}" for i in range(1, 6)]
    resultats = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    total_mise = 0
    gains_table = {0: 0, 1: 0, 2: 0, 3: 4, 4: 50, 5: 5000}
    total_gains = 0
    historique = []

    for idx in range(min(nb_tirages_test, len(df))):
        tirage = df.iloc[idx]
        boules_tirage = set([int(tirage[col]) for col in cols_boules])

        for _ in range(grilles_par_tirage):
            resultat = generer_grille(jeu_id, stats, mode=mode)
            grille_set = set(resultat["grille"])
            nb_bons = len(grille_set & boules_tirage)
            resultats[str(nb_bons)] += 1
            total_mise += jeu["prix"]
            gain = gains_table.get(nb_bons, 0)
            total_gains += gain

            if nb_bons >= 3:
                historique.append({
                    "date": tirage["date"],
                    "grille": resultat["grille"],
                    "tirage": list(boules_tirage),
                    "bons": nb_bons,
                    "gain": gain
                })

    return {
        "resultats": resultats,
        "total_mise": round(total_mise, 2),
        "total_gains": round(total_gains, 2),
        "bilan": round(total_gains - total_mise, 2),
        "nb_grilles": nb_tirages_test * grilles_par_tirage,
        "historique": historique
    }


# ============================================================
# SYSTÈME RÉDUCTEUR SIMPLIFIÉ
# ============================================================

def systeme_reducteur_simple(numeros_choisis: list, taille_grille: int = 5) -> list:
    """
    Version simplifiée du système réducteur.
    Génère des grilles diversifiées à partir d'une sélection élargie.
    """
    from itertools import combinations

    if len(numeros_choisis) <= taille_grille:
        return [sorted(numeros_choisis)]

    toutes_combs = list(combinations(numeros_choisis, taille_grille))

    grilles = []
    numeros_couverts = set()

    random.shuffle(toutes_combs)

    for comb in toutes_combs:
        comb_set = set(comb)
        nouveaux = comb_set - numeros_couverts

        if len(nouveaux) >= 1 or len(grilles) == 0:
            grilles.append(sorted(list(comb)))
            numeros_couverts |= comb_set

        if numeros_couverts == set(numeros_choisis) and len(grilles) >= 3:
            break

        if len(grilles) >= 10:
            break

    return grilles


# ============================================================
# INTERFACE PRINCIPALE
# ============================================================

def main():
    # ---- SIDEBAR ----
    st.sidebar.markdown(
        "<div style='text-align:center;'>"
        "<h1 style='font-size:2rem;'>🎱 Smart-Loto</h1>"
        "<p style='color:#64748b;font-size:0.9rem;'>Analyse Statistique Intelligente</p>"
        "</div>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

    jeu_id = st.sidebar.selectbox(
        "🎮 Choisis ton jeu",
        ["euromillions", "loto"],
        format_func=lambda x: f"{JEUX[x]['emoji']} {JEUX[x]['nom']}"
    )

    page = st.sidebar.radio(
        "📑 Navigation",
        [
            "🏠 Dashboard",
            "🎯 Générateur",
            "📊 Statistiques",
            "🧪 Backtesting",
            "🧮 Réducteur",
            "ℹ️ À propos"
        ]
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        "<div style='background:#fef3c7;padding:12px;border-radius:10px;"
        "border:1px solid #f59e0b;font-size:0.8rem;text-align:center;'>"
        "⚠️ Prototype de démonstration<br>"
        "Données simulées<br>"
        "Aucune garantie de gain<br><br>"
        "🛡️ <a href='https://www.joueurs-info-service.fr/' target='_blank'>"
        "Joueurs Info Service</a><br>09 74 75 13 13"
        "</div>",
        unsafe_allow_html=True
    )

    # Charger les données
    df = generer_historique(jeu_id)
    stats = calculer_stats(df, jeu_id)
    jeu = JEUX[jeu_id]

    # ================================================================
    # PAGE : DASHBOARD
    # ================================================================
    if page == "🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — Analyse en temps réel</div>",
                    unsafe_allow_html=True)

        # Dernier tirage
        dernier = df.iloc[0]
        cols_b = [f"boule_{i}" for i in range(1, 6)]
        boules_dernier = [int(dernier[c]) for c in cols_b]

        st.subheader(f"🎱 Dernier tirage — {dernier['date']}")

        boules_html = "<div class='grille-container'>"
        for b in boules_dernier:
            boules_html += f"<span class='boule'>{b}</span>"

        if jeu["nb_etoiles"] > 0:
            boules_html += "<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
            for i in range(jeu["nb_etoiles"]):
                e = int(dernier[f"etoile_{i+1}"])
                boules_html += f"<span class='etoile'>⭐{e}</span>"

        boules_html += "</div>"
        st.markdown(boules_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Métriques rapides
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        chaud_top = max(stats["boules"].values(), key=lambda x: x["indice_chaleur"])
        froid_top = max(stats["boules"].values(), key=lambda x: x["ecart_actuel"])
        col_m1.metric("🔥 Plus chaud", f"N°{chaud_top['numero']}",
                     f"Chaleur: {chaud_top['indice_chaleur']}")
        col_m2.metric("🧊 Plus absent", f"N°{froid_top['numero']}",
                     f"Écart: {froid_top['ecart_actuel']}")
        col_m3.metric("📅 Tirages analysés", f"{len(df)}")
        col_m4.metric("📊 Période", f"{df.iloc[-1]['date']} → {df.iloc[0]['date']}")

        st.markdown("---")

        # Top chauds et froids
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔥 Top 10 — En Forme")
            chauds = sorted(stats["boules"].values(),
                          key=lambda x: x["indice_chaleur"], reverse=True)[:10]
            df_chauds = pd.DataFrame(chauds)[
                ["numero", "indice_chaleur", "frequence_20t", "ecart_actuel"]
            ]
            df_chauds.columns = ["N°", "🌡️ Chaleur", "Freq (20t)", "Écart"]
            st.dataframe(df_chauds, hide_index=True, use_container_width=True)

        with col2:
            st.subheader("🧊 Top 10 — Grands Absents")
            froids = sorted(stats["boules"].values(),
                          key=lambda x: x["ecart_actuel"], reverse=True)[:10]
            df_froids = pd.DataFrame(froids)[
                ["numero", "ecart_actuel", "ecart_moyen", "ecart_max"]
            ]
            df_froids.columns = ["N°", "Écart actuel", "Écart moyen", "Record"]
            st.dataframe(df_froids, hide_index=True, use_container_width=True)

        # Paires
        st.subheader("💑 Paires les plus fréquentes (top 8)")
        paires_data = [{"Paire": f"{p[0][0]} — {p[0][1]}", "Fréquence": p[1]}
                       for p in stats["paires"][:8]]
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.dataframe(pd.DataFrame(paires_data[:4]), hide_index=True,
                        use_container_width=True)
        with col_p2:
            st.dataframe(pd.DataFrame(paires_data[4:8]), hide_index=True,
                        use_container_width=True)

        # Étoiles (Euromillions)
        if stats["etoiles"]:
            st.subheader("⭐ Étoiles — Situation")
            df_etoiles = pd.DataFrame([
                {
                    "⭐": f"Étoile {s['numero']}",
                    "Écart": s["ecart_actuel"],
                    "Freq (20t)": s["frequence_20t"],
                    "Freq totale": s["frequence_totale"]
                }
                for s in stats["etoiles"].values()
            ])
            st.dataframe(df_etoiles, hide_index=True, use_container_width=True)

    # ================================================================
    # PAGE : GÉNÉRATEUR
    # ================================================================
    elif page == "🎯 Générateur":
        st.markdown("<div class='main-header'>🎯 Générateur de Grilles</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>Configure tes filtres et génère des grilles optimisées</div>",
                    unsafe_allow_html=True)

        col_config1, col_config2 = st.columns(2)

        with col_config1:
            st.markdown("### 📌 Niveau 1 — Tendance")
            mode = st.selectbox(
                "Mode de sélection",
                ["aleatoire", "chaud", "froid", "top", "hybride"],
                format_func=lambda x: {
                    "aleatoire": "🎲 Aléatoire (Gratuit)",
                    "chaud": "🔥 En Forme — Top chaleur récente",
                    "froid": "🧊 Peu Probable — Grands absents",
                    "top": "⭐ Top du Top — Stars de l'année",
                    "hybride": "🧠 Hybride Intelligent — Mix pondéré"
                }[x]
            )

            st.markdown("### 📌 Niveau 2 — Préférences")
            numeros_forces_input = st.text_input(
                "🔒 Numéros forcés (max 3, séparés par virgules)",
                placeholder="Ex: 7, 14, 23"
            )
            numeros_forces = []
            if numeros_forces_input:
                try:
                    numeros_forces = [int(n.strip()) for n in numeros_forces_input.split(",")
                                     if n.strip().isdigit()]
                    numeros_forces = [n for n in numeros_forces
                                     if 1 <= n <= jeu["boules_max"]][:3]
                    if numeros_forces:
                        st.success(f"Numéros forcés : {numeros_forces}")
                except ValueError:
                    st.error("Format invalide")

            chasseur = st.slider(
                "🎯 Chasseur d'écart (écart minimum requis)",
                0, 30, 0,
                help="Inclut uniquement les numéros absents depuis au moins X tirages"
            )

        with col_config2:
            st.markdown("### 📌 Niveau 3 — Filtres structurels")
            filtre_parite = st.checkbox("⚖️ Équilibre Parité", value=True,
                                        help="Rejette 100% paires ou 100% impaires")
            filtre_somme = st.checkbox("➕ Somme Gaussienne", value=True,
                                       help=f"Somme entre {jeu['somme_min']} et {jeu['somme_max']}")
            filtre_dizaines = st.checkbox("📊 Répartition Dizaines", value=True,
                                          help="Max 3 numéros par dizaine")
            filtre_anti_suite = st.checkbox("🚫 Anti-suite", value=True,
                                            help="Interdit les suites de 3 consécutifs")

            ecart_etoiles = 0
            if jeu["nb_etoiles"] > 0:
                ecart_etoiles = st.slider("⭐ Écart minimum entre étoiles", 0, 8, 2)

            st.markdown("### 📌 Options")
            nb_grilles = st.selectbox("Nombre de grilles à générer",
                                      [1, 3, 5, 10], index=1)

        st.markdown("---")

        # Bouton
        col_btn = st.columns([1, 2, 1])
        with col_btn[1]:
            generer_btn = st.button("🎱 GÉNÉRER MES GRILLES",
                                    type="primary", use_container_width=True)

        if generer_btn:
            st.markdown("---")

            for g_idx in range(nb_grilles):
                resultat = generer_grille(
                    jeu_id=jeu_id, stats=stats, mode=mode,
                    filtre_parite=filtre_parite, filtre_somme=filtre_somme,
                    filtre_dizaines=filtre_dizaines, filtre_anti_suite=filtre_anti_suite,
                    chasseur_ecart=chasseur, numeros_forces=numeros_forces,
                    ecart_etoiles_min=ecart_etoiles
                )

                score = resultat["score"]
                grille = resultat["grille"]
                etoiles_gen = resultat["etoiles"]

                if score["total"] >= 80: etoiles_viz = "⭐⭐⭐⭐⭐"
                elif score["total"] >= 65: etoiles_viz = "⭐⭐⭐⭐"
                elif score["total"] >= 50: etoiles_viz = "⭐⭐⭐"
                elif score["total"] >= 35: etoiles_viz = "⭐⭐"
                else: etoiles_viz = "⭐"

                with st.container():
                    st.markdown(f"#### Grille {g_idx + 1} / {nb_grilles}")

                    html = "<div class='grille-container'>"
                    for b in grille:
                        html += f"<span class='boule'>{b}</span>"
                    if etoiles_gen:
                        html += "<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
                        for e in etoiles_gen:
                            html += f"<span class='etoile'>⭐{e}</span>"
                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)

                    col_s1, col_s2 = st.columns([1, 2])

                    with col_s1:
                        score_color = "#22c55e" if score["total"] >= 70 else (
                            "#f59e0b" if score["total"] >= 50 else "#ef4444")
                        st.markdown(
                            f"<div style='text-align:center;padding:15px;'>"
                            f"<div style='font-size:3rem;font-weight:800;"
                            f"color:{score_color};'>{score['total']}</div>"
                            f"<div style='font-size:0.9rem;color:#64748b;'>/ 100</div>"
                            f"<div style='font-size:1.2rem;margin-top:5px;'>{etoiles_viz}</div>"
                            f"<div style='font-size:0.8rem;color:#94a3b8;margin-top:5px;'>"
                            f"Somme: {sum(grille)} | "
                            f"P: {sum(1 for n in grille if n%2==0)} "
                            f"I: {sum(1 for n in grille if n%2!=0)}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    with col_s2:
                        max_pts = {"⚖️ Parité": 25, "📊 Dizaines": 20,
                                  "➕ Somme": 20, "🔀 Diversité": 15,
                                  "🚫 Anti-suite": 10, "⭐ Étoiles": 10}

                        for critere, pts in score["detail"].items():
                            mx = max_pts.get(critere, 10)
                            pct = pts / mx
                            color = "#22c55e" if pct >= 0.7 else (
                                "#f59e0b" if pct >= 0.4 else "#ef4444")
                            bar = "█" * int(pct * 12) + "░" * (12 - int(pct * 12))
                            st.markdown(
                                f"<span style='font-family:monospace;'>"
                                f"{critere} <span style='color:{color};'>{bar}</span>"
                                f" **{pts}/{mx}**</span>",
                                unsafe_allow_html=True
                            )

                    st.markdown("---")

    # ================================================================
    # PAGE : STATISTIQUES
    # ================================================================
    elif page == "📊 Statistiques":
        st.markdown("<div class='main-header'>📊 Statistiques Complètes</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {len(df)} tirages analysés</div>",
                    unsafe_allow_html=True)

        # Heatmap
        st.subheader("🌡️ Carte de Chaleur")

        nb_cols_heat = 10
        nb_rows_heat = (jeu["boules_max"] + nb_cols_heat - 1) // nb_cols_heat

        z_data = []
        text_data = []
        for row in range(nb_rows_heat):
            z_row, t_row = [], []
            for col in range(nb_cols_heat):
                num = row * nb_cols_heat + col + 1
                if num <= jeu["boules_max"]:
                    s = stats["boules"][num]
                    z_row.append(s["indice_chaleur"])
                    t_row.append(f"N°{num}<br>Chaleur: {s['indice_chaleur']}<br>"
                                f"Écart: {s['ecart_actuel']}<br>Freq 20t: {s['frequence_20t']}")
                else:
                    z_row.append(None)
                    t_row.append("")
            z_data.append(z_row)
            text_data.append(t_row)

        fig_heat = go.Figure(data=go.Heatmap(
            z=z_data, text=text_data, hoverinfo="text",
            colorscale=[[0, "#1e3a5f"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            showscale=True, colorbar=dict(title="Chaleur")
        ))
        for row in range(nb_rows_heat):
            for col in range(nb_cols_heat):
                num = row * nb_cols_heat + col + 1
                if num <= jeu["boules_max"]:
                    fig_heat.add_annotation(x=col, y=row, text=str(num),
                        showarrow=False, font=dict(color="white", size=14, family="Arial Black"))

        fig_heat.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20),
                              xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
        st.plotly_chart(fig_heat, use_container_width=True)

        # Écarts
        st.subheader("📈 Écarts actuels vs Moyenne")

        ecart_data = [(n, stats["boules"][n]["ecart_actuel"],
                       stats["boules"][n]["ecart_moyen"]) for n in range(1, jeu["boules_max"]+1)]

        fig_ecarts = go.Figure()
        fig_ecarts.add_trace(go.Bar(
            x=[d[0] for d in ecart_data], y=[d[1] for d in ecart_data], name="Écart actuel",
            marker_color=["#ef4444" if d[1] > d[2] * 1.3 else "#3b82f6" for d in ecart_data]
        ))
        fig_ecarts.add_trace(go.Scatter(
            x=[d[0] for d in ecart_data], y=[d[2] for d in ecart_data], name="Écart moyen",
            mode="lines", line=dict(color="#f59e0b", width=2, dash="dash")
        ))
        fig_ecarts.update_layout(height=350, xaxis_title="Numéro", yaxis_title="Tirages",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig_ecarts, use_container_width=True)

        # Fréquences
        st.subheader("📊 Fréquences (20 derniers tirages)")
        freq_data = [(n, stats["boules"][n]["frequence_20t"])
                     for n in range(1, jeu["boules_max"]+1)]
        freq_data.sort(key=lambda x: x[1], reverse=True)

        fig_freq = go.Figure(go.Bar(
            x=[str(f[0]) for f in freq_data], y=[f[1] for f in freq_data],
            marker_color=["#22c55e" if f[1] >= 3 else ("#f59e0b" if f[1] >= 2 else "#94a3b8")
                         for f in freq_data]
        ))
        fig_freq.update_layout(height=300, xaxis_title="Numéro", yaxis_title="Sorties")
        st.plotly_chart(fig_freq, use_container_width=True)

        # Tableau
        st.subheader("📋 Tableau complet")
        tri = st.selectbox("Trier par", ["🌡️ Chaleur", "Écart", "Freq 20t", "Freq 12m"])
        df_complet = pd.DataFrame([{
            "N°": n, "🌡️ Chaleur": stats["boules"][n]["indice_chaleur"],
            "Écart": stats["boules"][n]["ecart_actuel"],
            "Écart moy.": stats["boules"][n]["ecart_moyen"],
            "Record": stats["boules"][n]["ecart_max"],
            "Freq 20t": stats["boules"][n]["frequence_20t"],
            "Freq 12m": stats["boules"][n]["frequence_12m"],
        } for n in range(1, jeu["boules_max"]+1)])

        df_complet = df_complet.sort_values(tri, ascending=(tri == "Écart"))
        st.dataframe(df_complet, hide_index=True, use_container_width=True, height=500)

    # ================================================================
    # PAGE : BACKTESTING
    # ================================================================
    elif page == "🧪 Backtesting":
        st.markdown("<div class='main-header'>🧪 Backtesting</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Teste ta stratégie sur l'historique</div>",
                    unsafe_allow_html=True)

        col_bt1, col_bt2 = st.columns(2)
        with col_bt1:
            mode_bt = st.selectbox("Stratégie", ["aleatoire", "chaud", "froid", "top", "hybride"],
                format_func=lambda x: {"aleatoire": "🎲 Aléatoire", "chaud": "🔥 En Forme",
                    "froid": "🧊 Peu Probable", "top": "⭐ Top du Top",
                    "hybride": "🧠 Hybride"}[x])
        with col_bt2:
            nb_bt = st.selectbox("Tirages à tester", [20, 50, 100, 200], index=1)

        if st.button("🚀 LANCER LE BACKTEST", type="primary", use_container_width=True):
            with st.spinner("⏳ Simulation en cours..."):
                res_bt = mini_backtest(df, jeu_id, stats, mode_bt, nb_bt)

            st.markdown("---")

            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("💰 Misé", f"{res_bt['total_mise']} €")
            col_r2.metric("🏆 Gagné", f"{res_bt['total_gains']} €")
            bilan = res_bt['bilan']
            col_r3.metric("📈 Bilan", f"{bilan:+.2f} €",
                         delta_color="normal" if bilan >= 0 else "inverse")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                res = res_bt["resultats"]
                fig_bt = go.Figure(go.Bar(
                    x=[f"{k} bons" for k in sorted(res.keys())],
                    y=[res[k] for k in sorted(res.keys())],
                    marker_color=["#ef4444", "#f97316", "#f59e0b",
                                  "#84cc16", "#22c55e", "#15803d"],
                    text=[res[k] for k in sorted(res.keys())], textposition="auto"
                ))
                fig_bt.update_layout(height=300, title="Correspondances")
                st.plotly_chart(fig_bt, use_container_width=True)

            with col_g2:
                df_res = pd.DataFrame([{
                    "Résultat": f"{k}/5 bons numéros",
                    "Occurrences": v,
                    "%": f"{v/res_bt['nb_grilles']*100:.1f}%"
                } for k, v in sorted(res.items(), reverse=True)])
                st.dataframe(df_res, hide_index=True, use_container_width=True)

            if res_bt["historique"]:
                st.subheader("🎯 Meilleures correspondances")
                for h in res_bt["historique"][:5]:
                    st.markdown(f"📅 **{h['date']}** — Grille: `{h['grille']}` "
                               f"— **{h['bons']} bons** — Gain: {h['gain']}€")

            st.info("⚠️ Performances passées ≠ résultats futurs. Chaque tirage est indépendant.")

    # ================================================================
    # PAGE : RÉDUCTEUR
    # ================================================================
    elif page == "🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Système Réducteur</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Choisis plus de numéros, "
                    "le système génère les grilles optimales</div>", unsafe_allow_html=True)

        st.markdown("""
        **Comment ça marche :**
        1. Sélectionne **8 à 15 numéros** que tu penses gagnants
        2. Le système génère automatiquement des grilles de 5 numéros
        3. Les grilles sont **diversifiées** pour maximiser la couverture
        """)

        numeros_input = st.text_input(
            "🔢 Tes numéros sélectionnés (séparés par virgules)",
            placeholder="Ex: 3, 7, 14, 19, 23, 28, 34, 41"
        )

        if numeros_input:
            try:
                numeros = [int(n.strip()) for n in numeros_input.split(",")
                          if n.strip().isdigit()]
                numeros = sorted(set([n for n in numeros if 1 <= n <= jeu["boules_max"]]))

                if len(numeros) < 6:
                    st.warning("⚠️ Sélectionne au moins 6 numéros pour activer le réducteur.")
                elif len(numeros) > 15:
                    st.warning("⚠️ Maximum 15 numéros. Les premiers 15 seront utilisés.")
                    numeros = numeros[:15]
                else:
                    st.success(f"✅ {len(numeros)} numéros sélectionnés : {numeros}")

                    if st.button("🧮 GÉNÉRER LE SYSTÈME RÉDUIT",
                                type="primary", use_container_width=True):

                        grilles_red = systeme_reducteur_simple(numeros)

                        st.markdown("---")
                        st.subheader(f"📋 {len(grilles_red)} grilles générées")

                        cout = len(grilles_red) * jeu["prix"]
                        st.info(f"💰 Coût total : {len(grilles_red)} × {jeu['prix']}€ = **{cout:.2f}€**")

                        for i, gr in enumerate(grilles_red):
                            etoiles_r = sorted(random.sample(
                                range(1, jeu["etoiles_max"] + 1), jeu["nb_etoiles"]
                            )) if jeu["nb_etoiles"] > 0 else []

                            score_r = score_robustesse(gr, etoiles_r, stats)

                            html_r = f"<div class='grille-container'><strong>G{i+1}</strong>&nbsp;&nbsp;"
                            for b in gr:
                                html_r += f"<span class='boule'>{b}</span>"
                            if etoiles_r:
                                html_r += "<span style='margin:0 10px;color:#94a3b8;'>|</span>"
                                for e in etoiles_r:
                                    html_r += f"<span class='etoile'>⭐{e}</span>"
                            html_r += f"&nbsp;&nbsp;<span style='color:#64748b;'>"
                            html_r += f"Score: {score_r['total']}/100</span></div>"
                            st.markdown(html_r, unsafe_allow_html=True)

                        # Matrice de couverture
                        st.subheader("📊 Matrice de couverture")
                        couverture = {}
                        for n in numeros:
                            couverture[n] = sum(1 for g in grilles_red if n in g)

                        df_couv = pd.DataFrame([{
                            "Numéro": n, "Présent dans": f"{c} grille(s)",
                            "Couverture": f"{c/len(grilles_red)*100:.0f}%"
                        } for n, c in couverture.items()])
                        st.dataframe(df_couv, hide_index=True, use_container_width=True)

            except Exception as e:
                st.error(f"Erreur : {e}")

    # ================================================================
    # PAGE : À PROPOS
    # ================================================================
    elif page == "ℹ️ À propos":
        st.markdown("<div class='main-header'>ℹ️ À propos</div>", unsafe_allow_html=True)

        st.markdown("""
        ## 🎯 Smart-Loto — Prototype

        **Outil d'aide à la décision** pour les joueurs de loterie,
        basé sur l'analyse statistique des tirages historiques.

        ### ✅ Fonctionnalités du prototype

        | Module | Description | Statut |
        |--------|------------|--------|
        | 🏠 Dashboard | Stats en temps réel, top chauds/froids | ✅ |
        | 🎯 Générateur | 5 modes + 6 filtres + score robustesse | ✅ |
        | 📊 Statistiques | Heatmap, écarts, fréquences, tableau | ✅ |
        | 🧪 Backtesting | Test de stratégie sur l'historique | ✅ |
        | 🧮 Réducteur | Système réducteur simplifié | ✅ |

        ### ⏳ Prévu pour le SAAS complet

        | Module | Description |
        |--------|------------|
        | 🔐 Comptes | Inscription, abonnements Premium/Elite |
        | 📱 Mobile | Interface responsive, mode buraliste |
        | 🔔 Alertes | Notifications email/SMS/push |
        | 👥 Syndicats | Gestion de groupes de joueurs |
        | 📄 Export PDF | Bulletins imprimables |
        | 📡 Données réelles | Connexion API FDJ |

        ### ⚠️ Avertissements importants

        - **Ce n'est PAS un outil de prédiction**
        - **Aucune garantie de gain**
        - Les données de ce prototype sont **simulées**
        - Chaque tirage est un **événement indépendant**

        ### 🛡️ Jeu Responsable

        Jouer comporte des risques : endettement, isolement, dépendance.

        **Joueurs Info Service : 09 74 75 13 13**

        [www.joueurs-info-service.fr](https://www.joueurs-info-service.fr/)
        """)

    # ---- FOOTER ----
    st.markdown(
        "<div class='footer-disclaimer'>"
        "⚠️ Cet outil est un prototype d'analyse statistique. "
        "Il ne garantit aucun gain. Les loteries sont des jeux de hasard. "
        "Chaque tirage est indépendant.<br>"
        "🛡️ Jouer comporte des risques. "
        "<a href='https://www.joueurs-info-service.fr/' target='_blank'>"
        "Joueurs Info Service</a> : 09 74 75 13 13"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
