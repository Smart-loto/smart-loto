# ============================================================
# SMART-LOTO — PROTOTYPE V2.0 — DONNÉES RÉELLES CSV
# Fichier : app.py
# Lancer : streamlit run app.py
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import io

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart-Loto — Analyse Intelligente",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .data-badge-real {
        background: #22c55e;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .data-badge-simulated {
        background: #f59e0b;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
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
    .upload-zone {
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        border: 2px dashed #3b82f6;
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
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
# CHARGEMENT DES DONNÉES — CSV RÉEL OU SIMULÉ
# ============================================================

def detecter_et_charger_csv(uploaded_file, jeu_id: str) -> pd.DataFrame:
    """
    Détecte automatiquement le format du CSV FDJ
    et le convertit en format interne standardisé.
    
    Gère plusieurs formats possibles :
    - Séparateur ; ou ,
    - Dates DD/MM/YYYY ou YYYY-MM-DD
    - Colonnes nommées différemment
    """
    jeu = JEUX[jeu_id]
    
    # Lire le contenu brut pour détecter le séparateur
    content = uploaded_file.read()
    uploaded_file.seek(0)  # Remettre au début
    
    # Essayer de décoder
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except UnicodeDecodeError:
            text = content.decode("iso-8859-1")
    
    # Détecter le séparateur
    first_line = text.split("\n")[0]
    if ";" in first_line:
        sep = ";"
    elif "\t" in first_line:
        sep = "\t"
    else:
        sep = ","
    
    # Charger le CSV
    try:
        df = pd.read_csv(io.StringIO(text), sep=sep, encoding="utf-8")
    except Exception:
        df = pd.read_csv(io.StringIO(text), sep=sep, encoding="latin-1")
    
    # Nettoyer les noms de colonnes
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    
    # ---- DÉTECTION DES COLONNES ----
    
    # Chercher la colonne de date
    date_col = None
    for candidate in ["date_de_tirage", "date", "date_tirage", "draw_date"]:
        if candidate in df.columns:
            date_col = candidate
            break
    
    if date_col is None:
        # Chercher une colonne qui contient des dates
        for col in df.columns:
            sample = str(df[col].iloc[0])
            if "/" in sample or "-" in sample:
                try:
                    pd.to_datetime(df[col].iloc[0], dayfirst=True)
                    date_col = col
                    break
                except Exception:
                    continue
    
    if date_col is None:
        st.error("❌ Impossible de trouver la colonne de date dans le CSV.")
        st.write("Colonnes détectées :", list(df.columns))
        return None
    
    # Chercher les colonnes de boules
    boule_cols = []
    for i in range(1, 8):
        for candidate in [f"boule_{i}", f"ball_{i}", f"numero_{i}", f"num_{i}", f"n{i}"]:
            if candidate in df.columns:
                boule_cols.append(candidate)
                break
    
    if len(boule_cols) < jeu["nb_boules"]:
        # Essayer de trouver par pattern
        for col in df.columns:
            if "boule" in col or "ball" in col or "numero" in col:
                if col not in boule_cols:
                    boule_cols.append(col)
        boule_cols = boule_cols[:jeu["nb_boules"]]
    
    if len(boule_cols) < jeu["nb_boules"]:
        st.error(f"❌ Impossible de trouver {jeu['nb_boules']} colonnes de boules.")
        st.write("Colonnes détectées :", list(df.columns))
        return None
    
    # Chercher les colonnes d'étoiles (Euromillions)
    etoile_cols = []
    if jeu["nb_etoiles"] > 0:
        for i in range(1, 4):
            for candidate in [f"etoile_{i}", f"star_{i}", f"étoile_{i}", f"lucky_star_{i}"]:
                if candidate in df.columns:
                    etoile_cols.append(candidate)
                    break
        etoile_cols = etoile_cols[:jeu["nb_etoiles"]]
    
    # ---- CONSTRUCTION DU DATAFRAME STANDARDISÉ ----
    
    result = pd.DataFrame()
    
    # Date
    try:
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True).dt.date
    except Exception:
        try:
            result["date"] = pd.to_datetime(df[date_col], format="%d/%m/%Y").dt.date
        except Exception:
            result["date"] = pd.to_datetime(df[date_col]).dt.date
    
    # Boules
    for i, col in enumerate(boule_cols[:jeu["nb_boules"]], 1):
        result[f"boule_{i}"] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    
    # Étoiles
    if etoile_cols and jeu["nb_etoiles"] > 0:
        for i, col in enumerate(etoile_cols[:jeu["nb_etoiles"]], 1):
            result[f"etoile_{i}"] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    
    # Nettoyage
    result = result.dropna(subset=[f"boule_{i}" for i in range(1, jeu["nb_boules"]+1)])
    result = result.sort_values("date", ascending=False).reset_index(drop=True)
    
    # Convertir en int classique
    for i in range(1, jeu["nb_boules"]+1):
        result[f"boule_{i}"] = result[f"boule_{i}"].astype(int)
    if jeu["nb_etoiles"] > 0:
        for i in range(1, jeu["nb_etoiles"]+1):
            if f"etoile_{i}" in result.columns:
                result[f"etoile_{i}"] = result[f"etoile_{i}"].astype(int)
    
    return result


def generer_historique_simule(jeu_id: str, nb_tirages: int = 500) -> pd.DataFrame:
    """
    Génère un historique simulé (fallback si pas de CSV).
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
            "date": (date_courante - timedelta(days=i * 3.5)).date(),
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
    return df.sort_values("date", ascending=False).reset_index(drop=True)


# ============================================================
# MOTEUR STATISTIQUE
# ============================================================

@st.cache_data
def calculer_stats(df: pd.DataFrame, jeu_id: str) -> dict:
    """
    Calcule toutes les statistiques pour chaque numéro.
    Fonctionne identiquement avec données réelles ou simulées.
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
            boules_tirage = [int(row[col]) for col in cols_boules]
            if numero in boules_tirage:
                break
            ecart += 1
        
        positions = []
        for idx, row in df.iterrows():
            boules_tirage = [int(row[col]) for col in cols_boules]
            if numero in boules_tirage:
                positions.append(idx)
        
        ecarts_historiques = []
        for i in range(len(positions) - 1):
            ecarts_historiques.append(positions[i + 1] - positions[i])
        
        ecart_moyen = np.mean(ecarts_historiques) if ecarts_historiques else 10
        ecart_max = max(ecarts_historiques) if ecarts_historiques else ecart
        derniere_sortie = None
        for idx, row in df.iterrows():
            boules_tirage = [int(row[col]) for col in cols_boules]
            if numero in boules_tirage:
                derniere_sortie = row["date"]
                break
        
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
            "indice_chaleur": round(indice_chaleur, 1),
            "derniere_sortie": derniere_sortie
        }
    
    # Étoiles
    stats_etoiles = {}
    if jeu["nb_etoiles"] > 0 and "etoile_1" in df.columns:
        cols_etoiles = [f"etoile_{i}" for i in range(1, jeu["nb_etoiles"]+1)]
        tous_etoiles = []
        for col in cols_etoiles:
            if col in df.columns:
                tous_etoiles.extend(df[col].tolist())
        
        etoiles_20 = []
        for col in cols_etoiles:
            if col in df.columns:
                etoiles_20.extend(df_20[col].tolist())
        
        etoiles_12m = []
        for col in cols_etoiles:
            if col in df.columns:
                etoiles_12m.extend(df_12m[col].tolist())
        
        freq_etoiles = Counter(tous_etoiles)
        freq_etoiles_20 = Counter(etoiles_20)
        freq_etoiles_12m = Counter(etoiles_12m)
        
        for numero in range(1, jeu["etoiles_max"] + 1):
            ecart = 0
            for idx, row in df.iterrows():
                etoiles_tirage = [int(row[col]) for col in cols_etoiles if col in df.columns]
                if numero in etoiles_tirage:
                    break
                ecart += 1
            
            forme_e = (freq_etoiles_20.get(numero, 0) / 20) * 100
            freq_th_e = (len(df_12m) * jeu["nb_etoiles"]) / jeu["etoiles_max"]
            freq_n_e = (freq_etoiles_12m.get(numero, 0) / max(freq_th_e, 1)) * 50
            ecart_p_e = max(0, 30 - (ecart * 2))
            chaleur_e = min(100, max(0, 0.40 * forme_e + 0.35 * freq_n_e + 0.25 * ecart_p_e))
            
            stats_etoiles[numero] = {
                "numero": numero,
                "ecart_actuel": ecart,
                "frequence_totale": freq_etoiles.get(numero, 0),
                "frequence_20t": freq_etoiles_20.get(numero, 0),
                "frequence_12m": freq_etoiles_12m.get(numero, 0),
                "indice_chaleur": round(chaleur_e, 1)
            }
    
    # Paires
    paires = Counter()
    for idx, row in df.iterrows():
        boules = sorted([int(row[col]) for col in cols_boules])
        for i in range(len(boules)):
            for j in range(i + 1, len(boules)):
                paires[(boules[i], boules[j])] += 1
    
    top_paires = paires.most_common(20)
    
    # Triplets (top 10)
    triplets = Counter()
    for idx, row in df.head(200).iterrows():  # Limiter pour performance
        boules = sorted([int(row[col]) for col in cols_boules])
        for i in range(len(boules)):
            for j in range(i+1, len(boules)):
                for k in range(j+1, len(boules)):
                    triplets[(boules[i], boules[j], boules[k])] += 1
    
    top_triplets = triplets.most_common(10)
    
    return {
        "boules": stats,
        "etoiles": stats_etoiles,
        "paires": top_paires,
        "triplets": top_triplets,
        "nb_tirages": len(df),
        "date_premier": df.iloc[-1]["date"] if len(df) > 0 else None,
        "date_dernier": df.iloc[0]["date"] if len(df) > 0 else None,
    }


# ============================================================
# SCORE DE ROBUSTESSE
# ============================================================

def score_robustesse(grille: list, etoiles: list, stats: dict, jeu_id: str) -> dict:
    jeu = JEUX[jeu_id]
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
    moyenne_theorique = jeu["nb_boules"] * (jeu["boules_max"] + 1) / 2
    z = abs(somme - moyenne_theorique) / 35
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
    
    # NOUVEAU : Bonus si la grille ne correspond à aucun tirage passé
    scores["🆕 Inédit"] = 0  # Placeholder, calculé si données réelles
    
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
    filtre_plafond: str = "aucun",
    max_tentatives: int = 1000
) -> dict:
    
    jeu = JEUX[jeu_id]
    
    for tentative in range(max_tentatives):
        # NIVEAU 1 : Pool de départ selon le mode
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
        
        # NIVEAU 2 : Filtres utilisateur
        
        # Filtre Plafond
        if filtre_plafond == "moins_40":
            pool = [n for n in pool if n < 40]
        elif filtre_plafond == "force_40":
            pass  # Géré après la génération
        
        # Chasseur d'écart
        if chasseur_ecart > 0:
            pool_filtre = [n for n in pool if stats["boules"][n]["ecart_actuel"] >= chasseur_ecart]
            if len(pool_filtre) >= jeu["nb_boules"]:
                pool = pool_filtre
        
        # Numéros forcés
        forces = list(numeros_forces or [])
        forces = [f for f in forces if 1 <= f <= jeu["boules_max"]]
        
        pool_disponible = [n for n in pool if n not in forces]
        nb_manquant = jeu["nb_boules"] - len(forces)
        
        if nb_manquant > len(pool_disponible):
            pool_disponible = [n for n in range(1, jeu["boules_max"] + 1) if n not in forces]
        
        if nb_manquant > 0:
            choisis = random.sample(pool_disponible, min(nb_manquant, len(pool_disponible)))
        else:
            choisis = []
        
        grille = sorted(forces + choisis)[:jeu["nb_boules"]]
        
        # Force > 40
        if filtre_plafond == "force_40":
            if not any(n >= 40 for n in grille):
                # Remplacer un numéro par un > 40
                nums_sup_40 = [n for n in range(40, jeu["boules_max"]+1) if n not in grille]
                if nums_sup_40:
                    # Remplacer le numéro avec le plus faible indice de chaleur
                    remplacer = min(grille, key=lambda x: stats["boules"][x]["indice_chaleur"] if x not in forces else 999)
                    if remplacer not in forces:
                        grille.remove(remplacer)
                        grille.append(random.choice(nums_sup_40))
                        grille = sorted(grille)
        
        # Étoiles
        etoiles = []
        if jeu["nb_etoiles"] > 0 and jeu["etoiles_max"]:
            for _ in range(100):
                etoiles = sorted(random.sample(range(1, jeu["etoiles_max"] + 1), jeu["nb_etoiles"]))
                if ecart_etoiles_min > 0 and len(etoiles) == 2:
                    if abs(etoiles[0] - etoiles[1]) >= ecart_etoiles_min:
                        break
                else:
                    break
        
        # NIVEAU 3 : Validation structurelle
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
            score = score_robustesse(grille, etoiles, stats, jeu_id)
            return {
                "grille": grille,
                "etoiles": etoiles,
                "score": score,
                "tentatives": tentative + 1,
                "mode": mode
            }
    
    # Fallback
    grille = sorted(random.sample(range(1, jeu["boules_max"] + 1), jeu["nb_boules"]))
    etoiles = sorted(random.sample(range(1, jeu["etoiles_max"] + 1), jeu["nb_etoiles"])) if jeu["nb_etoiles"] > 0 and jeu["etoiles_max"] else []
    score = score_robustesse(grille, etoiles, stats, jeu_id)
    return {"grille": grille, "etoiles": etoiles, "score": score, "tentatives": max_tentatives, "mode": "fallback"}


# ============================================================
# BACKTESTING
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
                    "date": str(tirage["date"]),
                    "grille": resultat["grille"],
                    "tirage": sorted(list(boules_tirage)),
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
# SYSTÈME RÉDUCTEUR
# ============================================================

def systeme_reducteur(numeros_choisis: list, taille_grille: int = 5) -> list:
    from itertools import combinations
    
    if len(numeros_choisis) <= taille_grille:
        return [sorted(numeros_choisis)]
    
    toutes_combs = list(combinations(numeros_choisis, taille_grille))
    random.shuffle(toutes_combs)
    
    grilles = []
    numeros_couverts = set()
    
    for comb in toutes_combs:
        comb_set = set(comb)
        nouveaux = comb_set - numeros_couverts
        
        if len(nouveaux) >= 1 or len(grilles) == 0:
            grilles.append(sorted(list(comb)))
            numeros_couverts |= comb_set
        
        if numeros_couverts == set(numeros_choisis) and len(grilles) >= 3:
            break
        if len(grilles) >= 12:
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
    
    jeu = JEUX[jeu_id]
    
    # ---- UPLOAD CSV ----
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📂 Source de données")
    
    uploaded_file = st.sidebar.file_uploader(
        f"📤 Importe ton CSV {jeu['nom']}",
        type=["csv", "txt"],
        help="Télécharge le CSV depuis le site FDJ : fdj.fr → Historique des tirages"
    )
    
    # Charger les données
    donnees_reelles = False
    
    if uploaded_file is not None:
        df = detecter_et_charger_csv(uploaded_file, jeu_id)
        if df is not None and len(df) > 0:
            donnees_reelles = True
            st.sidebar.markdown(
                f"<span class='data-badge-real'>✅ DONNÉES RÉELLES</span><br>"
                f"<small>{len(df)} tirages chargés<br>"
                f"Du {df.iloc[-1]['date']} au {df.iloc[0]['date']}</small>",
                unsafe_allow_html=True
            )
        else:
            st.sidebar.error("❌ Erreur de lecture CSV. Données simulées utilisées.")
            df = generer_historique_simule(jeu_id)
    else:
        df = generer_historique_simule(jeu_id)
        st.sidebar.markdown(
            "<span class='data-badge-simulated'>⚠️ DONNÉES SIMULÉES</span><br>"
            "<small>Importe un CSV FDJ pour<br>des résultats réels !</small>",
            unsafe_allow_html=True
        )
    
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.radio(
        "📑 Navigation",
        ["🏠 Dashboard", "🎯 Générateur", "📊 Statistiques",
         "🧪 Backtesting", "🧮 Réducteur", "📂 Données", "ℹ️ À propos"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='background:#fef3c7;padding:12px;border-radius:10px;"
        "border:1px solid #f59e0b;font-size:0.75rem;text-align:center;'>"
        "⚠️ Outil d'analyse statistique<br>"
        "Aucune garantie de gain<br><br>"
        "🛡️ <a href='https://www.joueurs-info-service.fr/'>Joueurs Info Service</a><br>"
        "09 74 75 13 13"
        "</div>",
        unsafe_allow_html=True
    )
    
    # Calculer les stats
    stats = calculer_stats(df, jeu_id)
    
    # Badge de source
    if donnees_reelles:
        badge = "🟢 Données réelles FDJ"
    else:
        badge = "🟡 Données simulées (démo)"
    
    # ================================================================
    # PAGE : DASHBOARD
    # ================================================================
    if page == "🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {badge} — {stats['nb_tirages']} tirages</div>",
                    unsafe_allow_html=True)
        
        if donnees_reelles:
            st.success(f"✅ Analyse basée sur {stats['nb_tirages']} tirages réels "
                      f"({stats['date_premier']} → {stats['date_dernier']})")
        
        # Dernier tirage
        dernier = df.iloc[0]
        cols_b = [f"boule_{i}" for i in range(1, 6)]
        boules_dernier = [int(dernier[c]) for c in cols_b]
        
        st.subheader(f"🎱 Dernier tirage — {dernier['date']}")
        
        boules_html = "<div class='grille-container'>"
        for b in boules_dernier:
            boules_html += f"<span class='boule'>{b}</span>"
        
        if jeu["nb_etoiles"] > 0 and "etoile_1" in df.columns:
            boules_html += "<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
            for i in range(1, jeu["nb_etoiles"]+1):
                if f"etoile_{i}" in dernier:
                    e = int(dernier[f"etoile_{i}"])
                    boules_html += f"<span class='etoile'>⭐{e}</span>"
        
        boules_html += "</div>"
        st.markdown(boules_html, unsafe_allow_html=True)
        
        # 5 derniers tirages
        st.subheader("📋 5 derniers tirages")
        derniers_5 = []
        for idx in range(min(5, len(df))):
            row = df.iloc[idx]
            tirage_str = f"{int(row['boule_1'])} - {int(row['boule_2'])} - {int(row['boule_3'])} - {int(row['boule_4'])} - {int(row['boule_5'])}"
            if jeu["nb_etoiles"] > 0 and "etoile_1" in df.columns:
                etoiles_str = f"⭐{int(row['etoile_1'])} ⭐{int(row['etoile_2'])}"
            else:
                etoiles_str = ""
            derniers_5.append({
                "📅 Date": str(row["date"]),
                "🎱 Boules": tirage_str,
                "⭐": etoiles_str
            })
        st.dataframe(pd.DataFrame(derniers_5), hide_index=True, use_container_width=True)
        
        st.markdown("---")
        
        # Métriques
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        chaud_top = max(stats["boules"].values(), key=lambda x: x["indice_chaleur"])
        froid_top = max(stats["boules"].values(), key=lambda x: x["ecart_actuel"])
        col_m1.metric("🔥 Plus chaud", f"N°{chaud_top['numero']}", f"Chaleur: {chaud_top['indice_chaleur']}")
        col_m2.metric("🧊 Plus absent", f"N°{froid_top['numero']}", f"Écart: {froid_top['ecart_actuel']}")
        col_m3.metric("📅 Tirages", f"{stats['nb_tirages']}")
        col_m4.metric("📊 Période", f"{stats['date_premier']} → {stats['date_dernier']}")
        
        st.markdown("---")
        
        # Top chauds / froids
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 Top 10 — En Forme")
            chauds = sorted(stats["boules"].values(), key=lambda x: x["indice_chaleur"], reverse=True)[:10]
            df_chauds = pd.DataFrame(chauds)[["numero", "indice_chaleur", "frequence_20t", "ecart_actuel"]]
            df_chauds.columns = ["N°", "🌡️ Chaleur", "Freq (20t)", "Écart"]
            st.dataframe(df_chauds, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("🧊 Top 10 — Grands Absents")
            froids = sorted(stats["boules"].values(), key=lambda x: x["ecart_actuel"], reverse=True)[:10]
            df_froids = pd.DataFrame(froids)[["numero", "ecart_actuel", "ecart_moyen", "ecart_max"]]
            df_froids.columns = ["N°", "Écart actuel", "Écart moyen", "Record"]
            st.dataframe(df_froids, hide_index=True, use_container_width=True)
        
        # Paires
        st.subheader("💑 Paires les plus fréquentes")
        paires_data = [{"Paire": f"{p[0][0]} — {p[0][1]}", "Fréquence": p[1]} for p in stats["paires"][:10]]
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.dataframe(pd.DataFrame(paires_data[:5]), hide_index=True, use_container_width=True)
        with col_p2:
            st.dataframe(pd.DataFrame(paires_data[5:10]), hide_index=True, use_container_width=True)
        
        # Triplets
        if stats["triplets"]:
            st.subheader("🔺 Triplets les plus fréquents")
            triplets_data = [{"Triplet": f"{t[0][0]} — {t[0][1]} — {t[0][2]}", "Fréquence": t[1]} for t in stats["triplets"][:6]]
            st.dataframe(pd.DataFrame(triplets_data), hide_index=True, use_container_width=True)
        
        # Étoiles
        if stats["etoiles"]:
            st.subheader("⭐ Étoiles — Situation")
            df_etoiles = pd.DataFrame([{
                "⭐": f"Étoile {s['numero']}",
                "🌡️ Chaleur": s.get("indice_chaleur", "—"),
                "Écart": s["ecart_actuel"],
                "Freq (20t)": s["frequence_20t"],
                "Freq 12m": s.get("frequence_12m", "—"),
            } for s in stats["etoiles"].values()])
            st.dataframe(df_etoiles, hide_index=True, use_container_width=True)
    
    # ================================================================
    # PAGE : GÉNÉRATEUR
    # ================================================================
    elif page == "🎯 Générateur":
        st.markdown("<div class='main-header'>🎯 Générateur de Grilles</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{badge}</div>", unsafe_allow_html=True)
        
        if donnees_reelles:
            st.success(f"✅ Grilles basées sur {stats['nb_tirages']} tirages réels !")
        else:
            st.warning("⚠️ Données simulées. Importe un CSV FDJ dans la sidebar pour des résultats réels.")
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("### 📌 Niveau 1 — Tendance")
            mode = st.selectbox("Mode", ["aleatoire", "chaud", "froid", "top", "hybride"],
                format_func=lambda x: {
                    "aleatoire": "🎲 Aléatoire",
                    "chaud": "🔥 En Forme (numéros chauds)",
                    "froid": "🧊 Peu Probable (grands absents)",
                    "top": "⭐ Top du Top (stars 12 mois)",
                    "hybride": "🧠 Hybride Intelligent"
                }[x])
            
            st.markdown("### 📌 Niveau 2 — Préférences")
            numeros_forces_input = st.text_input("🔒 Numéros forcés (max 3)", placeholder="Ex: 7, 14, 23")
            numeros_forces = []
            if numeros_forces_input:
                try:
                    numeros_forces = [int(n.strip()) for n in numeros_forces_input.split(",") if n.strip().isdigit()]
                    numeros_forces = [n for n in numeros_forces if 1 <= n <= jeu["boules_max"]][:3]
                    if numeros_forces:
                        st.success(f"Forcés : {numeros_forces}")
                except ValueError:
                    pass
            
            chasseur = st.slider("🎯 Chasseur d'écart", 0, 30, 0, help="Écart minimum requis")
            
            filtre_plafond = st.selectbox("🔝 Filtre Plafond", ["aucun", "moins_40", "force_40"],
                format_func=lambda x: {"aucun": "Aucun", "moins_40": "Uniquement < 40", "force_40": "Forcer au moins 1 numéro ≥ 40"}[x])
        
        with col_c2:
            st.markdown("### 📌 Niveau 3 — Filtres structurels")
            filtre_parite = st.checkbox("⚖️ Équilibre Parité", value=True)
            filtre_somme = st.checkbox("➕ Somme Gaussienne", value=True)
            filtre_dizaines = st.checkbox("📊 Répartition Dizaines", value=True)
            filtre_anti_suite = st.checkbox("🚫 Anti-suite", value=True)
            
            ecart_etoiles = 0
            if jeu["nb_etoiles"] > 0:
                ecart_etoiles = st.slider("⭐ Écart min étoiles", 0, 8, 2)
            
            nb_grilles = st.selectbox("Nombre de grilles", [1, 3, 5, 10], index=1)
        
        st.markdown("---")
        
        col_btn = st.columns([1, 2, 1])
        with col_btn[1]:
            go_btn = st.button("🎱 GÉNÉRER MES GRILLES", type="primary", use_container_width=True)
        
        if go_btn:
            st.markdown("---")
            
            toutes_grilles = []
            
            for g_idx in range(nb_grilles):
                resultat = generer_grille(
                    jeu_id=jeu_id, stats=stats, mode=mode,
                    filtre_parite=filtre_parite, filtre_somme=filtre_somme,
                    filtre_dizaines=filtre_dizaines, filtre_anti_suite=filtre_anti_suite,
                    chasseur_ecart=chasseur, numeros_forces=numeros_forces,
                    ecart_etoiles_min=ecart_etoiles, filtre_plafond=filtre_plafond
                )
                
                toutes_grilles.append(resultat)
                score = resultat["score"]
                grille = resultat["grille"]
                etoiles_gen = resultat["etoiles"]
                
                if score["total"] >= 80: etoiles_viz = "⭐⭐⭐⭐⭐"
                elif score["total"] >= 65: etoiles_viz = "⭐⭐⭐⭐"
                elif score["total"] >= 50: etoiles_viz = "⭐⭐⭐"
                elif score["total"] >= 35: etoiles_viz = "⭐⭐"
                else: etoiles_viz = "⭐"
                
                st.markdown(f"#### Grille {g_idx + 1} / {nb_grilles}")
                
                html = "<div class='grille-container'>"
                for b in grille:
                    chaleur_b = stats["boules"][b]["indice_chaleur"]
                    if chaleur_b >= 60:
                        bg = "linear-gradient(135deg, #dc2626, #ef4444)"
                    elif chaleur_b >= 40:
                        bg = "linear-gradient(135deg, #1e40af, #3b82f6)"
                    else:
                        bg = "linear-gradient(135deg, #1e3a5f, #475569)"
                    html += (f"<span style='background:{bg};color:white;border-radius:50%;"
                            f"width:65px;height:65px;display:inline-flex;align-items:center;"
                            f"justify-content:center;font-size:22px;font-weight:bold;"
                            f"margin:5px;box-shadow:0 4px 12px rgba(0,0,0,0.3);'>{b}</span>")
                
                if etoiles_gen:
                    html += "<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
                    for e in etoiles_gen:
                        html += f"<span class='etoile'>⭐{e}</span>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
                
                # Détail de chaque numéro
                detail_nums = []
                for b in grille:
                    s = stats["boules"][b]
                    detail_nums.append({
                        "N°": b,
                        "🌡️": s["indice_chaleur"],
                        "Écart": s["ecart_actuel"],
                        "Freq 20t": s["frequence_20t"],
                        "Dernière sortie": str(s.get("derniere_sortie", "—"))
                    })
                
                col_s1, col_s2 = st.columns([1, 2])
                
                with col_s1:
                    score_color = "#22c55e" if score["total"] >= 70 else ("#f59e0b" if score["total"] >= 50 else "#ef4444")
                    st.markdown(
                        f"<div style='text-align:center;padding:15px;'>"
                        f"<div style='font-size:3rem;font-weight:800;color:{score_color};'>{score['total']}</div>"
                        f"<div style='font-size:0.9rem;color:#64748b;'>/ 100</div>"
                        f"<div style='font-size:1.2rem;margin-top:5px;'>{etoiles_viz}</div>"
                        f"<div style='font-size:0.8rem;color:#94a3b8;margin-top:5px;'>"
                        f"Somme: {sum(grille)} | P: {sum(1 for n in grille if n%2==0)} I: {sum(1 for n in grille if n%2!=0)}</div>"
                        f"</div>", unsafe_allow_html=True)
                
                with col_s2:
                    max_pts = {"⚖️ Parité": 25, "📊 Dizaines": 20, "➕ Somme": 20,
                              "🔀 Diversité": 15, "🚫 Anti-suite": 10, "⭐ Étoiles": 10, "🆕 Inédit": 0}
                    for critere, pts in score["detail"].items():
                        mx = max_pts.get(critere, 10)
                        if mx == 0:
                            continue
                        pct = pts / mx
                        color = "#22c55e" if pct >= 0.7 else ("#f59e0b" if pct >= 0.4 else "#ef4444")
                        bar = "█" * int(pct * 12) + "░" * (12 - int(pct * 12))
                        st.markdown(f"<span style='font-family:monospace;'>{critere} <span style='color:{color};'>{bar}</span> **{pts}/{mx}**</span>", unsafe_allow_html=True)
                
                with st.expander(f"📋 Détail des numéros — Grille {g_idx+1}"):
                    st.dataframe(pd.DataFrame(detail_nums), hide_index=True, use_container_width=True)
                
                st.markdown("---")
            
            # Résumé mode mobile
            st.subheader("📱 Mode Buraliste (recopie rapide)")
            for i, r in enumerate(toutes_grilles):
                g_str = " — ".join([str(n) for n in r["grille"]])
                e_str = ""
                if r["etoiles"]:
                    e_str = "  |  ⭐ " + " — ".join([str(e) for e in r["etoiles"]])
                st.markdown(
                    f"<div style='text-align:center;font-size:28px;font-weight:bold;"
                    f"padding:15px;background:#f8fafc;border-radius:12px;margin:8px 0;'>"
                    f"G{i+1} : {g_str}{e_str}</div>", unsafe_allow_html=True)
    
    # ================================================================
    # PAGE : STATISTIQUES
    # ================================================================
    elif page == "📊 Statistiques":
        st.markdown("<div class='main-header'>📊 Statistiques Complètes</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {badge} — {stats['nb_tirages']} tirages</div>", unsafe_allow_html=True)
        
        # Heatmap
        st.subheader("🌡️ Carte de Chaleur")
        nb_cols_h = 10
        nb_rows_h = (jeu["boules_max"] + nb_cols_h - 1) // nb_cols_h
        
        z_data, text_data = [], []
        for row in range(nb_rows_h):
            z_row, t_row = [], []
            for col in range(nb_cols_h):
                num = row * nb_cols_h + col + 1
                if num <= jeu["boules_max"]:
                    s = stats["boules"][num]
                    z_row.append(s["indice_chaleur"])
                    t_row.append(f"N°{num}<br>🌡️ Chaleur: {s['indice_chaleur']}<br>"
                                f"Écart: {s['ecart_actuel']}<br>Freq 20t: {s['frequence_20t']}<br>"
                                f"Freq 12m: {s['frequence_12m']}")
                else:
                    z_row.append(None)
                    t_row.append("")
            z_data.append(z_row)
            text_data.append(t_row)
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=z_data, text=text_data, hoverinfo="text",
            colorscale=[[0, "#1e3a5f"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            showscale=True, colorbar=dict(title="Chaleur")))
        for row in range(nb_rows_h):
            for col in range(nb_cols_h):
                num = row * nb_cols_h + col + 1
                if num <= jeu["boules_max"]:
                    fig_heat.add_annotation(x=col, y=row, text=str(num), showarrow=False,
                        font=dict(color="white", size=14, family="Arial Black"))
        fig_heat.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20),
                              xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Écarts
        st.subheader("📈 Écarts actuels vs Moyenne historique")
        ecart_data = [(n, stats["boules"][n]["ecart_actuel"], stats["boules"][n]["ecart_moyen"])
                      for n in range(1, jeu["boules_max"]+1)]
        
        fig_ecarts = go.Figure()
        fig_ecarts.add_trace(go.Bar(x=[d[0] for d in ecart_data], y=[d[1] for d in ecart_data],
            name="Écart actuel",
            marker_color=["#ef4444" if d[1] > d[2]*1.5 else ("#f59e0b" if d[1] > d[2] else "#3b82f6") for d in ecart_data]))
        fig_ecarts.add_trace(go.Scatter(x=[d[0] for d in ecart_data], y=[d[2] for d in ecart_data],
            name="Écart moyen", mode="lines", line=dict(color="#22c55e", width=2, dash="dash")))
        fig_ecarts.update_layout(height=350, xaxis_title="Numéro", yaxis_title="Tirages",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig_ecarts, use_container_width=True)
        
        if donnees_reelles:
            st.info("🟢 Ces statistiques sont calculées à partir de vrais tirages FDJ.")
        
        # Fréquences
        st.subheader("📊 Fréquences (20 derniers tirages)")
        freq_data = [(n, stats["boules"][n]["frequence_20t"]) for n in range(1, jeu["boules_max"]+1)]
        freq_data.sort(key=lambda x: x[1], reverse=True)
        fig_freq = go.Figure(go.Bar(x=[str(f[0]) for f in freq_data], y=[f[1] for f in freq_data],
            marker_color=["#22c55e" if f[1] >= 3 else ("#f59e0b" if f[1] >= 2 else "#94a3b8") for f in freq_data]))
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
            "Freq totale": stats["boules"][n]["frequence_totale"],
        } for n in range(1, jeu["boules_max"]+1)])
        df_complet = df_complet.sort_values(tri, ascending=(tri == "Écart"))
        st.dataframe(df_complet, hide_index=True, use_container_width=True, height=500)
    
    # ================================================================
    # PAGE : BACKTESTING
    # ================================================================
    elif page == "🧪 Backtesting":
        st.markdown("<div class='main-header'>🧪 Backtesting</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>Teste ta stratégie sur l'historique — {badge}</div>", unsafe_allow_html=True)
        
        if donnees_reelles:
            st.success("✅ Backtesting sur données RÉELLES — Résultats significatifs !")
        else:
            st.warning("⚠️ Backtesting sur données simulées — Importe un CSV pour des résultats réels.")
        
        col_bt1, col_bt2 = st.columns(2)
        with col_bt1:
            mode_bt = st.selectbox("Stratégie", ["aleatoire", "chaud", "froid", "top", "hybride"],
                format_func=lambda x: {"aleatoire": "🎲 Aléatoire", "chaud": "🔥 En Forme",
                    "froid": "🧊 Peu Probable", "top": "⭐ Top du Top", "hybride": "🧠 Hybride"}[x])
        with col_bt2:
            nb_bt = st.selectbox("Tirages à tester", [20, 50, 100, 200, 500], index=1)
            grilles_bt = st.selectbox("Grilles par tirage", [1, 3, 5], index=0)
        
        if st.button("🚀 LANCER LE BACKTEST", type="primary", use_container_width=True):
            with st.spinner("⏳ Simulation en cours..."):
                res_bt = mini_backtest(df, jeu_id, stats, mode_bt, nb_bt, grilles_bt)
            
            st.markdown("---")
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            col_r1.metric("🎟️ Grilles jouées", res_bt['nb_grilles'])
            col_r2.metric("💰 Misé", f"{res_bt['total_mise']:.2f} €")
            col_r3.metric("🏆 Gagné", f"{res_bt['total_gains']:.2f} €")
            bilan = res_bt['bilan']
            col_r4.metric("📈 Bilan", f"{bilan:+.2f} €", delta_color="normal" if bilan >= 0 else "inverse")
            
            res = res_bt["resultats"]
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_bt = go.Figure(go.Bar(
                    x=[f"{k} bons" for k in sorted(res.keys())],
                    y=[res[k] for k in sorted(res.keys())],
                    marker_color=["#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e", "#15803d"],
                    text=[res[k] for k in sorted(res.keys())], textposition="auto"))
                fig_bt.update_layout(height=300, title="Correspondances")
                st.plotly_chart(fig_bt, use_container_width=True)
            with col_g2:
                df_res = pd.DataFrame([{"Résultat": f"{k}/5", "Fois": v,
                    "%": f"{v/res_bt['nb_grilles']*100:.1f}%"} for k, v in sorted(res.items(), reverse=True)])
                st.dataframe(df_res, hide_index=True, use_container_width=True)
            
            if res_bt["historique"]:
                st.subheader("🎯 Meilleures correspondances trouvées")
                for h in res_bt["historique"][:10]:
                    st.markdown(f"📅 **{h['date']}** — Grille: `{h['grille']}` vs Tirage: `{h['tirage']}` — **{h['bons']} bons** — {h['gain']}€")
            
            st.info("⚠️ Performances passées ≠ résultats futurs.")
    
    # ================================================================
    # PAGE : RÉDUCTEUR
    # ================================================================
    elif page == "🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Système Réducteur</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Sélectionne plus de numéros, génère des grilles optimales</div>", unsafe_allow_html=True)
        
        st.markdown("""
        **Mode d'emploi :**
        1. Sélectionne **6 à 15 numéros** que tu penses prometteurs
        2. Le système génère des grilles diversifiées automatiquement
        3. La couverture maximale est assurée
        """)
        
        # Aide : suggestion basée sur les stats
        with st.expander("💡 Suggestions basées sur les stats"):
            top_chaleur = sorted(stats["boules"].values(), key=lambda x: x["indice_chaleur"], reverse=True)[:10]
            suggestion = ", ".join([str(n["numero"]) for n in top_chaleur])
            st.markdown(f"**Top 10 chaleur :** `{suggestion}`")
            
            top_ecart = sorted(stats["boules"].values(), key=lambda x: x["ecart_actuel"], reverse=True)[:5]
            suggestion_froid = ", ".join([str(n["numero"]) for n in top_ecart])
            st.markdown(f"**Top 5 écart :** `{suggestion_froid}`")
        
        nums_input = st.text_input("🔢 Tes numéros", placeholder="Ex: 3, 7, 14, 19, 23, 28, 34, 41")
        
        if nums_input:
            try:
                nums = sorted(set([int(n.strip()) for n in nums_input.split(",") if n.strip().isdigit() and 1 <= int(n.strip()) <= jeu["boules_max"]]))
                
                if len(nums) < 6:
                    st.warning(f"⚠️ Sélectionne au moins 6 numéros ({len(nums)} actuellement)")
                elif len(nums) > 15:
                    st.warning("⚠️ Max 15. Les premiers 15 sont gardés.")
                    nums = nums[:15]
                else:
                    st.success(f"✅ {len(nums)} numéros : {nums}")
                    
                    if st.button("🧮 GÉNÉRER", type="primary", use_container_width=True):
                        grilles_r = systeme_reducteur(nums)
                        
                        st.subheader(f"📋 {len(grilles_r)} grilles générées")
                        cout = len(grilles_r) * jeu["prix"]
                        st.info(f"💰 Coût : {len(grilles_r)} × {jeu['prix']}€ = **{cout:.2f}€**")
                        
                        for i, gr in enumerate(grilles_r):
                            et_r = sorted(random.sample(range(1, jeu["etoiles_max"]+1), jeu["nb_etoiles"])) if jeu["nb_etoiles"] > 0 and jeu["etoiles_max"] else []
                            sc_r = score_robustesse(gr, et_r, stats, jeu_id)
                            
                            html_r = f"<div class='grille-container'><strong>G{i+1}</strong>&nbsp;&nbsp;"
                            for b in gr:
                                html_r += f"<span class='boule'>{b}</span>"
                            if et_r:
                                html_r += "<span style='margin:0 10px;color:#94a3b8;'>|</span>"
                                for e in et_r:
                                    html_r += f"<span class='etoile'>⭐{e}</span>"
                            html_r += f"&nbsp;&nbsp;<span style='color:#64748b;'>Score: {sc_r['total']}/100</span></div>"
                            st.markdown(html_r, unsafe_allow_html=True)
                        
                        st.subheader("📊 Couverture")
                        couv = {n: sum(1 for g in grilles_r if n in g) for n in nums}
                        df_couv = pd.DataFrame([{"N°": n, "Dans": f"{c}/{len(grilles_r)} grilles",
                            "%": f"{c/len(grilles_r)*100:.0f}%"} for n, c in couv.items()])
                        st.dataframe(df_couv, hide_index=True, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur : {e}")
    
    # ================================================================
    # PAGE : DONNÉES
    # ================================================================
    elif page == "📂 Données":
        st.markdown("<div class='main-header'>📂 Gestion des Données</div>", unsafe_allow_html=True)
        
        st.markdown("""
        ## Comment obtenir les données réelles
        
        ### Euromillions
        1. Va sur **[fdj.fr](https://www.fdj.fr/jeux-de-tirage/euromillions-my-million/historique)**
        2. Clique sur **"Historique"** ou **"Télécharger"**
        3. Télécharge le fichier CSV
        4. Importe-le via la sidebar ← à gauche
        
        ### Loto
        1. Va sur **[fdj.fr](https://www.fdj.fr/jeux-de-tirage/loto/historique)**
        2. Même procédure
        
        ### Formats acceptés
        """)
        
        st.code("""
# Format FDJ classique (séparateur ;)
annee_numero_de_tirage;jour_de_tirage;date_de_tirage;boule_1;boule_2;boule_3;boule_4;boule_5;etoile_1;etoile_2
2025/010;mardi;04/02/2025;6;14;20;27;44;3;7
2025/009;vendredi;31/01/2025;2;10;23;38;50;2;11

# Format alternatif (séparateur ,)
date,boule_1,boule_2,boule_3,boule_4,boule_5,etoile_1,etoile_2
2025-02-04,6,14,20,27,44,3,7
        """, language="csv")
        
        st.markdown("---")
        st.subheader("📊 Données actuellement chargées")
        
        if donnees_reelles:
            st.success(f"✅ **DONNÉES RÉELLES** — {len(df)} tirages")
        else:
            st.warning(f"⚠️ **DONNÉES SIMULÉES** — {len(df)} tirages générés aléatoirement")
        
        col_d1, col_d2, col_d3 = st.columns(3)
        col_d1.metric("Tirages", len(df))
        col_d2.metric("Premier", str(df.iloc[-1]["date"]))
        col_d3.metric("Dernier", str(df.iloc[0]["date"]))
        
        st.subheader("👀 Aperçu des données")
        st.dataframe(df.head(20), use_container_width=True)
        
        st.subheader("📋 Colonnes détectées")
        st.write(list(df.columns))
        
        # Option pour créer un CSV manuellement
        st.markdown("---")
        st.subheader("✏️ Ou crée ton CSV manuellement")
        st.markdown("Si tu n'arrives pas à télécharger le CSV FDJ, tu peux copier-coller les tirages ici :")
        
        csv_manuel = st.text_area(
            "Colle tes tirages (format : date;boule_1;boule_2;boule_3;boule_4;boule_5;etoile_1;etoile_2)",
            placeholder="04/02/2025;6;14;20;27;44;3;7\n31/01/2025;2;10;23;38;50;2;11",
            height=200
        )
        
        if csv_manuel and st.button("📥 Charger ces tirages"):
            try:
                header = "date_de_tirage;boule_1;boule_2;boule_3;boule_4;boule_5"
                if jeu["nb_etoiles"] > 0:
                    header += ";etoile_1;etoile_2"
                csv_complet = header + "\n" + csv_manuel
                
                temp_file = io.BytesIO(csv_complet.encode("utf-8"))
                df_manuel = detecter_et_charger_csv(temp_file, jeu_id)
                
                if df_manuel is not None and len(df_manuel) > 0:
                    st.success(f"✅ {len(df_manuel)} tirages chargés avec succès !")
                    st.dataframe(df_manuel.head(10), use_container_width=True)
                    st.info("💡 Pour utiliser ces données, sauvegarde-les en fichier CSV et importe-le via la sidebar.")
                else:
                    st.error("❌ Format non reconnu.")
            except Exception as e:
                st.error(f"Erreur : {e}")
    
    # ================================================================
    # PAGE : À PROPOS
    # ================================================================
    elif page == "ℹ️ À propos":
        st.markdown("<div class='main-header'>ℹ️ À propos</div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        ## 🎱 Smart-Loto — Prototype V2.0
        
        ### ✅ Nouveautés V2
        
        | Fonctionnalité | Statut |
        |---|---|
        | 📂 **Import CSV réel FDJ** | ✅ NOUVEAU |
        | 🏠 Dashboard (5 derniers tirages) | ✅ |
        | 🎯 Générateur (5 modes + 7 filtres) | ✅ |
        | 📊 Statistiques (heatmap, écarts, fréquences) | ✅ |
        | 🧪 Backtesting | ✅ |
        | 🧮 Système Réducteur | ✅ |
        | 🔺 Triplets fréquents | ✅ NOUVEAU |
        | 🎨 Boules colorées selon chaleur | ✅ NOUVEAU |
        | 📱 Mode buraliste | ✅ NOUVEAU |
        | 📋 Détail par numéro dans grille | ✅ NOUVEAU |
        | 🔝 Filtre Plafond (<40 / >40) | ✅ NOUVEAU |
        | ✏️ Saisie manuelle de tirages | ✅ NOUVEAU |
        
        ### Source des données : **{badge}**
        - Tirages chargés : **{stats['nb_tirages']}**
        - Période : **{stats['date_premier']}** → **{stats['date_dernier']}**
        
        ### ⚠️ Avertissements
        - Outil d'analyse statistique, **pas de prédiction**
        - **Aucune garantie de gain**
        - Chaque tirage est un **événement indépendant**
        
        ### 🛡️ Jeu Responsable
        **Joueurs Info Service : 09 74 75 13 13**
        """)
    
    # Footer
    st.markdown(
        "<div class='footer-disclaimer'>"
        "⚠️ Outil d'analyse statistique — Aucune garantie de gain — "
        "Les loteries sont des jeux de hasard<br>"
        "🛡️ <a href='https://www.joueurs-info-service.fr/'>Joueurs Info Service</a> : 09 74 75 13 13"
        "</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
