# ============================================================
# SMART-LOTO — VERSION 6.3.1 — STABLE
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
    page_title="Smart-Loto V6.3.1", 
    page_icon="🎱", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Injection des styles CSS sécurisés
st.markdown("""
<style>
    .main-header {font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#1e40af,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;padding:10px 0;}
    .sub-header {text-align:center;color:#475569 !important;font-size:1.1rem;margin-bottom:30px;}
    .boule {background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff !important;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(30,64,175,0.4);}
    .etoile {background:linear-gradient(135deg,#f59e0b,#fbbf24);color:#fff !important;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(245,158,11,0.4);}
    .grille-container {display:flex;align-items:center;justify-content:center;padding:25px;background:linear-gradient(135deg,#f8fafc,#e2e8f0);border-radius:20px;margin:15px 0;border:2px solid #e2e8f0;color:#1e293b !important;}
    .grille-container b, .grille-container strong {color:#1e293b !important;}
    .footer-disclaimer {background:#fef3c7;border:1px solid #f59e0b;border-radius:12px;padding:15px;margin-top:30px;text-align:center;font-size:0.9rem;color:#92400e !important;}
    .footer-disclaimer a {color:#b45309 !important;text-decoration:underline;}
    .insight-card {background:linear-gradient(135deg,#eff6ff,#dbeafe);border:2px solid #3b82f6;border-radius:16px;padding:20px;margin:10px 0;color:#1e3a5f !important;}
    .reco-card {background:linear-gradient(135deg,#fdf4ff,#f3e8ff);border:2px solid #a855f7;border-radius:16px;padding:20px;margin:10px 0;color:#581c87 !important;}
    .score-big {text-align:center;}
    .score-big .score-number {font-size:3rem;font-weight:800;}
    .score-big .score-label {color:#64748b !important;font-size:0.9rem;}
    .glossary-term {background:#f1f5f9;border:1px solid #cbd5e1;border-radius:8px;padding:12px;margin:6px 0;color:#1e293b !important;}
    .glossary-term b {color:#1e40af !important;}
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
    "Entropie de Shannon": "Mesure mathématique de la répartition des écarts internes de la grille pour éviter les motifs trop réguliers.",
    "Modèle Sabermétrique": "Pondération théorique de la valeur du ticket en fonction de la densité attendue des autres joueurs pour maximiser les gains non partagés.",
    "Test de Wald-Wolfowitz": "Test non paramétrique d'indépendance statistique (Runs Test) visant à vérifier l'absence de biais sur la machine de tirage.",
    "Prospect Theory": "Théorie de Kahneman et Tversky modélisant la perception subjective de l'utilité du ticket face au risque.",
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
# UTILITIES & MATHEMATICAL HELPER FUNCTIONS (DEFINED FIRST)
# ============================================================
def calc_shannon_entropy(gr, max_val=50):
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
    score_pop = 0.0
    for n in gr:
        p = 1.0
        if n <= 31:
            p += 0.8
        if n in [7, 13, 11, 21]:
            p += 0.4
        if n > 40:
            p -= 0.3
        score_pop += p
    return round(score_pop / len(gr), 2)

def calc_sabermetric_efficiency_from_pop(pop_score):
    """Calcule l'efficacité sabermétrique d'un ticket (0-100%) à partir de son score de popularité."""
    # L'indice de popularité oscille généralement entre 0.7 et 2.2
    efficiency = (2.2 - pop_score) / (2.2 - 0.7) * 100.0
    return max(0.0, min(100.0, float(efficiency)))

def normal_cdf(x):
    return 0.5 * (1.0 + np.sign(x) * np.sqrt(1.0 - np.exp(-2.0 * x * x / np.pi)))

def audit_wald_wolfowitz(sequence):
    n = len(sequence)
    if n < 15:
        return 0.0, 1.0
    
    median = np.median(sequence)
    binarized = np.array([1 if x >= median else 0 for x in sequence])
    
    runs = 1
    for i in range(1, n):
        if binarized[i] != binarized[i-1]:
            runs += 1
            
    n1 = int(np.sum(binarized == 1))
    n2 = int(np.sum(binarized == 0))
    
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0
        
    mu = ((2.0 * n1 * n2) / n) + 1.0
    var = (2.0 * n1 * n2 * (2.0 * n1 * n2 - n)) / (n * n * (n - 1.0))
    
    if var <= 0:
        return 0.0, 1.0
        
    sigma = np.sqrt(var)
    z = (runs - mu) / sigma
    p_val = 2.0 * (1.0 - normal_cdf(abs(z)))
    return float(z), float(p_val)

def calc_prospect_utility(jackpot_m, prix_ticket, pr_gagner):
    alpha = 0.88
    beta = 0.88
    lambda_val = 2.25
    gamma = 0.61
    
    gain = jackpot_m * 1_000_000.0
    p = pr_gagner
    
    numerator = p ** gamma
    denominator = (numerator + ((1.0 - p) ** gamma)) ** (1.0 / gamma)
    pi_p = numerator / denominator
    
    u_gains = pi_p * (gain ** alpha)
    u_pertes = -lambda_val * (prix_ticket ** beta)
    u_nette = u_gains + u_pertes
    
    return float(u_nette), float(pi_p)

# ============================================================
# DATA MANAGEMENT FUNCTIONS
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
# MOTEUR STATISTIQUE VECTORISÉ DIRECT
# ============================================================
@st.cache_data
def calc_stats_vectorized(df, jid, jf=None):
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
        freq_tot = int(len(sorties_indices))
        f20 = int(np.sum(occurrences[:20, idx_num]))
        f12m = int(np.sum(occurrences[:100, idx_num]))
        f3m = int(np.sum(occurrences[:25, idx_num]))
        
        if freq_tot > 1:
            intervalles = np.diff(sorties_indices)
            em = float(np.mean(intervalles))
            ex = int(np.max(intervalles))
            es = float(np.std(intervalles)) if len(intervalles) > 1 else 5.0
        else:
            em = float(n_tirages / 5.0)
            ex = int(n_tirages)
            es = 5.0
            
        ec_actuel = int(ecarts_actuels[idx_num])
        zz = (ec_actuel - em) / max(es, 1.0)
        pb = min(99.0, max(1.0, 50.0 + zz * 15.0))
        td = "↗️" if f3m > (f12m - f3m) * 1.3 else ("↘️" if f3m < (f12m - f3m) * 0.7 else "→")
        
        dn = "—"
        if freq_tot > 0:
            dn = str(df.iloc[sorties_indices[0]]["date"])
            
        stats_boules[num] = {
            "numero": num,
            "ecart": ec_actuel,
            "ecart_moy": round(em, 1),
            "ecart_max": ex,
            "freq_tot": freq_tot,
            "f20": f20,
            "f12m": f12m,
            "f3m": f3m,
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
    
    dizs = (draws_matrix - 1) // 10
    diz_diff = np.array([len(np.unique(r)) for r in dizs])
    
    po = {
        "somme_moy": float(sums.mean()),
        "somme_q1": float(np.percentile(sums, 25)),
        "somme_q3": float(np.percentile(sums, 75)),
        "pairs_moy": float(pairs_counts.mean()),
        "bas_moy": float(bas_counts.mean()),
        "terms_moy": float(terms_diff.mean()),
        "diz_moy": float(diz_diff.mean())
    }
    
    paires = Counter()
    for row in draws_matrix:
        bs = sorted(row)
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                paires[(bs[i], bs[j])] += 1
                
    return {
        "boules": stats_boules, 
        "etoiles": se, 
        "paires": paires.most_common(30),
        "profil": po, 
        "nb_tirages": n_tirages,
        "date_1": str(df.iloc[-1]["date"]) if len(df) > 0 else "—",
        "date_n": str(df.iloc[0]["date"]) if len(df) > 0 else "—"
    }

# ============================================================
# SCORE DE QUALITÉ COHÉRENT V6.1 (ENTROPIE ET POPULARITÉ)
# ============================================================
def score_v6_1(gr, et, st_, jid):
    jeu = JEUX[jid]
    sc = {}
    po = st_.get("profil", {})
    
    # 1. Parité (10 pts)
    np2 = sum(1 for n in gr if n % 2 == 0)
    sc["⚖️ Parité"] = 10 if abs(np2 - po.get("pairs_moy", 2.5)) <= 0.5 else (7 if abs(np2 - po.get("pairs_moy", 2.5)) <= 1.5 else 3)
    
    # 2. Dizaines (10 pts)
    dz = Counter((n - 1) // 10 for n in gr)
    sc["📊 Dizaines"] = 10 if len(dz) >= round(po.get("diz_moy", 4)) else (7 if len(dz) >= round(po.get("diz_moy", 4)) - 1 else 3)
    
    # 3. Somme (10 pts)
    s = sum(gr)
    q1, q3 = po.get("somme_q1", 90), po.get("somme_q3", 160)
    sc["➕ Somme"] = 10 if q1 <= s <= q3 else (7 if jeu["somme_min"] <= s <= jeu["somme_max"] else 2)
    
    # 4. Diversité (10 pts)
    ecs = [st_["boules"][n]["ecart"] for n in gr if n in st_["boules"]]
    sc["🔀 Diversité"] = (10 if float(np.std(ecs)) > 5 else (7 if float(np.std(ecs)) > 3 else 3)) if len(set(ecs)) > 1 else 3
    
    # 5. Absence de Suite (8 pts)
    g = sorted(gr)
    hs = any(g[i+1] == g[i] + 1 and g[i+2] == g[i] + 2 for i in range(len(g) - 2))
    sc["🚫 Suite"] = 2 if hs else 8
    
    # 6. Étoiles (8 pts)
    if et and len(et) == 2:
        e = abs(et[0] - et[1])
        sc["⭐ Étoiles"] = 8 if e >= 3 else (5 if e >= 2 else 2)
    else:
        sc["⭐ Étoiles"] = 8
        
    # 7. Terminaisons (8 pts)
    terms = set(n % 10 for n in gr)
    sc["🔢 Terms"] = 8 if len(terms) >= round(po.get("terms_moy", 4)) else (5 if len(terms) >= round(po.get("terms_moy", 4)) - 1 else 2)
    
    # 8. Bas / Hauts (8 pts)
    nb_bas = sum(1 for n in gr if n <= jeu["boules_max"] // 2)
    sc["⬆️⬇️ B/H"] = 8 if abs(nb_bas - po.get("bas_moy", 2.5)) <= 0.5 else (5 if abs(nb_bas - po.get("bas_moy", 2.5)) <= 1.5 else 2)
    
    # 9. Chaleur (8 pts)
    chs = [st_["boules"][n]["chaleur"] for n in gr if n in st_["boules"]]
    mc = np.mean(chs) if chs else 50
    sc["🌡️ Chaleur"] = 8 if 35 <= mc <= 65 else (5 if 20 <= mc <= 80 else 2)
    
    # 10. Probabilité théorique (8 pts)
    pbs = [st_["boules"][n]["proba"] for n in gr if n in st_["boules"]]
    mp = np.mean(pbs) if pbs else 50
    sc["📊 Proba"] = 8 if mp >= 55 else (5 if mp >= 45 else 2)

    # 11. Entropie de Shannon (12 pts)
    ent = calc_shannon_entropy(gr, jeu["boules_max"])
    sc["🌀 Entropie"] = 12 if 2.1 <= ent <= 2.55 else (8 if 1.8 <= ent < 2.1 else 3)
    
    return {"total": sum(sc.values()), "detail": sc, "max": 100}

# ============================================================
# GÉNÉRATEUR CONSTRUCTIF AVEC FILTRES SCIENTIFIQUES
# ============================================================
def gen_grille_constructive(jid, st_, mode="aleatoire", fp=False, fs=False, fd=False, fa=False,
                            chasseur=0, forces=None, ee=0, plafond="aucun",
                            f_term=False, f_bh=False, pw_ch=50, pw_ec=50, pw_pr=50):
    jeu = JEUX[jid]
    max_boules = jeu["boules_max"]
    fo = [f for f in (forces or []) if 1 <= f <= max_boules][:3]
    
    candidats = list(range(1, max_boules + 1))
    poids = []
    for n in candidats:
        s = st_["boules"][n]
        if mode == "chaud":
            w = s["chaleur"] ** 1.5 + 1
        elif mode == "retard":
            w = s["retard"] ** 1.5 + 1
        elif mode == "probabiliste":
            w = s["proba"] ** 1.5 + 1
        elif mode == "optimal":
            score_opt = (pw_ch / 100) * s["chaleur"] + (pw_ec / 100) * min(100, s["ecart"] * 8) + (pw_pr / 100) * s["proba"]
            p_pop = get_popularity_profile([n])
            if plafond == "force_40":
                w = score_opt ** 1.5 * (1 / p_pop) + 1
            else:
                w = score_opt ** 1.5 + 1
        else:
            w = 1.0
        poids.append(w)
        
    poids = np.array(poids)
    poids /= poids.sum()
    
    pool = candidats.copy()
    if plafond == "moins_40":
        pool = [n for n in pool if n < 40]
    elif plafond == "force_40":
        pool = [n for n in pool if n >= 35]
    if chasseur > 0:
        pool = [n for n in pool if st_["boules"][n]["ecart"] >= chasseur]
    if not pool:
        pool = candidats.copy()
        
    grille = set(fo)
    essais = 0
    
    while len(grille) < 5 and essais < 200:
        essais += 1
        indices_possibles = [i for i, n in enumerate(candidats) if n in pool and n not in grille]
        if not indices_possibles:
            break
        p_slice = poids[indices_possibles]
        p_slice /= p_slice.sum()
        choix = np.random.choice(indices_possibles, p=p_slice)
        num_candidat = candidats[choix]
        
        valide = True
        temp_grille = list(grille) + [num_candidat]
        
        if fp:
            np_count = sum(1 for n in temp_grille if n % 2 == 0)
            if len(temp_grille) == 5 and (np_count == 0 or np_count == 5):
                valide = False
        if fd:
            dz = Counter((n - 1) // 10 for n in temp_grille)
            if max(dz.values()) > 3:
                valide = False
        if fa and len(temp_grille) >= 3:
            g_sorted = sorted(temp_grille)
            if any(g_sorted[i+1] == g_sorted[i]+1 and g_sorted[i+2] == g_sorted[i]+2 for i in range(len(g_sorted)-2)):
                valide = False
        if f_term:
            if len(temp_grille) == 5 and len(set(n % 10 for n in temp_grille)) < 4:
                valide = False
                
        if valide:
            grille.add(num_candidat)
            
    while len(grille) < 5:
        restants = [n for n in candidats if n not in grille]
        if not restants:
            break
        grille.add(random.choice(restants))
        
    grille = sorted(list(grille))
    
    etoiles = []
    if jeu["nb_etoiles"] and jeu["etoiles_max"]:
        for _ in range(50):
            etoiles = sorted(random.sample(range(1, jeu["etoiles_max"] + 1), jeu["nb_etoiles"]))
            if ee > 0 and abs(etoiles[0] - etoiles[1]) >= ee:
                break
                
    return {
        "grille": grille, 
        "etoiles": etoiles, 
        "score": score_v6_1(grille, etoiles, st_, jid), 
        "mode": mode
    }

# ============================================================
# RÉDUCTEUR D'ÉCART OPTIMISÉ (NP-HARD HEURISTIC)
# ============================================================
def reducteur_mathematique(numeros_selectionnes: list, t_garantie: int = 3) -> list:
    v = sorted(list(set(numeros_selectionnes)))
    if len(v) < 5:
        return [v]
        
    from itertools import combinations
    sous_combinaisons_a_couvrir = set(combinations(v, t_garantie))
    
    grilles_retenues = []
    max_grilles = 15
    
    while sous_combinaisons_a_couvrir and len(grilles_retenues) < max_grilles:
        meilleure_grille = None
        max_couverts = -1
        combinaisons_candidates = list(combinations(v, 5))
        
        if len(combinaisons_candidates) > 1000:
            combinaisons_candidates = random.sample(combinaisons_candidates, 1000)
            
        for candidate in combinaisons_candidates:
            c_set = set(candidate)
            internes = set(c for c in sous_combinaisons_a_couvrir if set(c).issubset(c_set))
            if len(internes) > max_couverts:
                max_couverts = len(internes)
                meilleure_grille = candidate
                meilleures_combis = internes
                
        if meilleure_grille is None or max_couverts == 0:
            break
            
        grilles_retenues.append(sorted(list(meilleure_grille)))
        sous_combinaisons_a_couvrir -= meilleures_combis
        
    if sous_combinaisons_a_couvrir and len(grilles_retenues) < max_grilles:
        restant = list(sous_combinaisons_a_couvrir)[0]
        comblement = sorted(list(set(restant) | set(v[:5]))[:5])
        grilles_retenues.append(comblement)
        
    return grilles_retenues

# ============================================================
# COMPOSANTS D'AFFICHAGE & MOTEURS DE SIMULATIONS (BACKTEST / MC)
# ============================================================
def backtest(df, jid, st_, mode, nt=50):
    jeu = JEUX[jid]
    res = {str(i): 0 for i in range(6)}
    tm = 0
    tg = 0
    gt = {0: 0, 1: 0, 2: 0, 3: 4, 4: 50, 5: 5000}
    hi = []
    C = [f"boule_{i}" for i in range(1, 6)]
    
    for idx in range(min(nt, len(df))):
        row = df.iloc[idx]
        bt = set(int(row[c]) for c in C)
        r = gen_grille_constructive(jid, st_, mode=mode)
        nb = len(set(r["grille"]) & bt)
        res[str(nb)] += 1
        tm += jeu["prix"]
        g = gt.get(nb, 0)
        tg += g
        if nb >= 3:
            hi.append({"date": str(row["date"]), "grille": r["grille"], "tirage": sorted(bt), "bons": nb, "gain": g})
            
    return {
        "res": res, 
        "slate_mise": tm,
        "mise": round(tm, 2), 
        "gains": round(tg, 2), 
        "bilan": round(tg - tm, 2), 
        "nb": nt, 
        "hi": hi
    }

def simulate_monte_carlo(jid, st_, mode, n_simulations=2000):
    jeu = JEUX[jid]
    res = {str(i): 0 for i in range(6)}
    tm = n_simulations * jeu["prix"]
    tg = 0
    gt = {0: 0, 1: 0, 2: 2.2, 3: 10, 4: 120, 5: 25000}
    
    r = gen_grille_constructive(jid, st_, mode=mode)
    ma_grille = set(r["grille"])
    
    for _ in range(n_simulations):
        tirage_virtuel = set(random.sample(range(1, jeu["boules_max"] + 1), 5))
        nb = len(ma_grille & tirage_virtuel)
        res[str(nb)] += 1
        tg += gt.get(nb, 0)
        
    return {
        "res": res,
        "mise": round(tm, 2),
        "gains": round(tg, 2),
        "bilan": round(tg - tm, 2),
        "nb": n_simulations
    }

def html_gr(gr, et, st_, jid):
    h = "<div class='grille-container'>"
    for b in gr:
        ch = st_["boules"][b]["chaleur"]
        bg = "linear-gradient(135deg,#dc2626,#ef4444)" if ch >= 60 else ("linear-gradient(135deg,#1e40af,#3b82f6)" if ch >= 40 else "linear-gradient(135deg,#1e3a5f,#475569)")
        h += f"<span style='background:{bg};color:#fff;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(0,0,0,0.3);'>{b}</span>"
    if et:
        h += "<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
        for e in et:
            h += f"<span class='etoile'>⭐ {e}</span>"
    h += "</div>"
    return h

def show_sc(sc, entropy_val, pop_score):
    ev = "⭐" * max(1, min(5, (sc["total"] - 20) // 15 + 1))
    cc = "#22c55e" if sc["total"] >= 70 else ("#f59e0b" if sc["total"] >= 50 else "#ef4444")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"<div class='score-big'><div class='score-number' style='color:{cc};'>{sc['total']}</div><div class='score-label'>/ {sc['max']} {ev}</div></div>", unsafe_allow_html=True)
        st.write(f"🌀 **Entropie** : `{entropy_val:.3f}` *(cible : 2.1 - 2.5)*")
        
        # Résolution sécurisée de l'Efficacité Sabermétrique sans NameError
        eff_val = calc_sabermetric_efficiency_from_pop(pop_score)
        st.write(f"👥 **Efficacité Sabermétrique** : `{eff_val:.1f}%` *(évitement du partage du jackpot)*")
    with c2:
        mx = {"⚖️ Parité": 10, "📊 Dizaines": 10, "➕ Somme": 10, "🔀 Diversité": 10, "🚫 Suite": 8, "⭐ Étoiles": 8, "🔢 Terms": 8, "⬆️⬇️ B/H": 8, "🌡️ Chaleur": 8, "📊 Proba": 8, "🌀 Entropie": 12}
        for cr, pt in sc["detail"].items():
            m = mx.get(cr, 8)
            pct = pt / m if m else 0
            cl = "#22c55e" if pct >= .7 else ("#f59e0b" if pct >= .4 else "#ef4444")
            bar = "█" * int(pct * 10) + "░" * (10 - int(pct * 10))
            st.markdown(f"<span style='font-size:.85rem;color:#1e293b;'><code>{cr}</code> <span style='color:{cl};font-family:monospace;'>{bar}</span> **{pt}/{m}**</span>", unsafe_allow_html=True)

def auto_sug(st_, jid):
    jeu = JEUX[jid]
    rc = []
    nh = sum(1 for s in st_["boules"].values() if s["tend"] == "↗️")
    if nh > jeu["boules_max"] * 0.25:
        rc.append({"m": "tendance", "r": f"{nh} numéros en hausse", "c": 80})
    nr = sum(1 for s in st_["boules"].values() if s["ratio_rec"] >= 80)
    if nr >= 5:
        rc.append({"m": "retard", "r": f"{nr} numéros approchant leur record", "c": 75})
    mp = np.mean([s["proba"] for s in st_["boules"].values()])
    if mp > 55:
        rc.append({"m": "probabiliste", "r": f"Probabilité d'écart moyenne élevée ({mp:.1f}%)", "c": 70})
    rc.append({"m": "optimal", "r": "Configuration optimale équilibrée", "c": 70})
    rc.sort(key=lambda x: x["c"], reverse=True)
    return rc

# ============================================================
# POINT D'ENTRÉE DE L'APPLICATION
# ============================================================
def main():
    st.sidebar.markdown("<div style='text-align:center;'><h1 style='font-size:2rem;color:#1e293b;'>🎱 Smart-Loto</h1><p style='color:#64748b;'>V6.3.1 — Intelligence Distribuée</p></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    jid = st.sidebar.selectbox("🎮 Jeu", ["euromillions", "loto"], format_func=lambda x: f"{JEUX[x]['emoji']} {JEUX[x]['nom']}")
    jeu = JEUX[jid]
    
    st.sidebar.markdown("---")
    up = st.sidebar.file_uploader("📤 CSV Officiel FDJ", type=["csv", "txt"])
    
    reel = False
    if up:
        df, dbg = load_csv(up, jid)
        if df is not None and len(df) > 0:
            reel = True
            st.sidebar.success(f"✅ {len(df)} tirages synchronisés")
        else:
            st.sidebar.error("❌ Format non reconnu.")
            df = gen_simul(jid)
    else:
        df = gen_simul(jid)
        st.sidebar.info("💡 Utilisation de données simulées de test")
        
    if "gg" not in st.session_state:
        st.session_state.gg = []
        
    st.sidebar.markdown("---")
    page = st.sidebar.radio("📑 Menu", [
        "🏠 Dashboard",
        "🎱 Générer (Simple)",
        "🎯 Générer (Expert)",
        "📊 Statistiques",
        "📱 Vérifier mes grilles",
        "💎 Quand jouer ?",
        "📖 Glossaire",
        "🧪 Backtest",
        "🧮 Réducteur",
        "🏆 Mes grilles",
        "🔍 Debug"
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ Aucune garantie mathématique de gain")
    st.sidebar.caption("🛡️ Joueurs Info Service : 09 74 75 13 13")
    
    stats = calc_stats_vectorized(df, jid)
    bdg = "🟢 Données réelles" if reel else "🟡 Données simulées"

    # 1. PAGE DASHBOARD
    if page == "🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {bdg} — {stats['nb_tirages']} tirages analysés</div>", unsafe_allow_html=True)
        
        d = df.iloc[0]
        bs = [int(d[f"boule_{i}"]) for i in range(1, 6)]
        et_d = [int(d[f"etoile_{i}"]) for i in range(1, jeu["nb_etoiles"] + 1)] if jeu["nb_etoiles"] and "etoile_1" in df.columns else []
        
        st.subheader(f"🎱 Dernier tirage enregistré — {d['date']}")
        st.markdown(html_gr(bs, et_d, stats, jid), unsafe_allow_html=True)
        
        seq_auditee = df[[f"boule_{i}" for i in range(1, 6)]].to_numpy().flatten()
        z_score, p_val = audit_wald_wolfowitz(seq_auditee[:500])
        
        st.subheader("🛡️ Rapport d'Audit de Hasard (Wald-Wolfowitz)")
        if p_val > 0.05:
            st.success(f"✅ Indépendance validée (p-value = {p_val:.4f}). Les données d'historique ne révèlent aucun biais de tirage physique.")
        else:
            st.warning(f"⚠️ Déviation mineure détectée (p-value = {p_val:.4f}). Motif de tirage potentiellement non uniforme.")
        
        rc = auto_sug(stats, jid)
        if rc:
            b = rc[0]
            st.markdown(f"<div class='reco-card'>🔮 <b>Recommandation dynamique :</b> Profil conseillé <b>{b['m'].upper()}</b> — {b['r']} (Confiance {b['c']}%)</div>", unsafe_allow_html=True)

    # 2. PAGE GÉNÉRER SIMPLE
    elif page == "🎱 Générer (Simple)":
        st.markdown("<div class='main-header'>🎱 Générateur Assisté</div>", unsafe_allow_html=True)
        st.subheader("1️⃣ Sélectionnez votre profil de jeu")
        
        profil_choisi = st.radio("Style de jeu :", list(PROFILS.keys()), horizontal=True)
        p = PROFILS[profil_choisi]
        st.markdown(f"<div class='insight-card'>💡 <b>{profil_choisi}</b> : {p['desc']}</div>", unsafe_allow_html=True)
        
        st.subheader("2️⃣ Options de volume")
        c1, c2 = st.columns(2)
        with c1:
            nbg = st.selectbox("Nombre de grilles souhaité", [1, 3, 5, 10], index=1)
            fi = st.text_input("🔒 Inclure des numéros fétiches (max 3, séparés par des virgules)")
            
            forces = []
            if fi:
                for n in fi.split(","):
                    n_clean = n.strip()
                    if n_clean.isdigit():
                        val = int(n_clean)
                        if 1 <= val <= jeu["boules_max"]:
                            forces.append(val)
                forces = forces[:3]
                
        with c2:
            ee = st.slider("⭐ Écart requis entre les étoiles", 0, 8, 2) if jeu["nb_etoiles"] else 0
            
        if st.button("🎱 GÉNÉRER LES COMBINAISONS", type="primary", use_container_width=True):
            ag = []
            for gi in range(nbg):
                r = gen_grille_constructive(
                    jid, stats, p["mode"], fp=p["fp"], fs=p["fs"], fd=p["fd"], fa=p["fa"],
                    chasseur=0, forces=forces, ee=ee, plafond=p["plafond"],
                    f_term=p["ft"], f_bh=p["fb"]
                )
                ag.append(r)
                st.markdown(f"#### Grille {gi + 1}")
                st.markdown(html_gr(r["grille"], r["etoiles"], stats, jid), unsafe_allow_html=True)
                
                sc = r["score"]
                ent_val = calc_shannon_entropy(r["grille"], jeu["boules_max"])
                pop_val = get_popularity_profile(r["grille"])
                eff_val = calc_sabermetric_efficiency_from_pop(pop_val)
                cc = "#22c55e" if sc["total"] >= 70 else ("#f59e0b" if sc["total"] >= 50 else "#ef4444")
                
                st.markdown(f"<div style='border-left: 5px solid {cc}; padding-left: 10px; margin-bottom:15px;'>Score de conformité structurelle : <b>{sc['total']}/100</b> | Entropie : <b>{ent_val:.2f}</b> | Efficacité Sabermétrique : <b>{eff_val:.1f}%</b></div>", unsafe_allow_html=True)
                st.markdown("---")
                
            st.session_state.gg.extend([{"g": r["grille"], "e": r["etoiles"], "s": r["score"]["total"], "m": profil_choisi, "t": datetime.now().strftime("%H:%M")} for r in ag])

    # 3. PAGE GÉNÉRER EXPERT
    elif page == "🎯 Générer (Expert)":
        st.markdown("<div class='main-header'>🎯 Configuration Avancée</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 🎯 Choix de Pondération")
            mode = st.selectbox("Algorithme de base", ["aleatoire", "chaud", "retard", "probabiliste", "optimal"])
            pw_ch, pw_ec, pw_pr = 50, 50, 50
            if mode == "optimal":
                pw_ch = st.slider("🌡️ Poids de la chaleur", 0, 100, 50)
                pw_ec = st.slider("📏 Poids de l'écart", 0, 100, 50)
                pw_pr = st.slider("📊 Poids de la probabilité", 0, 100, 50)
        with c2:
            st.markdown("### 🔧 Paramètres Physiques")
            fi = st.text_input("Numéros requis (max 3)")
            
            forces = []
            if fi:
                for n in fi.split(","):
                    n_clean = n.strip()
                    if n_clean.isdigit():
                        val = int(n_clean)
                        if 1 <= val <= jeu["boules_max"]:
                            forces.append(val)
                forces = forces[:3]
                
            plafond = st.selectbox("Limitateur de popularité (Plafond)", ["aucun", "moins_40", "force_40"])
            ee = st.slider("Écart min étoiles", 0, 8, 2) if jeu["nb_etoiles"] else 0
            nbg = st.selectbox("Nombre de grilles", [1, 3, 5, 10], index=1)
        with c3:
            st.markdown("### 🛡️ Filtres de Structure")
            fpa = st.checkbox("Éviter les parités extrêmes (5/0 ou 0/5)", True)
            fdi = st.checkbox("Limiter à 3 numéros max par dizaine", True)
            fan = st.checkbox("Interdire les suites de 3 numéros", True)
            ftm = st.checkbox("Vérifier les terminaisons", False)
            
        if st.button("🎯 CALCULER LA GRILLE", type="primary", use_container_width=True):
            ag = []
            for gi in range(nbg):
                r = gen_grille_constructive(
                    jid, stats, mode, fp=fpa, fs=True, fd=fdi, fa=fan,
                    chasseur=0, forces=forces, ee=ee, plafond=plafond,
                    f_term=ftm, f_bh=False, pw_ch=pw_ch, pw_ec=pw_ec, pw_pr=pw_pr
                )
                ag.append(r)
                st.markdown(f"#### Grille G{gi+1}")
                st.markdown(html_gr(r["grille"], r["etoiles"], stats, jid), unsafe_allow_html=True)
                show_sc(r["score"], calc_shannon_entropy(r["grille"], jeu["boules_max"]), get_popularity_profile(r["grille"]))
                st.markdown("---")
            st.session_state.gg.extend([{"g": r["grille"], "e": r["etoiles"], "s": r["score"]["total"], "m": f"Expert ({mode})", "t": datetime.now().strftime("%H:%M")} for r in ag])

    # 4. PAGE STATISTIQUES
    elif page == "📊 Statistiques":
        st.markdown("<div class='main-header'>📊 Analyse Graphique</div>", unsafe_allow_html=True)
        
        nc = 10
        nr = (jeu["boules_max"] + nc - 1) // nc
        zd, td = [], []
        for row in range(nr):
            zr, tr = [], []
            for col in range(nc):
                n = row * nc + col + 1
                if n <= jeu["boules_max"]:
                    s = stats["boules"][n]
                    zr.append(s["chaleur"])
                    tr.append(f"Numéro {n}<br>Indice chaleur : {s['chaleur']}/100<br>Écart actuel : {s['ecart']}")
                else:
                    zr.append(None)
                    tr.append("")
            zd.append(zr)
            td.append(tr)
            
        fh = go.Figure(data=go.Heatmap(
            z=zd, text=td, hoverinfo="text",
            colorscale=[[0, "#1e3a5f"], [0.5, "#f59e0b"], [1, "#ef4444"]],
            showscale=False
        ))
        
        for row in range(nr):
            for col in range(nc):
                n = row * nc + col + 1
                if n <= jeu["boules_max"]:
                    fh.add_annotation(x=col, y=row, text=str(n), showarrow=False, font=dict(color="white", size=14))
                    
        fh.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
        st.plotly_chart(fh, use_container_width=True)
        
        st.subheader("📋 Matrice globale des numéros")
        dfc = pd.DataFrame(list(stats["boules"].values()))
        st.dataframe(dfc[["numero", "ecart", "ecart_moy", "ecart_max", "chaleur", "proba", "tend", "retard"]].rename(
            columns={"numero": "N°", "ecart": "Écart Actuel", "ecart_moy": "Moyenne", "ecart_max": "Max", "chaleur": "Chaleur /100", "proba": "Index Proba %", "tend": "Tendance", "retard": "Retard estimé"}
        ), hide_index=True, use_container_width=True)

    # 5. PAGE VÉRIFICATEUR
    elif page == "📱 Vérifier mes grilles":
        st.markdown("<div class='main-header'>📱 Module de Vérification</div>", unsafe_allow_html=True)
        ti = st.text_input("Saisir les 5 numéros du tirage (séparés par des virgules)")
        ei = st.text_input("Saisir les étoiles (séparées par des virgules)") if jeu["nb_etoiles"] else ""
        
        if ti:
            try:
                tirage = sorted(set(int(n.strip()) for n in ti.split(",") if n.strip().isdigit()))
                etoiles_t = sorted(set(int(n.strip()) for n in ei.split(",") if n.strip().isdigit())) if ei else []
                if len(tirage) == 5:
                    st.subheader("Tirage de référence")
                    st.markdown(html_gr(tirage, etoiles_t, stats, jid), unsafe_allow_html=True)
                    
                    if st.session_state.gg:
                        st.subheader("Résultats comparatifs")
                        for g in st.session_state.gg:
                            commun = set(g["g"]) & set(tirage)
                            st.markdown(f"👉 Grille `{g['g']}` : **{len(commun)} numéros correspondants** {list(commun)}")
                    else:
                        st.info("Aucune grille enregistrée dans la session pour l'instant.")
            except Exception as ex:
                st.error(f"Erreur de saisie : {str(ex)}")

    # 6. PAGE QUAND JOUER ?
    elif page == "💎 Quand jouer ?":
        st.markdown("<div class='main-header'>💎 Évaluation de Rentabilité & Utilité</div>", unsafe_allow_html=True)
        jp = st.number_input("Jackpot de la cagnotte (en millions d'euros)", 17, 250, 50, step=5)
        
        prix = jeu["prix"]
        pr_gagner = 1.0 / 139838160.0 if jid == "euromillions" else 1.0 / 19068840.0
        
        esp = (jp * 1_000_000.0) * pr_gagner
        bilan = esp - prix
        
        u_nette, pi_p = calc_prospect_utility(jp, prix, pr_gagner)
        
        st.subheader("📊 Approche Mathématique Classique")
        st.metric("Rendement moyen espéré", f"{esp:.4f} €")
        st.metric("Espérance nette par grille", f"{bilan:.4f} €", delta=f"{bilan:.4f} €")
        
        st.subheader("🧠 Approche Comportementale (Prospect Theory)")
        st.metric("Utilité nette perçue", f"{u_nette:.4f} Utils", help="Un score positif indique que l'attractivité du jackpot justifie psychologiquement l'achat d'un ticket selon Kahneman-Tversky.")
        st.write(f"Pondération subjective de la probabilité : `{pi_p:.12f}` *(vs probabilité réelle : `{pr_gagner:.12f}`)*")
        
        if u_nette > 0:
            st.success("✅ Selon la Prospect Theory, le montant du jackpot compense subjectivement l'aversion à la perte. La grille possède une utilité perçue positive.")
        else:
            st.warning("📉 L'utilité perçue reste négative. Malgré la taille de la cagnotte, le coût du ticket pèse plus lourd dans la fonction de valeur subjective.")

    # 7. PAGE GLOSSAIRE
    elif page == "📖 Glossaire":
        st.markdown("<div class='main-header'>📖 Glossaire</div>", unsafe_allow_html=True)
        for terme, definition in GLOSSAIRE.items():
            st.markdown(f"<div class='glossary-term'><b>{terme}</b><br>{definition}</div>", unsafe_allow_html=True)

    # 8. PAGE BACKTEST
    elif page == "🧪 Backtest":
        st.markdown("<div class='main-header'>🧪 Simulations de Rendement</div>", unsafe_allow_html=True)
        
        st.write("Ce module vous permet d'éprouver une stratégie sur l'historique enregistré ou via un moteur de Monte-Carlo (tirages aléatoires uniformes synthétisés).")
        
        c1, c2 = st.columns(2)
        with c1:
            mode = st.selectbox("Stratégie de sélection", ["aleatoire", "chaud", "retard", "optimal"])
            sim_type = st.radio("Moteur de simulation", ["Historique (Tirages passés)", "Monte-Carlo (Tirages virtuels uniformes)"])
        with c2:
            if sim_type == "Historique (Tirages passés)":
                nt = st.selectbox("Nombre de tirages tests", [20, 50, 100, 200], index=1)
            else:
                nt = st.selectbox("Nombre de tirages virtuels", [1000, 5000, 10000], index=1)
        
        if st.button("🚀 LANCER LA SIMULATION", type="primary", use_container_width=True):
            if sim_type == "Historique (Tirages passés)":
                rb = backtest(df, jid, stats, mode, nt)
                st.subheader(f"Résultats de la simulation historique ({nt} tirages)")
            else:
                rb = simulate_monte_carlo(jid, stats, mode, nt)
                st.subheader(f"Résultats de la simulation de Monte-Carlo ({nt} tirages uniformes)")
                
            st.metric("Total des mises théoriques", f"{rb['mise']} €")
            st.metric("Total des gains retournés", f"{rb['gains']} €")
            st.metric("Solde financier net", f"{rb['bilan']} €", delta=f"{rb['bilan']} €")
            
            st.markdown("### Distribution des correspondances de numéros :")
            st.bar_chart(pd.Series(rb["res"]))

    # 9. PAGE RÉDUCTEUR
    elif page == "🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Réducteur Combinatoire</div>", unsafe_allow_html=True)
        ni = st.text_input("Entrez votre sélection de 6 à 15 numéros (séparés par des virgules)", "5, 12, 19, 24, 33, 41, 45")
        garantie = st.selectbox("Niveau de garantie théorique", [2, 3, 4])
        
        if ni:
            nums = []
            for n in ni.split(","):
                n_clean = n.strip()
                if n_clean.isdigit():
                    val = int(n_clean)
                    if 1 <= val <= jeu["boules_max"]:
                        nums.append(val)
            nums = sorted(list(set(nums)))
            
            if len(nums) >= 6:
                st.success(f"Numéros sélectionnés : {nums}")
                if st.button("🧮 OPTIMISER LES GRILLES", type="primary", use_container_width=True):
                    grilles = reducteur_mathematique(nums, garantie)
                    st.write(f"Nombre de grilles générées : **{len(grilles)}**")
                    for i, g in enumerate(grilles):
                        st.markdown(f"<div class='grille-container'><b>G{i+1} :</b> &nbsp;" + " ".join(f"<span class='boule'>{b}</span>" for b in g) + "</div>", unsafe_allow_html=True)
            else:
                st.warning("Veuillez sélectionner au moins 6 numéros différents.")

    # 10. PAGE MES GRILLES
    elif page == "🏆 Mes grilles":
        st.markdown("<div class='main-header'>🏆 Mes Grilles Générées</div>", unsafe_allow_html=True)
        if st.session_state.gg:
            for g in st.session_state.gg:
                st.write(f"🔹 Grille : `{g['g']}` — Étoiles : `{g['e']}` (Score : **{g['s']}/100** | {g['m']})")
            if st.button("🗑️ Réinitialiser la session"):
                st.session_state.gg = []
                st.rerun()
        else:
            st.info("Aucune grille générée pour le moment lors de cette session.")

    # 11. PAGE DEBUG
    elif page == "🔍 Debug":
        st.markdown("<div class='main-header'>🔍 Diagnostic Fichier</div>", unsafe_allow_html=True)
        st.write("Aperçu brut de la matrice de traitement active :")
        st.dataframe(df.head(10), use_container_width=True)

    # Note réglementaire obligatoire
    st.markdown("<div class='footer-disclaimer'>⚠️ Outil de traitement d'informations statistiques de jeu — Aucune garantie de gains — Le hasard conserve son indépendance lors de chaque tirage.<br>🛡️ <a href='https://www.joueurs-info-service.fr/'>Joueurs Info Service</a> : 09 74 75 13 13</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
