# ============================================================
# SMART-LOTO — V2.2 — FORMAT FDJ CORRIGÉ
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from datetime import datetime, timedelta
import plotly.graph_objects as go
import io
import re

st.set_page_config(
    page_title="Smart-Loto",
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
        color: white; border-radius: 50%;
        width: 65px; height: 65px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 22px; font-weight: bold; margin: 5px;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.4);
    }
    .etoile {
        background: linear-gradient(135deg, #f59e0b, #fbbf24);
        color: white; border-radius: 50%;
        width: 65px; height: 65px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 22px; font-weight: bold; margin: 5px;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
    }
    .grille-container {
        display: flex; align-items: center; justify-content: center;
        padding: 25px;
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-radius: 20px; margin: 15px 0; border: 2px solid #e2e8f0;
    }
    .footer-disclaimer {
        background: #fef3c7; border: 1px solid #f59e0b;
        border-radius: 12px; padding: 15px; margin-top: 30px;
        text-align: center; font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {
        "nom": "Euromillions", "emoji": "⭐",
        "boules_max": 50, "nb_boules": 5,
        "etoiles_max": 12, "nb_etoiles": 2,
        "prix": 2.50, "somme_min": 90, "somme_max": 160,
    },
    "loto": {
        "nom": "Loto", "emoji": "🎱",
        "boules_max": 49, "nb_boules": 5,
        "etoiles_max": None, "nb_etoiles": 0,
        "prix": 2.20, "somme_min": 60, "somme_max": 180,
    }
}


# ============================================================
# CHARGEMENT CSV — COMPATIBLE FORMAT FDJ
# ============================================================

def detecter_et_charger_csv(uploaded_file, jeu_id):
    """
    Détecte et charge le CSV FDJ.
    Format attendu : NUM;DATE;JACKPOT;N1;N2;N3;N4;N5;E1;E2;...
    Mais accepte aussi d'autres formats.
    """
    jeu = JEUX[jeu_id]
    debug = {}

    # Lire le contenu
    content = uploaded_file.read()
    uploaded_file.seek(0)

    # Décoder
    text = None
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]:
        try:
            text = content.decode(enc)
            debug["encodage"] = enc
            break
        except Exception:
            continue

    if text is None:
        return None, {"erreur": "Impossible de décoder le fichier"}

    # Supprimer BOM
    text = text.lstrip("\ufeff")

    # Détecter séparateur
    first_line = text.split("\n")[0]
    debug["premiere_ligne"] = first_line[:300]

    if first_line.count(";") > first_line.count(","):
        sep = ";"
    elif first_line.count("\t") > first_line.count(","):
        sep = "\t"
    else:
        sep = ","
    debug["separateur"] = sep

    # Charger
    try:
        df = pd.read_csv(io.StringIO(text), sep=sep)
    except Exception as e:
        return None, {"erreur": f"Erreur CSV: {e}"}

    # Nettoyer les noms de colonnes
    df.columns = [c.strip() for c in df.columns]

    # Supprimer les colonnes vides (trailing separator)
    df = df.loc[:, ~df.columns.str.match(r'^Unnamed')]
    df = df.loc[:, df.columns != '']

    debug["colonnes"] = list(df.columns)
    debug["nb_lignes_brut"] = len(df)

    # ═══════════════════════════════════════
    # MAPPING DES COLONNES — TOUS FORMATS
    # ═══════════════════════════════════════

    colonnes_lower = {c.strip().lower(): c for c in df.columns}

    # ---- DATE ----
    date_col = None
    # Priorité 1 : noms exacts connus
    for candidat in ["date", "date_de_tirage", "date de tirage", "draw_date", "jour_de_tirage"]:
        if candidat in colonnes_lower:
            date_col = colonnes_lower[candidat]
            break

    # Priorité 2 : contient "date"
    if date_col is None:
        for cl, co in colonnes_lower.items():
            if "date" in cl:
                date_col = co
                break

    # Priorité 3 : chercher une colonne avec des /
    if date_col is None:
        for col in df.columns:
            try:
                sample = str(df[col].iloc[0]).strip()
                if re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', sample) or re.match(r'\d{4}-\d{2}-\d{2}', sample):
                    date_col = col
                    break
            except Exception:
                continue

    debug["date_col"] = date_col
    if date_col is None:
        return None, debug

    # ---- BOULES ----
    boule_cols = []

    # Format FDJ : N1, N2, N3, N4, N5
    for i in range(1, 6):
        for candidat in [f"n{i}", f"N{i}", f"boule_{i}", f"boule {i}", f"Boule {i}",
                         f"ball_{i}", f"numero_{i}", f"num_{i}", f"b{i}"]:
            if candidat in df.columns:
                boule_cols.append(candidat)
                break
            elif candidat.lower() in colonnes_lower:
                boule_cols.append(colonnes_lower[candidat.lower()])
                break

    debug["boule_cols_detectees"] = boule_cols

    # Fallback : colonnes numériques 1-50
    if len(boule_cols) < 5:
        boule_cols = []
        date_idx = list(df.columns).index(date_col) if date_col in df.columns else 0
        for col in df.columns[date_idx + 1:]:
            try:
                vals = pd.to_numeric(df[col], errors="coerce")
                valid = vals.dropna()
                if len(valid) > len(df) * 0.5:
                    if valid.min() >= 1 and valid.max() <= jeu["boules_max"]:
                        boule_cols.append(col)
                        if len(boule_cols) >= 5:
                            break
            except Exception:
                continue
        debug["boule_cols_fallback"] = boule_cols

    if len(boule_cols) < 5:
        debug["erreur_boules"] = f"Seulement {len(boule_cols)} colonnes de boules trouvées"
        return None, debug

    # ---- ÉTOILES ----
    etoile_cols = []
    if jeu["nb_etoiles"] > 0:
        for i in range(1, 3):
            for candidat in [f"e{i}", f"E{i}", f"etoile_{i}", f"etoile {i}",
                             f"Etoile {i}", f"étoile_{i}", f"star_{i}", f"s{i}"]:
                if candidat in df.columns:
                    etoile_cols.append(candidat)
                    break
                elif candidat.lower() in colonnes_lower:
                    etoile_cols.append(colonnes_lower[candidat.lower()])
                    break

        # Fallback étoiles
        if len(etoile_cols) < 2:
            etoile_cols = []
            boule_set = set(boule_cols)
            for col in df.columns:
                if col in boule_set or col == date_col:
                    continue
                try:
                    vals = pd.to_numeric(df[col], errors="coerce").dropna()
                    if len(vals) > len(df) * 0.5:
                        if vals.min() >= 1 and vals.max() <= 12:
                            etoile_cols.append(col)
                            if len(etoile_cols) >= 2:
                                break
                except Exception:
                    continue

    debug["etoile_cols"] = etoile_cols

    # ═══════════════════════════════════════
    # CONSTRUCTION DU DATAFRAME FINAL
    # ═══════════════════════════════════════

    result = pd.DataFrame()

    # Date
    try:
        result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce").dt.date
    except Exception:
        try:
            result["date"] = pd.to_datetime(df[date_col], format="%d/%m/%Y", errors="coerce").dt.date
        except Exception:
            try:
                result["date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
            except Exception:
                return None, debug

    # Boules
    for i, col in enumerate(boule_cols[:5], 1):
        result[f"boule_{i}"] = pd.to_numeric(df[col], errors="coerce")

    # Étoiles
    for i, col in enumerate(etoile_cols[:2], 1):
        result[f"etoile_{i}"] = pd.to_numeric(df[col], errors="coerce")

    # Nettoyage
    result = result.dropna(subset=["date", "boule_1", "boule_2", "boule_3", "boule_4", "boule_5"])

    for i in range(1, 6):
        result[f"boule_{i}"] = result[f"boule_{i}"].astype(int)
    for i in range(1, 3):
        if f"etoile_{i}" in result.columns:
            result[f"etoile_{i}"] = result[f"etoile_{i}"].fillna(0).astype(int)

    # Filtrer valeurs invalides
    for i in range(1, 6):
        result = result[(result[f"boule_{i}"] >= 1) & (result[f"boule_{i}"] <= jeu["boules_max"])]

    result = result.sort_values("date", ascending=False).drop_duplicates(subset=["date"]).reset_index(drop=True)

    debug["nb_tirages_final"] = len(result)
    debug["premier_tirage"] = str(result.iloc[-1]["date"]) if len(result) > 0 else "—"
    debug["dernier_tirage"] = str(result.iloc[0]["date"]) if len(result) > 0 else "—"
    debug["succes"] = len(result) > 0
    debug["mapping"] = {
        "date": date_col,
        "boules": boule_cols[:5],
        "etoiles": etoile_cols[:2]
    }

    return result, debug


def generer_historique_simule(jeu_id, nb=500):
    random.seed(42); np.random.seed(42)
    jeu = JEUX[jeu_id]
    tirages = []
    now = datetime.now()
    for i in range(nb):
        b = sorted(random.sample(range(1, jeu["boules_max"]+1), 5))
        e = sorted(random.sample(range(1, jeu["etoiles_max"]+1), 2)) if jeu["etoiles_max"] else []
        t = {"date": (now - timedelta(days=i*3.5)).date(),
             "boule_1": b[0], "boule_2": b[1], "boule_3": b[2], "boule_4": b[3], "boule_5": b[4]}
        if e:
            t["etoile_1"] = e[0]; t["etoile_2"] = e[1]
        tirages.append(t)
    return pd.DataFrame(tirages).sort_values("date", ascending=False).reset_index(drop=True)


# ============================================================
# MOTEUR STATISTIQUE
# ============================================================

@st.cache_data
def calculer_stats(df_json, jeu_id):
    df = pd.read_json(io.StringIO(df_json))
    df["date"] = pd.to_datetime(df["date"]).dt.date
    jeu = JEUX[jeu_id]
    stats = {}
    cols = [f"boule_{i}" for i in range(1, 6)]

    all_nums = []
    for c in cols:
        all_nums.extend(df[c].tolist())

    df20 = df.head(20)
    nums20 = []
    for c in cols:
        nums20.extend(df20[c].tolist())

    date12m = datetime.now().date() - timedelta(days=365)
    df12m = df[df["date"] >= date12m]
    nums12m = []
    for c in cols:
        nums12m.extend(df12m[c].tolist())

    freq_all = Counter(all_nums)
    freq20 = Counter(nums20)
    freq12m = Counter(nums12m)

    for n in range(1, jeu["boules_max"]+1):
        ecart = 0
        for _, row in df.iterrows():
            if n in [int(row[c]) for c in cols]:
                break
            ecart += 1

        positions = [idx for idx, row in df.iterrows() if n in [int(row[c]) for c in cols]]
        ecarts_h = [positions[i+1]-positions[i] for i in range(len(positions)-1)] if len(positions) > 1 else []
        ecart_moy = np.mean(ecarts_h) if ecarts_h else 10
        ecart_max = max(ecarts_h) if ecarts_h else ecart

        dern = None
        for _, row in df.iterrows():
            if n in [int(row[c]) for c in cols]:
                dern = row["date"]; break

        forme = (freq20.get(n, 0) / 20) * 100
        freq_th = (len(df12m) * 5) / jeu["boules_max"]
        freq_n = (freq12m.get(n, 0) / max(freq_th, 1)) * 50
        ec_p = max(0, 30 - (ecart * 2))
        chaleur = min(100, max(0, 0.40*forme + 0.35*freq_n + 0.25*ec_p))

        stats[n] = {
            "numero": n, "ecart_actuel": ecart, "ecart_moyen": round(ecart_moy, 1),
            "ecart_max": ecart_max, "frequence_totale": freq_all.get(n, 0),
            "frequence_20t": freq20.get(n, 0), "frequence_12m": freq12m.get(n, 0),
            "indice_chaleur": round(chaleur, 1), "derniere_sortie": str(dern) if dern else "—"
        }

    # Étoiles
    stats_et = {}
    if jeu["nb_etoiles"] and jeu["nb_etoiles"] > 0 and "etoile_1" in df.columns:
        ce = [f"etoile_{i}" for i in range(1, jeu["nb_etoiles"]+1)]
        all_e = []; e20 = []
        for c in ce:
            if c in df.columns:
                all_e.extend(df[c].tolist())
                e20.extend(df20[c].tolist())
        fe = Counter(all_e); fe20 = Counter(e20)
        for n in range(1, jeu["etoiles_max"]+1):
            ecart = 0
            for _, row in df.iterrows():
                if n in [int(row[c]) for c in ce if c in df.columns]:
                    break
                ecart += 1
            stats_et[n] = {"numero": n, "ecart_actuel": ecart,
                           "frequence_totale": fe.get(n, 0), "frequence_20t": fe20.get(n, 0)}

    # Paires
    paires = Counter()
    for _, row in df.iterrows():
        bs = sorted([int(row[c]) for c in cols])
        for i in range(len(bs)):
            for j in range(i+1, len(bs)):
                paires[(bs[i], bs[j])] += 1

    return {
        "boules": stats, "etoiles": stats_et,
        "paires": paires.most_common(20),
        "nb_tirages": len(df),
        "date_premier": str(df.iloc[-1]["date"]) if len(df) > 0 else "—",
        "date_dernier": str(df.iloc[0]["date"]) if len(df) > 0 else "—",
    }


# ============================================================
# SCORE & GÉNÉRATEUR
# ============================================================

def score_robustesse(grille, etoiles, stats, jeu_id):
    jeu = JEUX[jeu_id]
    sc = {}
    np2 = sum(1 for n in grille if n % 2 == 0)
    r = np2 / len(grille)
    sc["⚖️ Parité"] = 25 if 0.3 <= r <= 0.7 else (15 if 0.2 <= r <= 0.8 else 5)

    diz = Counter(n // 10 for n in grille)
    sc["📊 Dizaines"] = 20 if (len(diz) >= 4 and max(diz.values()) <= 2) else (15 if (len(diz) >= 3 and max(diz.values()) <= 3) else 5)

    s = sum(grille)
    m = jeu["nb_boules"] * (jeu["boules_max"]+1) / 2
    z = abs(s - m) / 35
    sc["➕ Somme"] = 20 if z <= 0.5 else (15 if z <= 1 else (10 if z <= 1.5 else 3))

    ecs = [stats["boules"][n]["ecart_actuel"] for n in grille if n in stats["boules"]]
    if len(set(ecs)) > 1:
        std = float(np.std(ecs))
        sc["🔀 Diversité"] = 15 if std > 5 else (10 if std > 3 else 5)
    else:
        sc["🔀 Diversité"] = 5

    g = sorted(grille)
    hs = any(g[i+1]==g[i]+1 and g[i+2]==g[i]+2 for i in range(len(g)-2))
    sc["🚫 Anti-suite"] = 2 if hs else 10

    if etoiles and len(etoiles) == 2:
        ec = abs(etoiles[0]-etoiles[1])
        sc["⭐ Étoiles"] = 10 if ec >= 3 else (6 if ec >= 2 else 2)
    else:
        sc["⭐ Étoiles"] = 10

    return {"total": sum(sc.values()), "detail": sc}


def generer_grille(jeu_id, stats, mode="aleatoire", f_par=False, f_som=False,
                   f_diz=False, f_sui=False, chasseur=0, forces=None,
                   ec_et=0, plafond="aucun", max_t=1000):
    jeu = JEUX[jeu_id]
    for t in range(max_t):
        if mode == "chaud":
            pool = sorted(stats["boules"], key=lambda x: stats["boules"][x]["indice_chaleur"], reverse=True)[:20]
        elif mode == "froid":
            pool = sorted(stats["boules"], key=lambda x: stats["boules"][x]["ecart_actuel"], reverse=True)[:20]
        elif mode == "top":
            pool = sorted(stats["boules"], key=lambda x: stats["boules"][x]["frequence_12m"], reverse=True)[:15]
        elif mode == "hybride":
            nums = list(stats["boules"].keys())
            poids = [stats["boules"][n]["indice_chaleur"]**1.5 + 5 for n in nums]
            tp = sum(poids)
            pool = list(np.random.choice(nums, size=min(25, len(nums)), replace=False, p=[p/tp for p in poids]))
        else:
            pool = list(range(1, jeu["boules_max"]+1))

        if plafond == "moins_40":
            pool = [n for n in pool if n < 40]
        if chasseur > 0:
            pf = [n for n in pool if stats["boules"][n]["ecart_actuel"] >= chasseur]
            if len(pf) >= 5: pool = pf

        fo = [f for f in (forces or []) if 1 <= f <= jeu["boules_max"]]
        dispo = [n for n in pool if n not in fo]
        manq = 5 - len(fo)
        if manq > len(dispo):
            dispo = [n for n in range(1, jeu["boules_max"]+1) if n not in fo]
        ch = random.sample(dispo, min(manq, len(dispo))) if manq > 0 else []
        grille = sorted(fo + ch)[:5]

        if plafond == "force_40" and not any(n >= 40 for n in grille):
            s40 = [n for n in range(40, jeu["boules_max"]+1) if n not in grille]
            if s40:
                non_fo = [n for n in grille if n not in fo]
                if non_fo:
                    rem = min(non_fo, key=lambda x: stats["boules"][x]["indice_chaleur"])
                    grille.remove(rem); grille.append(random.choice(s40)); grille = sorted(grille)

        etoiles = []
        if jeu["nb_etoiles"] and jeu["nb_etoiles"] > 0 and jeu["etoiles_max"]:
            for _ in range(100):
                etoiles = sorted(random.sample(range(1, jeu["etoiles_max"]+1), jeu["nb_etoiles"]))
                if ec_et > 0 and len(etoiles) == 2 and abs(etoiles[0]-etoiles[1]) >= ec_et:
                    break
                elif ec_et == 0:
                    break

        v = True
        if f_par:
            np2 = sum(1 for n in grille if n%2==0)
            if np2 == 0 or np2 == 5: v = False
        if f_som:
            if not (jeu["somme_min"] <= sum(grille) <= jeu["somme_max"]): v = False
        if f_diz:
            if max(Counter(n//10 for n in grille).values()) > 3: v = False
        if f_sui:
            gs = sorted(grille)
            if any(gs[i+1]==gs[i]+1 and gs[i+2]==gs[i]+2 for i in range(len(gs)-2)): v = False

        if v:
            return {"grille": grille, "etoiles": etoiles,
                    "score": score_robustesse(grille, etoiles, stats, jeu_id),
                    "tentatives": t+1, "mode": mode}

    grille = sorted(random.sample(range(1, jeu["boules_max"]+1), 5))
    etoiles = sorted(random.sample(range(1, jeu["etoiles_max"]+1), 2)) if jeu["etoiles_max"] else []
    return {"grille": grille, "etoiles": etoiles,
            "score": score_robustesse(grille, etoiles, stats, jeu_id),
            "tentatives": max_t, "mode": "fallback"}


# ============================================================
# BACKTESTING & RÉDUCTEUR
# ============================================================

def mini_backtest(df, jeu_id, stats, mode, nb_t=50, gpt=1):
    jeu = JEUX[jeu_id]
    cols = [f"boule_{i}" for i in range(1, 6)]
    res = {str(i): 0 for i in range(6)}
    tm, tg = 0, 0
    gt = {0:0, 1:0, 2:0, 3:4, 4:50, 5:5000}
    hist = []
    for idx in range(min(nb_t, len(df))):
        row = df.iloc[idx]
        bt = set(int(row[c]) for c in cols)
        for _ in range(gpt):
            r = generer_grille(jeu_id, stats, mode=mode)
            nb = len(set(r["grille"]) & bt)
            res[str(nb)] += 1; tm += jeu["prix"]; g = gt.get(nb, 0); tg += g
            if nb >= 3:
                hist.append({"date": str(row["date"]), "grille": r["grille"],
                    "tirage": sorted(bt), "bons": nb, "gain": g})
    return {"resultats": res, "total_mise": round(tm, 2), "total_gains": round(tg, 2),
            "bilan": round(tg-tm, 2), "nb_grilles": nb_t*gpt, "historique": hist}


def systeme_reducteur(nums, taille=5):
    from itertools import combinations
    if len(nums) <= taille: return [sorted(nums)]
    combs = list(combinations(nums, taille)); random.shuffle(combs)
    grilles, couverts = [], set()
    for c in combs:
        if set(c) - couverts or not grilles:
            grilles.append(sorted(c)); couverts |= set(c)
        if couverts == set(nums) and len(grilles) >= 3: break
        if len(grilles) >= 12: break
    return grilles


# ============================================================
# INTERFACE
# ============================================================

def main():
    st.sidebar.markdown("<div style='text-align:center;'><h1 style='font-size:2rem;'>🎱 Smart-Loto</h1>"
        "<p style='color:#64748b;'>V2.2 — Format FDJ</p></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    jeu_id = st.sidebar.selectbox("🎮 Jeu", ["euromillions", "loto"],
        format_func=lambda x: f"{JEUX[x]['emoji']} {JEUX[x]['nom']}")
    jeu = JEUX[jeu_id]

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📂 Données")
    uploaded = st.sidebar.file_uploader(f"📤 CSV {jeu['nom']}", type=["csv", "txt"])

    donnees_reelles = False
    debug = {}

    if uploaded:
        df, debug = detecter_et_charger_csv(uploaded, jeu_id)
        if df is not None and len(df) > 0:
            donnees_reelles = True
            st.sidebar.success(f"✅ {len(df)} tirages réels !")
            if "mapping" in debug:
                st.sidebar.caption(f"Date: {debug['mapping']['date']}")
                st.sidebar.caption(f"Boules: {debug['mapping']['boules']}")
                st.sidebar.caption(f"Étoiles: {debug['mapping']['etoiles']}")
        else:
            st.sidebar.error("❌ Erreur lecture CSV")
            if debug:
                st.sidebar.caption(f"Colonnes: {debug.get('colonnes', '?')}")
            df = generer_historique_simule(jeu_id)
    else:
        df = generer_historique_simule(jeu_id)
        st.sidebar.info("💡 Importe un CSV FDJ")

    st.sidebar.markdown("---")
    page = st.sidebar.radio("📑 Menu",
        ["🏠 Dashboard", "🎯 Générateur", "📊 Statistiques",
         "🧪 Backtesting", "🧮 Réducteur", "🔍 Debug CSV", "ℹ️ À propos"])
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ Aucune garantie de gain\n🛡️ 09 74 75 13 13")

    stats = calculer_stats(df.to_json(), jeu_id)
    badge = "🟢 Données réelles" if donnees_reelles else "🟡 Simulées"

    # ════════════════════════════════════
    # DASHBOARD
    # ════════════════════════════════════
    if page == "🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {badge} — {stats['nb_tirages']} tirages</div>", unsafe_allow_html=True)

        if donnees_reelles:
            st.success(f"✅ {stats['nb_tirages']} tirages réels ({stats['date_premier']} → {stats['date_dernier']})")

        d = df.iloc[0]
        bs = [int(d[f"boule_{i}"]) for i in range(1, 6)]
        st.subheader(f"🎱 Dernier tirage — {d['date']}")
        h = "<div class='grille-container'>"
        for b in bs: h += f"<span class='boule'>{b}</span>"
        if jeu["nb_etoiles"] and "etoile_1" in df.columns:
            h += "<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
            for i in range(1, jeu["nb_etoiles"]+1):
                if f"etoile_{i}" in d: h += f"<span class='etoile'>⭐{int(d[f'etoile_{i}'])}</span>"
        h += "</div>"
        st.markdown(h, unsafe_allow_html=True)

        # 10 derniers
        st.subheader("📋 10 derniers tirages")
        dern = []
        for i in range(min(10, len(df))):
            r = df.iloc[i]
            t = " - ".join(str(int(r[f"boule_{j}"])) for j in range(1, 6))
            e = ""
            if jeu["nb_etoiles"] and "etoile_1" in df.columns:
                e = f"⭐{int(r['etoile_1'])} ⭐{int(r['etoile_2'])}"
            dern.append({"📅": str(r["date"]), "🎱 Boules": t, "⭐": e})
        st.dataframe(pd.DataFrame(dern), hide_index=True, use_container_width=True)

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Top 10 Chauds")
            ch = sorted(stats["boules"].values(), key=lambda x: x["indice_chaleur"], reverse=True)[:10]
            st.dataframe(pd.DataFrame(ch)[["numero","indice_chaleur","frequence_20t","ecart_actuel"]].rename(
                columns={"numero":"N°","indice_chaleur":"🌡️","frequence_20t":"F20","ecart_actuel":"Écart"}),
                hide_index=True, use_container_width=True)
        with c2:
            st.subheader("🧊 Top 10 Absents")
            fr = sorted(stats["boules"].values(), key=lambda x: x["ecart_actuel"], reverse=True)[:10]
            st.dataframe(pd.DataFrame(fr)[["numero","ecart_actuel","ecart_moyen","ecart_max"]].rename(
                columns={"numero":"N°","ecart_actuel":"Écart","ecart_moyen":"Moy","ecart_max":"Record"}),
                hide_index=True, use_container_width=True)

        st.subheader("💑 Paires fréquentes")
        pd_data = [{"Paire": f"{p[0][0]} — {p[0][1]}", "Freq": p[1]} for p in stats["paires"][:10]]
        c1, c2 = st.columns(2)
        with c1: st.dataframe(pd.DataFrame(pd_data[:5]), hide_index=True, use_container_width=True)
        with c2: st.dataframe(pd.DataFrame(pd_data[5:]), hide_index=True, use_container_width=True)

        if stats["etoiles"]:
            st.subheader("⭐ Étoiles")
            st.dataframe(pd.DataFrame([{"⭐": f"Étoile {s['numero']}", "Écart": s["ecart_actuel"],
                "F20": s["frequence_20t"]} for s in stats["etoiles"].values()]),
                hide_index=True, use_container_width=True)

    # ════════════════════════════════════
    # GÉNÉRATEUR
    # ════════════════════════════════════
    elif page == "🎯 Générateur":
        st.markdown("<div class='main-header'>🎯 Générateur</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{badge}</div>", unsafe_allow_html=True)

        if donnees_reelles:
            st.success(f"✅ Basé sur {stats['nb_tirages']} tirages réels !")
        else:
            st.warning("⚠️ Données simulées — Importe un CSV")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📌 Tendance")
            mode = st.selectbox("Mode", ["aleatoire","chaud","froid","top","hybride"],
                format_func=lambda x: {"aleatoire":"🎲 Aléatoire","chaud":"🔥 Chauds",
                    "froid":"🧊 Absents","top":"⭐ Top 12m","hybride":"🧠 Hybride"}[x])
            st.markdown("### 📌 Préférences")
            fi = st.text_input("🔒 Forcés (max 3)", placeholder="7, 14, 23")
            forces = [int(n.strip()) for n in fi.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]][:3] if fi else []
            if forces: st.success(f"Forcés: {forces}")
            chasseur = st.slider("🎯 Écart min", 0, 30, 0)
            plafond = st.selectbox("🔝 Plafond", ["aucun","moins_40","force_40"],
                format_func=lambda x: {"aucun":"Aucun","moins_40":"< 40","force_40":"Forcer ≥ 40"}[x])

        with c2:
            st.markdown("### 📌 Filtres")
            fp = st.checkbox("⚖️ Parité", True)
            fs = st.checkbox("➕ Somme Gauss", True)
            fd = st.checkbox("📊 Dizaines", True)
            fa = st.checkbox("🚫 Anti-suite", True)
            ee = st.slider("⭐ Écart étoiles", 0, 8, 2) if jeu["nb_etoiles"] else 0
            nb = st.selectbox("Grilles", [1,3,5,10], index=1)

        st.markdown("---")
        if st.button("🎱 GÉNÉRER", type="primary", use_container_width=True):
            all_g = []
            for gi in range(nb):
                r = generer_grille(jeu_id, stats, mode, fp, fs, fd, fa, chasseur, forces, ee, plafond)
                all_g.append(r)
                sc = r["score"]; gr = r["grille"]; et = r["etoiles"]
                ev = "⭐⭐⭐⭐⭐" if sc["total"]>=80 else ("⭐⭐⭐⭐" if sc["total"]>=65 else ("⭐⭐⭐" if sc["total"]>=50 else "⭐⭐"))

                st.markdown(f"#### Grille {gi+1}/{nb}")
                html = "<div class='grille-container'>"
                for b in gr:
                    ch = stats["boules"][b]["indice_chaleur"]
                    bg = "linear-gradient(135deg,#dc2626,#ef4444)" if ch>=60 else ("linear-gradient(135deg,#1e40af,#3b82f6)" if ch>=40 else "linear-gradient(135deg,#1e3a5f,#475569)")
                    html += f"<span style='background:{bg};color:white;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(0,0,0,0.3);'>{b}</span>"
                if et:
                    html += "<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
                    for e in et: html += f"<span class='etoile'>⭐{e}</span>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

                cs1, cs2 = st.columns([1, 2])
                with cs1:
                    sc_c = "#22c55e" if sc["total"]>=70 else ("#f59e0b" if sc["total"]>=50 else "#ef4444")
                    st.markdown(f"<div style='text-align:center;'><div style='font-size:3rem;font-weight:800;color:{sc_c};'>{sc['total']}</div>"
                        f"<div style='color:#64748b;'>/ 100 {ev}</div>"
                        f"<div style='font-size:0.8rem;color:#94a3b8;'>Σ{sum(gr)} P:{sum(1 for n in gr if n%2==0)} I:{sum(1 for n in gr if n%2!=0)}</div></div>", unsafe_allow_html=True)
                with cs2:
                    mx = {"⚖️ Parité":25,"📊 Dizaines":20,"➕ Somme":20,"🔀 Diversité":15,"🚫 Anti-suite":10,"⭐ Étoiles":10}
                    for cr, pt in sc["detail"].items():
                        m = mx.get(cr, 10); pct = pt/m if m else 0
                        cl = "#22c55e" if pct>=0.7 else ("#f59e0b" if pct>=0.4 else "#ef4444")
                        bar = "█"*int(pct*12) + "░"*(12-int(pct*12))
                        st.markdown(f"`{cr}` <span style='color:{cl};font-family:monospace;'>{bar}</span> **{pt}/{m}**", unsafe_allow_html=True)

                with st.expander(f"📋 Détail numéros G{gi+1}"):
                    det = [{"N°": b, "🌡️": stats["boules"][b]["indice_chaleur"],
                            "Écart": stats["boules"][b]["ecart_actuel"],
                            "F20": stats["boules"][b]["frequence_20t"],
                            "Dernière": stats["boules"][b]["derniere_sortie"]} for b in gr]
                    st.dataframe(pd.DataFrame(det), hide_index=True, use_container_width=True)
                st.markdown("---")

            # Mode buraliste
            st.subheader("📱 Mode Buraliste")
            for i, r in enumerate(all_g):
                gs = " — ".join(str(n) for n in r["grille"])
                es = f"  |  ⭐ {' — '.join(str(e) for e in r['etoiles'])}" if r["etoiles"] else ""
                st.markdown(f"<div style='text-align:center;font-size:28px;font-weight:bold;padding:15px;background:#f8fafc;border-radius:12px;margin:8px 0;'>G{i+1}: {gs}{es}</div>", unsafe_allow_html=True)

    # ════════════════════════════════════
    # STATISTIQUES
    # ════════════════════════════════════
    elif page == "📊 Statistiques":
        st.markdown("<div class='main-header'>📊 Statistiques</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{badge} — {stats['nb_tirages']} tirages</div>", unsafe_allow_html=True)

        st.subheader("🌡️ Carte de Chaleur")
        nc = 10; nr = (jeu["boules_max"]+nc-1)//nc
        zd, td = [], []
        for row in range(nr):
            zr, tr = [], []
            for col in range(nc):
                n = row*nc+col+1
                if n <= jeu["boules_max"]:
                    s = stats["boules"][n]
                    zr.append(s["indice_chaleur"])
                    tr.append(f"N°{n}<br>🌡️{s['indice_chaleur']}<br>Écart:{s['ecart_actuel']}<br>F20:{s['frequence_20t']}")
                else: zr.append(None); tr.append("")
            zd.append(zr); td.append(tr)
        fh = go.Figure(data=go.Heatmap(z=zd, text=td, hoverinfo="text",
            colorscale=[[0,"#1e3a5f"],[0.5,"#f59e0b"],[1,"#ef4444"]], showscale=True))
        for row in range(nr):
            for col in range(nc):
                n = row*nc+col+1
                if n <= jeu["boules_max"]:
                    fh.add_annotation(x=col, y=row, text=str(n), showarrow=False, font=dict(color="white", size=14))
        fh.update_layout(height=350, margin=dict(l=20,r=20,t=20,b=20), xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
        st.plotly_chart(fh, use_container_width=True)

        st.subheader("📈 Écarts vs Moyenne")
        ed = [(n, stats["boules"][n]["ecart_actuel"], stats["boules"][n]["ecart_moyen"]) for n in range(1, jeu["boules_max"]+1)]
        fe = go.Figure()
        fe.add_trace(go.Bar(x=[d[0] for d in ed], y=[d[1] for d in ed], name="Actuel",
            marker_color=["#ef4444" if d[1]>d[2]*1.5 else "#3b82f6" for d in ed]))
        fe.add_trace(go.Scatter(x=[d[0] for d in ed], y=[d[2] for d in ed], name="Moyenne",
            mode="lines", line=dict(color="#22c55e", width=2, dash="dash")))
        fe.update_layout(height=350)
        st.plotly_chart(fe, use_container_width=True)

        st.subheader("📋 Tableau")
        tri = st.selectbox("Tri", ["🌡️ Chaleur","Écart","Freq 20t","Freq 12m"])
        dfc = pd.DataFrame([{"N°": n, "🌡️ Chaleur": stats["boules"][n]["indice_chaleur"],
            "Écart": stats["boules"][n]["ecart_actuel"], "Moy": stats["boules"][n]["ecart_moyen"],
            "Record": stats["boules"][n]["ecart_max"], "Freq 20t": stats["boules"][n]["frequence_20t"],
            "Freq 12m": stats["boules"][n]["frequence_12m"]} for n in range(1, jeu["boules_max"]+1)])
        st.dataframe(dfc.sort_values(tri, ascending=(tri=="Écart")), hide_index=True, use_container_width=True, height=500)

    # ════════════════════════════════════
    # BACKTESTING
    # ════════════════════════════════════
    elif page == "🧪 Backtesting":
        st.markdown("<div class='main-header'>🧪 Backtesting</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{badge}</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            mbt = st.selectbox("Stratégie", ["aleatoire","chaud","froid","top","hybride"],
                format_func=lambda x: {"aleatoire":"🎲","chaud":"🔥","froid":"🧊","top":"⭐","hybride":"🧠"}[x] + " " + x.capitalize())
        with c2:
            nbt = st.selectbox("Tirages", [20,50,100,200], index=1)

        if st.button("🚀 LANCER", type="primary", use_container_width=True):
            with st.spinner("⏳..."):
                rb = mini_backtest(df, jeu_id, stats, mbt, nbt)
            c1,c2,c3 = st.columns(3)
            c1.metric("💰 Misé", f"{rb['total_mise']}€")
            c2.metric("🏆 Gagné", f"{rb['total_gains']}€")
            c3.metric("📈 Bilan", f"{rb['bilan']:+.2f}€")
            res = rb["resultats"]
            fb = go.Figure(go.Bar(x=[f"{k} bons" for k in sorted(res)], y=[res[k] for k in sorted(res)],
                marker_color=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#15803d"]))
            fb.update_layout(height=300)
            st.plotly_chart(fb, use_container_width=True)
            if rb["historique"]:
                st.subheader("🎯 Correspondances")
                for h in rb["historique"][:10]:
                    st.markdown(f"📅 **{h['date']}** — `{h['grille']}` vs `{h['tirage']}` — **{h['bons']}** bons — {h['gain']}€")

    # ════════════════════════════════════
    # RÉDUCTEUR
    # ════════════════════════════════════
    elif page == "🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Réducteur</div>", unsafe_allow_html=True)
        with st.expander("💡 Suggestions"):
            top = sorted(stats["boules"].values(), key=lambda x: x["indice_chaleur"], reverse=True)[:10]
            st.markdown(f"**Top chaleur:** `{', '.join(str(n['numero']) for n in top)}`")
        ni = st.text_input("🔢 Numéros (6-15)", placeholder="3, 7, 14, 19, 23, 28, 34, 41")
        if ni:
            nums = sorted(set(int(n.strip()) for n in ni.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]))
            if len(nums) >= 6:
                st.success(f"✅ {len(nums)} numéros: {nums}")
                if st.button("🧮 GÉNÉRER", type="primary", use_container_width=True):
                    grs = systeme_reducteur(nums)
                    st.info(f"💰 {len(grs)} × {jeu['prix']}€ = **{len(grs)*jeu['prix']:.2f}€**")
                    for i, g in enumerate(grs):
                        html = f"<div class='grille-container'><b>G{i+1}</b>&nbsp;&nbsp;"
                        for b in g: html += f"<span class='boule'>{b}</span>"
                        html += "</div>"
                        st.markdown(html, unsafe_allow_html=True)
            else:
                st.warning(f"Min 6 ({len(nums)} actuellement)")

    # ════════════════════════════════════
    # DEBUG CSV
    # ════════════════════════════════════
    elif page == "🔍 Debug CSV":
        st.markdown("<div class='main-header'>🔍 Debug CSV</div>", unsafe_allow_html=True)

        if debug:
            st.subheader("📊 Résultat de l'analyse")

            if debug.get("succes"):
                st.success(f"✅ CSV chargé avec succès ! {debug.get('nb_tirages_final', '?')} tirages")

            if "premiere_ligne" in debug:
                st.subheader("📋 En-tête du CSV")
                st.code(debug["premiere_ligne"])

            if "encodage" in debug:
                st.info(f"Encodage: **{debug['encodage']}** | Séparateur: **{debug['separateur']}**")

            if "colonnes" in debug:
                st.subheader("📋 Colonnes détectées")
                for i, c in enumerate(debug["colonnes"]):
                    st.markdown(f"`{i}` → **{c}**")

            if "mapping" in debug:
                st.subheader("🔗 Mapping appliqué")
                m = debug["mapping"]
                st.success(f"**Date** : `{m['date']}`")
                st.success(f"**Boules** : `{m['boules']}`")
                st.success(f"**Étoiles** : `{m['etoiles']}`")

            if "date_col" in debug and debug["date_col"] is None:
                st.error("❌ Colonne date non trouvée !")

            if "erreur_boules" in debug:
                st.error(f"❌ {debug['erreur_boules']}")

            if debug.get("nb_tirages_final"):
                st.info(f"📅 {debug['premier_tirage']} → {debug['dernier_tirage']}")
        else:
            st.info("📤 Importe un CSV pour voir le debug")

        st.markdown("---")
        st.subheader("📋 Données chargées")
        st.dataframe(df.head(20), use_container_width=True)
        st.caption(f"Colonnes: {list(df.columns)} | Lignes: {len(df)}")

        st.subheader("📝 Format de ton CSV FDJ")
        st.code("NUM;DATE;JACKPOT;N1;N2;N3;N4;N5;E1;E2;...", language="text")
        st.markdown("""
        **Mapping automatique :**
        - `DATE` → Date du tirage
        - `N1, N2, N3, N4, N5` → Les 5 boules
        - `E1, E2` → Les 2 étoiles
        """)

    # ════════════════════════════════════
    # À PROPOS
    # ════════════════════════════════════
    elif page == "ℹ️ À propos":
        st.markdown("<div class='main-header'>ℹ️ À propos</div>", unsafe_allow_html=True)
        st.markdown(f"""
        ## Smart-Loto V2.2

        | Module | Statut |
        |---|---|
        | 📂 Import CSV FDJ (format N1/N2/E1/E2) | ✅ |
        | 🔍 Debug CSV | ✅ |
        | 🏠 Dashboard | ✅ |
        | 🎯 Générateur (5 modes + 7 filtres) | ✅ |
        | 📊 Stats (heatmap, écarts, tableau) | ✅ |
        | 🧪 Backtesting | ✅ |
        | 🧮 Réducteur | ✅ |

        **Source:** {badge} | **Tirages:** {stats['nb_tirages']}

        ⚠️ Aucune garantie de gain
        🛡️ Joueurs Info Service: 09 74 75 13 13
        """)

    # Footer
    st.markdown("<div class='footer-disclaimer'>⚠️ Outil d'analyse — Aucune garantie de gain — "
        "🛡️ <a href='https://www.joueurs-info-service.fr/'>Joueurs Info Service</a> 09 74 75 13 13</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
