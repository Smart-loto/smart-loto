# ============================================================
# SMART-LOTO — VERSION 6.1 — OPTIMISÉE & MODULAIRE
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from datetime import datetime, timedelta
import plotly.graph_objects as go
import io

# Configuration globale de l'interface
st.set_page_config(
    page_title="Smart-Loto V6.1", 
    page_icon="🎱", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Injection des styles CSS personnalisés
st.markdown("""
<style>
    .main-header {font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#1e40af,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;padding:10px 0;}
    .sub-header {text-align:center;color:#475569 !important;font-size:1.1rem;margin-bottom:30px;}
    .boule {background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff !important;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(30,64,175,0.4);}
    .etoile {background:linear-gradient(135deg,#f59e0b,#fbbf24);color:#fff !important;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(245,158,11,0.4);}
    .grille-container {display:flex;align-items:center;justify-content:center;padding:25px;background:linear-gradient(135deg,#f8fafc,#e2e8f0);border-radius:20px;margin:15px 0;border:2px solid #e2e8f0;color:#1e293b !important;}
    .grille-container b,.grille-container strong{color:#1e293b !important;}
    .footer-disclaimer {background:#fef3c7;border:1px solid #f59e0b;border-radius:12px;padding:15px;margin-top:30px;text-align:center;font-size:0.9rem;color:#92400e !important;}
    .footer-disclaimer a{color:#b45309 !important;text-decoration:underline;}
    .alert-card {background:linear-gradient(135deg,#fef2f2,#fee2e2);border:2px solid #ef4444;border-radius:16px;padding:20px;margin:10px 0;color:#991b1b !important;}
    .alert-card b,.alert-card strong{color:#7f1d1d !important;}
    .success-card {background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:2px solid #22c55e;border-radius:16px;padding:20px;margin:10px 0;color:#166534 !important;}
    .success-card b,.success-card strong{color:#14532d !important;}
    .insight-card {background:linear-gradient(135deg,#eff6ff,#dbeafe);border:2px solid #3b82f6;border-radius:16px;padding:20px;margin:10px 0;color:#1e3a5f !important;}
    .insight-card b,.insight-card strong,.insight-card span{color:#1e3a5f !important;}
    .reco-card {background:linear-gradient(135deg,#fdf4ff,#f3e8ff);border:2px solid #a855f7;border-radius:16px;padding:20px;margin:10px 0;color:#581c87 !important;}
    .reco-card b,.reco-card strong,.reco-card span{color:#581c87 !important;}
    .buraliste-card {text-align:center;font-size:28px;font-weight:bold;padding:15px;background:#f8fafc;border-radius:12px;margin:8px 0;color:#1e293b !important;border:1px solid #e2e8f0;}
    .score-big{text-align:center;}
    .score-big .score-number{font-size:3rem;font-weight:800;}
    .score-big .score-label{color:#64748b !important;font-size:0.9rem;}
    .preset-card {background:linear-gradient(135deg,#f8fafc,#e2e8f0);border:2px solid #cbd5e1;border-radius:16px;padding:20px;margin:10px 0;color:#1e293b !important;cursor:pointer;transition:all 0.2s;}
    .preset-card:hover {border-color:#3b82f6;box-shadow:0 4px 12px rgba(59,130,246,0.2);}
    .preset-card b,.preset-card strong{color:#1e293b !important;}
    .element-container div[data-testid="stMarkdownContainer"] > div{color:#1e293b;}
    .glossary-term {background:#f1f5f9;border:1px solid #cbd5e1;border-radius:8px;padding:12px;margin:6px 0;color:#1e293b !important;}
    .glossary-term b{color:#1e40af !important;}
</style>
""", unsafe_allow_html=True)

# Jeux de données et constantes
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
        "somme_max": 160
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
        "somme_max": 180
    }
}

GLOSSAIRE = {
    "Chaleur (🌡️)": "Score pondéré évaluant la récurrence à court terme d'un numéro.",
    "Écart (Éc.)": "Nombre de tirages consécutifs s'étant écoulés depuis la dernière apparition du numéro.",
    "Écart moyen (Moy)": "Intervalle moyen théorique séparant deux apparitions successives d'un numéro.",
    "Écart max (Max)": "La plus longue période d'absence enregistrée pour un numéro donné.",
    "F20": "Fréquence d'apparition mesurée sur la fenêtre des 20 derniers tirages.",
    "F12m": "Nombre total de sorties d'un numéro sur la période glissante des 12 derniers mois.",
    "F3m": "Nombre total de sorties d'un numéro sur la période glissante des 3 derniers mois.",
    "Probabilité (P%)": "Indice d'écart standardisé (Z-Score) converti en pourcentage.",
    "Tendance (📈)": "Indicateur de dynamique d'un numéro (Trimestre vs Année).",
    "Retard (⏳)": "Différence calculée entre l'écart moyen historique d'un numéro et son écart actuel.",
    "Parité": "Distribution relative entre les numéros pairs et impairs d'une grille.",
    "Somme": "Sommation mathématique des 5 numéros de la grille.",
    "Dizaines": "Répartition spatiale des numéros par blocs de dizaines (1-10, 11-20...).",
    "Terminaisons": "Analyse du dernier chiffre des numéros pour éviter les redondances.",
    "Entropie de Shannon": "Mesure mathématique de la répartition des écarts internes de la grille pour éviter les motifs trop réguliers ou prévisibles.",
    "Modèle de Popularité": "Estimation de l'attractivité humaine des numéros (dates de naissance, numéros fétiches) pour optimiser les rapports de gain.",
    "Système réducteur": "Algorithme combinatoire optimisant la sélection pour couvrir des garanties de gains.",
    "Backtest & Monte-Carlo": "Simulation historique et empirique évaluant le rendement d'une méthode de sélection sur un grand nombre d'itérations.",
    "Espérance": "Calcul du rendement moyen théorique espéré pour chaque grille jouée."
}

PROFILS = {
    "🎯 Équilibré": {
        "desc": "Le compromis standard. Distribution optimisée, combinant numéros chauds et froids.",
        "mode": "optimal", "fp": True, "fs": True, "fd": True, "fa": True, "ft": False, "fb": True,
        "plafond": "aucun", "pw_ch": 50, "pw_ec": 50, "pw_pr": 50
    },
    "🔥 Agressif": {
        "desc": "Privilégie les numéros qui présentent les plus fortes récurrences à court terme.",
        "mode": "chaud", "fp": True, "fs": True, "fd": True, "fa": True, "ft": False, "fb": False,
        "plafond": "aucun", "pw_ch": 80, "pw_ec": 20, "pw_pr": 50
    },
    "🧊 Chasseur": {
        "desc": "Cible prioritairement les numéros accusant les retards théoriques les plus prononcés.",
        "mode": "retard", "fp": True, "fs": True, "fd": True, "fa": True, "ft": False, "fb": False,
        "plafond": "aucun", "pw_ch": 20, "pw_ec": 80, "pw_pr": 50
    },
    "📊 Statisticien": {
        "desc": "Algorithme basé sur la probabilité d'écart estimée.",
        "mode": "probabiliste", "fp": True, "fs": True, "fd": True, "fa": True, "ft": True, "fb": True,
        "plafond": "aucun", "pw_ch": 40, "pw_ec": 40, "pw_pr": 80
    },
    "🚫 Anti-Populaire": {
        "desc": "Filtre limitant les numéros bas pour optimiser les gains en cas de victoire partagée.",
        "mode": "optimal", "fp": True, "fs": True, "fd": True, "fa": True, "ft": True, "fb": True,
        "plafond": "force_40", "pw_ch": 50, "pw_ec": 50, "pw_pr": 50
    },
    "🎲 Chance Pure": {
        "desc": "Génération aléatoire uniforme sans application de filtres structurels.",
        "mode": "aleatoire", "fp": False, "fs": False, "fd": False, "fa": False, "ft": False, "fb": False,
        "plafond": "aucun", "pw_ch": 50, "pw_ec": 50, "pw_pr": 50
    }
}

# ============================================================
# FONCTIONS DE BASE DE THÉORIE DE L'INFORMATION & POPULARITÉ
# ============================================================
def calc_shannon_entropy(gr, max_val=50):
    """Calcule l'entropie de Shannon basée sur les espaces d'écarts relatifs dans la grille."""
    g = sorted(list(gr))
    gaps = [g[0]]
    for i in range(1, len(g)):
        gaps.append(g[i] - g[i-1])
    gaps.append((max_val + 1) - g[-1])
    
    total = sum(gaps)
    entropy = 0.0
    for gap in gaps:
        if gap > 0:
            p = gap / total
            entropy -= p * np.log2(p)
    return float(entropy)

def get_popularity_profile(gr):
    """Estime un score de popularité moyen pour la grille (les grilles très jouées ont un score élevé)."""
    score_pop = 0.0
    for n in gr:
        p = 1.0
        if n <= 31:
            p += 0.8  # Effet anniversaire (dates de naissance)
        if n in [7, 13, 11, 21]:
            p += 0.4  # Chiffres porte-bonheur et fétiches récurrents
        if n > 40:
            p -= 0.3  # Zone moins sélectionnée par le grand public
        score_pop += p
    return round(score_pop / len(gr), 2)

# ============================================================
# SYSTÈME DE GESTION DES DONNÉES (CSV & SIMULATION DYNAMIQUE)
# ============================================================
def load_csv(up, jid):
    jeu = JEUX[jid]
    dbg = {}
    content = up.read()
    up.seek(0)
    text = None
    
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            text = content.decode(enc)
            dbg["enc"] = enc
            break
        except Exception:
            continue
            
    if not text:
        return None, {"err": "Impossible de décoder le fichier."}
        
    text = text.lstrip("\ufeff")
    df = None
    
    for s in [";", ",", "\t"]:
        try:
            d = pd.read_csv(io.StringIO(text), sep=s, engine="python")
            d = d.loc[:, ~d.columns.str.match(r'^Unnamed')]
            d.columns = [c.strip() for c in d.columns]
            if len(d.columns) >= 7 and (df is None or len(d.columns) > len(df.columns)):
                df = d
        except Exception:
            pass
            
    if df is None or len(df.columns) < 7:
        return None, {"err": "Format de colonnes insuffisant."}
        
    cl = {c.upper(): c for c in df.columns}
    dc = None
    for c in ["DATE", "date", "DATE_DE_TIRAGE"]:
        if c in df.columns:
            dc = c
            break
        elif c.upper() in cl:
            dc = cl[c.upper()]
            break
            
    if not dc:
        for c in df.columns:
            if "date" in c.lower():
                dc = c
                break
                
    if not dc:
        return None, {"err": "Colonne de date introuvable."}
        
    bc = []
    for i in range(1, 6):
        for c in [f"N{i}", f"n{i}", f"BOULE_{i}", f"boule_{i}"]:
            if c in df.columns:
                bc.append(c)
                break
            elif c.upper() in cl:
                bc.append(cl[c.upper()])
                break
                
    if len(bc) < 5:
        bc = []
        for c in df.columns:
            if c == dc:
                continue
            try:
                v = pd.to_numeric(df[c], errors="coerce").dropna()
                if len(v) > len(df) * 0.3 and v.min() >= 1 and v.max() <= jeu["boules_max"]:
                    bc.append(c)
                if len(bc) >= 5:
                    break
            except Exception:
                continue
                
    if len(bc) < 5:
        return None, {"err": f"Nombre de colonnes de boules détectées insuffisant : {len(bc)}/5"}
        
    ec = []
    if jeu["nb_etoiles"] > 0:
        for i in range(1, 3):
            for c in [f"E{i}", f"e{i}", f"ETOILE_{i}", f"etoile_{i}"]:
                if c in df.columns:
                    ec.append(c)
                    break
                elif c.upper() in cl:
                    ec.append(cl[c.upper()])
                    break
                    
    r = pd.DataFrame()
    for fmt in [None, "%d/%m/%Y", "%Y-%m-%d"]:
        try:
            if fmt:
                r["date"] = pd.to_datetime(df[dc], format=fmt, errors="coerce").dt.date
            else:
                r["date"] = pd.to_datetime(df[dc], dayfirst=True, errors="coerce").dt.date
            if r["date"].notna().sum() > len(df) * 0.5:
                break
        except Exception:
            continue
            
    for i, c in enumerate(bc[:5], 1):
        r[f"boule_{i}"] = pd.to_numeric(df[c], errors="coerce")
    for i, c in enumerate(ec[:2], 1):
        r[f"etoile_{i}"] = pd.to_numeric(df[c], errors="coerce")
        
    try:
        r["jour"] = pd.to_datetime(r["date"]).dt.day_name()
        jm = {"Monday": "lundi", "Tuesday": "mardi", "Wednesday": "mercredi", "Friday": "vendredi", "Saturday": "samedi"}
        r["jour"] = r["jour"].map(lambda x: jm.get(x, x))
    except Exception:
        r["jour"] = "?"
        
    try:
        r["mois"] = pd.to_datetime(r["date"]).dt.month
    except Exception:
        r["mois"] = 0
        
    r = r.dropna(subset=["date", "boule_1", "boule_2", "boule_3", "boule_4", "boule_5"])
    for i in range(1, 6):
        r[f"boule_{i}"] = r[f"boule_{i}"].astype(int)
    for i in range(1, 3):
        if f"etoile_{i}" in r.columns:
            r[f"etoile_{i}"] = r[f"etoile_{i}"].fillna(0).astype(int)
            
    for i in range(1, 6):
        r = r[(r[f"boule_{i}"] >= 1) & (r[f"boule_{i}"] <= jeu["boules_max"])]
        
    r = r.sort_values("date", ascending=False).drop_duplicates("date").reset_index(drop=True)
    dbg["ok"] = len(r) > 0
    dbg["n"] = len(r)
    dbg["map"] = {"d": dc, "b": bc[:5], "e": ec[:2]}
    return r, dbg

def gen_simul(jid, nb=500):
    """Générateur de simulation dynamique sans graine fixe"""
    jeu = JEUX[jid]
    t = []
    now = datetime.now()
    js = ["mardi", "vendredi"] if jid == "euromillions" else ["lundi", "mercredi", "samedi"]
    for i in range(nb):
        b = sorted(random.sample(range(1, jeu["boules_max"] + 1), 5))
        e = sorted(random.sample(range(1, jeu["etoiles_max"] + 1), 2)) if jeu["etoiles_max"] else []
        d = {
            "date": (now - timedelta(days=i * 3.5)).date(),
            "boule_1": b[0], "boule_2": b[1], "boule_3": b[2], "boule_4": b[3], "boule_5": b[4],
            "jour": js[i % len(js)], "mois": (now - timedelta(days=i * 3.5)).month
        }
        if e:
            d["etoile_1"] = e[0]
            d["etoile_2"] = e[1]
        t.append(d)
    return pd.DataFrame(t).sort_values("date", ascending=False).reset_index(drop=True)

# ============================================================
# MOTEUR STATISTIQUE VECTORISÉ
# ============================================================
@st.cache_data
def calc_stats_vectorized(df_json, jid, jf=None):
    df = pd.read_json(io.StringIO(df_json))
    df["date"] = pd.to_datetime(df["date"]).dt.date
    if jf and jf != "tous" and "jour" in df.columns:
        df = df[df["jour"].str.lower() == jf.lower()].reset_index(drop=True)
        
    jeu = JEUX[jid]
    n_tirages = len(df)
    max_boules = jeu["boules_max"]
    
    cols_boules = [f"boule_{i}" for i in range(1, 6)]
    draws_matrix = df[cols_boules].to_numpy(dtype=int)
    
    occurrences = np.zeros((n_tirages, max_boules), dtype=bool)
    for i in range(5):
        occurrences[np.arange(n_tirages), draws_matrix[:, i] - 1] = True
        
    ecarts_actuels = np.argmax(occurrences, axis=0)
    jamais_sorti = ~occurrences.any(axis=0)
    ecarts_actuels[jamais_sorti] = n_tirages
    
    stats_boules = {}
    for num in range(1, max_boules + 1):
        idx_num = num - 1
        sorties_indices = np.where(occurrences[:, idx_num])[0]
        freq_tot = len(sorties_indices)
        f20 = np.sum(occurrences[:20, idx_num])
        f12m = np.sum(occurrences[:100, idx_num])
        f3m = np.sum(occurrences[:25, idx_num])
        
        if freq_tot > 1:
            intervalles = np.diff(sorties_indices)
            em = np.mean(intervalles)
            ex = np.max(intervalles)
            es = np.std(intervalles) if len(intervalles) > 1 else 5.0
        else:
            em = n_tirages / 5.0
            ex = n_tirages
            es = 5.0
            
        ec_actuel = ecarts_actuels[idx_num]
        zz = (ec_actuel - em) / max(es, 1.0)
        pb = min(99.0, max(1.0, 50.0 + zz * 15.0))
        td = "↗️" if f3m > (f12m - f3m) * 1.3 else ("↘️" if f3m < (f12m - f3m) * 0.7 else "→")
        
        dn = "—"
        if freq_tot > 0:
            dn = str(df.iloc[sorties_indices[0]]["date"])
            
        stats_boules[num] = {
            "numero": num,
            "ecart": int(ec_actuel),
            "ecart_moy": round(float(em), 1),
            "ecart_max": int(ex),
            "freq_tot": int(freq_tot),
            "f20": int(f20),
            "f12m": int(f12m),
            "f3m": int(f3m),
            "chaleur": round(float(min(100.0, max(0.0, (f20 * 4) + (f12m * 0.5) + (30 - ec_actuel * 1.5)))), 1),
            "ratio_rec": round(float((ec_actuel / ex * 100) if ex > 0 else 0), 1),
            "proba": round(float(pb), 1),
            "tend": td,
            "term": num % 10,
            "diz": (num - 1) // 10,
            "retard": max(0, round(em - ec_actuel)),
            "dern": dn
        }
        
    se = {}
    if jeu["nb_etoiles"] and "etoile_1" in df.columns:
        ce = [f"etoile_{i}" for i in range(1, jeu["nb_etoiles"] + 1)]
        for n in range(1, jeu["etoiles_max"] + 1):
            ec = 0
            for _, r in df.iterrows():
                if n in [int(r[c]) for c in ce if c in df.columns]:
                    break
                ec += 1
            se[n] = {"numero": n, "ecart": ec, "freq_tot": 0, "f20": 0}
            
    sums = draws_matrix.sum(axis=1)
    pairs_counts = (draws_matrix % 2 == 0).sum(axis=1)
    bas_counts = (draws_matrix <= (max_boules // 2)).sum(axis=1)
    
    terms = draws_matrix % 10
    terms_diff = np.array([len(np.unique(r)) for r in terms])
    dizs = (draws_mat
