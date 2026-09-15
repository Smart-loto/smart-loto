# ============================================================
# SMART-LOTO — VERSION 37.0 — EVIDENCE ENGINE
# ============================================================
# Objectif : laboratoire statistique + générateur de portefeuilles
# IMPORTANT : aucune métrique présentée ici ne transforme un tirage
# aléatoire indépendant en événement prédictible. Les pondérations sont
# des heuristiques exploratoires, évaluées par backtest walk-forward.

import io
import math
import random
import re
import unicodedata
from itertools import combinations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


# ============================================================
# 1. CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Smart-Loto V37 Evidence",
    page_icon="🧬",
    layout="wide",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        html, body, [data-testid="stAppViewContainer"], .main {
            background-color:#0f172a !important;
            color:#f8fafc !important;
            font-family:'Inter',sans-serif;
        }
        [data-testid="stSidebar"] {
            background-color:#1e293b !important;
            border-right:1px solid #334155;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p {
            color:#fbbf24 !important;
            font-weight:700 !important;
        }
        .main-header {
            font-size:2.35rem;
            font-weight:900;
            background:linear-gradient(135deg,#fbbf24,#d97706);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            text-align:center;
            padding:1.2rem 0;
        }
        .result-card {
            background:#1e293b;
            border:1px solid #334155;
            border-radius:16px;
            padding:1.25rem;
            margin-bottom:1rem;
            border-left:5px solid #fbbf24;
        }
        .boule, .etoile {
            color:white !important;
            border-radius:50%;
            width:44px;
            height:44px;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            font-weight:900;
            margin:4px;
            box-shadow:0 4px 10px rgba(0,0,0,0.45);
            font-size:1rem;
        }
        .boule {
            background:radial-gradient(circle at 30% 30%,#3b82f6,#1e40af);
            border:1px solid #60a5fa;
        }
        .etoile {
            background:radial-gradient(circle at 30% 30%,#fbbf24,#d97706);
            border:1px solid #fcd34d;
        }
        .metric-card {
            background:#1e293b;
            border-left:5px solid #fbbf24;
            padding:1rem;
            border-radius:12px;
            margin-bottom:10px;
            box-shadow:0 4px 15px rgba(0,0,0,0.25);
        }
        .metric-title {
            font-size:.72rem;
            color:#94a3b8;
            text-transform:uppercase;
            font-weight:900;
        }
        .metric-value {
            font-size:1.08rem;
            font-weight:800;
            color:#fff;
        }
        .mini-grid {
            display:grid;
            grid-template-columns:repeat(10,1fr);
            gap:2px;
            background:#0f172a;
            padding:5px;
            border-radius:4px;
            width:110px;
        }
        .mini-cell {
            width:9px;
            height:9px;
            background:#334155;
            border-radius:1px;
        }
        .mini-cell.active { background:#fbbf24; }
        label, p, span, .stSlider, .stCheckbox { color:#fff !important; }
        div[data-baseweb="select"] > div {
            background-color:#1e293b !important;
            color:white !important;
            border:1px solid #334155 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

JEUX = {
    "euromillions": {
        "nom": "Euromillions",
        "b_max": 50,
        "e_max": 12,
        "nb_b": 5,
        "nb_e": 2,
        "sum_range": (90, 165),
        "extra_label": "Étoiles",
    },
    "loto": {
        "nom": "Loto",
        "b_max": 49,
        "e_max": 10,
        "nb_b": 5,
        "nb_e": 1,
        "sum_range": (75, 175),
        "extra_label": "Chance",
    },
}

PROFILS = {
    "🧠 Ensemble adaptatif": "Combine momentum, fréquence, retard normalisé et stabilité. Heuristique composite.",
    "🚫 Anti-partage": "Favorise les numéros > 31 pour limiter le risque de partage lié aux dates de naissance.",
    "🎯 Équilibré": "Pondération presque uniforme ; priorité à la structure de grille et à la stabilité statistique.",
    "🔥 Momentum": "Accent sur les numéros les plus présents dans la fenêtre récente.",
    "🧊 Retard": "Accent sur les numéros dont l'écart depuis la dernière sortie est élevé.",
    "⚖️ Paritaire": "Pondération sobre + contrainte forte 2/3 ou 3/2 pair/impair.",
}


# ============================================================
# 2. OUTILS MATHÉMATIQUES
# ============================================================
def normal_two_sided_p(z: float) -> float:
    """p-value bilatérale via approximation normale, sans dépendance SciPy."""
    return float(math.erfc(abs(float(z)) / math.sqrt(2.0)))


def fdr_bh(p_values):
    """Correction de Benjamini-Hochberg (FDR)."""
    p = np.asarray(p_values, dtype=float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order]
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0, 1)
    out = np.empty_like(adjusted)
    out[order] = adjusted
    return out


def calc_entropy(grille, b_max):
    g = sorted(list(grille))
    if not g:
        return 0.0
    gaps = [g[0]] + [g[i] - g[i - 1] for i in range(1, len(g))] + [(b_max + 1) - g[-1]]
    total = sum(gaps)
    if total <= 0:
        return 0.0
    return float(-sum((gap / total) * np.log2(gap / total) for gap in gaps if gap > 0))


def get_geometry_score(grille):
    rows = [(n - 1) // 10 for n in grille]
    cols = [(n - 1) % 10 for n in grille]
    return float(round(min(10.0, (np.std(rows) + np.std(cols)) * 2.2), 1))


def theoretical_sum_stats(jeu):
    """Moyenne et variance théoriques de la somme d'un échantillon sans remise."""
    n = jeu["b_max"]
    k = jeu["nb_b"]
    mean_one = (n + 1) / 2
    pop_var = (n**2 - 1) / 12
    var_sum = k * pop_var * ((n - k) / (n - 1))
    return k * mean_one, var_sum


def rank01(values):
    s = pd.Series(np.asarray(values, dtype=float))
    if s.nunique(dropna=True) <= 1:
        return np.full(len(s), 0.5)
    return s.rank(method="average", pct=True).to_numpy(dtype=float)


# ============================================================
# 3. IMPORT / VALIDATION CSV
# ============================================================
def normalize_name(name):
    txt = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    txt = txt.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", txt)


@st.cache_data(show_spinner=False)
def read_raw_csv(file_content):
    if not file_content:
        return None

    attempts = [
        {"sep": None, "engine": "python", "encoding": "utf-8-sig"},
        {"sep": ";", "engine": "python", "encoding": "utf-8-sig"},
        {"sep": ",", "engine": "python", "encoding": "utf-8-sig"},
        {"sep": "\t", "engine": "python", "encoding": "utf-8-sig"},
        {"sep": ";", "engine": "python", "encoding": "latin-1"},
    ]
    last_error = None
    for kwargs in attempts:
        try:
            df = pd.read_csv(io.BytesIO(file_content), on_bad_lines="skip", **kwargs)
            if df.shape[1] >= 2:
                df.columns = [str(c).strip() for c in df.columns]
                return df
        except Exception as exc:
            last_error = exc
    raise ValueError(f"CSV illisible : {last_error}")


def guess_mapping(raw, jeu):
    cols = list(raw.columns)
    norm = {c: normalize_name(c) for c in cols}

    ball_cols = []
    for i in range(1, jeu["nb_b"] + 1):
        aliases = {
            f"b{i}", f"boule{i}", f"numero{i}", f"num{i}", f"n{i}",
            f"ball{i}", f"number{i}",
        }
        found = next((c for c in cols if norm[c] in aliases and c not in ball_cols), None)
        if found:
            ball_cols.append(found)

    extra_cols = []
    for i in range(1, jeu["nb_e"] + 1):
        aliases = {
            f"e{i}", f"etoile{i}", f"star{i}", f"chance{i}",
            f"numerochance{i}", f"luckynumber{i}",
        }
        if jeu["nb_e"] == 1:
            aliases |= {"chance", "numerochance", "luckynumber"}
        found = next((c for c in cols if norm[c] in aliases and c not in extra_cols and c not in ball_cols), None)
        if found:
            extra_cols.append(found)

    # Fallback prudent : colonnes majoritairement numériques et dans la plage du jeu.
    numeric_candidates = []
    for c in cols:
        if c in ball_cols or c in extra_cols:
            continue
        if any(token in norm[c] for token in ["date", "annee", "year", "jour", "month", "mois", "rang", "gain"]):
            continue
        vals = pd.to_numeric(raw[c], errors="coerce")
        valid_ratio = vals.notna().mean()
        if valid_ratio < 0.75:
            continue
        if vals.dropna().between(1, max(jeu["b_max"], jeu["e_max"])).mean() >= 0.85:
            numeric_candidates.append(c)

    for c in numeric_candidates:
        if len(ball_cols) < jeu["nb_b"]:
            ball_cols.append(c)
        elif len(extra_cols) < jeu["nb_e"]:
            extra_cols.append(c)

    date_candidates = [c for c in cols if any(t in norm[c] for t in ["date", "tirage", "drawdate"])]
    date_col = date_candidates[0] if date_candidates else None
    return ball_cols[: jeu["nb_b"]], extra_cols[: jeu["nb_e"]], date_col


def prepare_archive(raw, jeu, ball_cols, extra_cols, date_col=None, row_order="Plus récent en premier"):
    if len(ball_cols) != jeu["nb_b"]:
        raise ValueError(f"Il faut sélectionner exactement {jeu['nb_b']} colonnes de boules.")
    if len(extra_cols) != jeu["nb_e"]:
        raise ValueError(f"Il faut sélectionner exactement {jeu['nb_e']} colonne(s) secondaire(s).")
    if len(set(ball_cols + extra_cols)) != len(ball_cols + extra_cols):
        raise ValueError("Une même colonne ne peut pas être utilisée deux fois.")

    clean = pd.DataFrame(index=raw.index)
    for i, c in enumerate(ball_cols, start=1):
        clean[f"b{i}"] = pd.to_numeric(raw[c], errors="coerce")
    for i, c in enumerate(extra_cols, start=1):
        clean[f"e{i}"] = pd.to_numeric(raw[c], errors="coerce")

    parsed_date = None
    if date_col and date_col in raw.columns:
        parsed_date = pd.to_datetime(raw[date_col], errors="coerce", dayfirst=True)
        if parsed_date.notna().mean() >= 0.5:
            clean["draw_date"] = parsed_date

    before = len(clean)
    required = [f"b{i}" for i in range(1, jeu["nb_b"] + 1)] + [f"e{i}" for i in range(1, jeu["nb_e"] + 1)]
    clean = clean.dropna(subset=required).copy()

    for c in required:
        clean[c] = clean[c].astype(int)

    ball_names = [f"b{i}" for i in range(1, jeu["nb_b"] + 1)]
    extra_names = [f"e{i}" for i in range(1, jeu["nb_e"] + 1)]

    valid_b_range = clean[ball_names].apply(lambda s: s.between(1, jeu["b_max"])).all(axis=1)
    valid_e_range = clean[extra_names].apply(lambda s: s.between(1, jeu["e_max"])).all(axis=1)
    unique_b = clean[ball_names].nunique(axis=1) == jeu["nb_b"]
    unique_e = clean[extra_names].nunique(axis=1) == jeu["nb_e"]
    clean = clean[valid_b_range & valid_e_range & unique_b & unique_e].copy()

    # Tri chronologique explicite : index 0 = tirage le plus récent.
    if "draw_date" in clean.columns and clean["draw_date"].notna().any():
        clean = clean.sort_values("draw_date", ascending=False)
    elif row_order == "Plus ancien en premier":
        clean = clean.iloc[::-1]

    clean = clean.reset_index(drop=True)
    dropped = before - len(clean)

    if len(clean) < 10:
        raise ValueError("Archive insuffisante après validation : moins de 10 tirages exploitables.")

    return clean, {"rows_raw": before, "rows_clean": len(clean), "dropped": dropped}


@st.cache_data(show_spinner=False)
def demo_archive(jid, rows=400, seed=42):
    """Démo explicite, déterministe. Jamais utilisée silencieusement après une erreur d'import."""
    jeu = JEUX[jid]
    rng = np.random.default_rng(seed)
    data = []
    start = pd.Timestamp.today().normalize()
    for i in range(rows):
        balls = sorted(rng.choice(np.arange(1, jeu["b_max"] + 1), jeu["nb_b"], replace=False).tolist())
        extras = sorted(rng.choice(np.arange(1, jeu["e_max"] + 1), jeu["nb_e"], replace=False).tolist())
        row = {f"b{j + 1}": balls[j] for j in range(jeu["nb_b"])}
        row.update({f"e{j + 1}": extras[j] for j in range(jeu["nb_e"])} )
        row["draw_date"] = start - pd.Timedelta(days=i * 3)
        data.append(row)
    return pd.DataFrame(data)


# ============================================================
# 4. STATISTIQUES PAR NUMÉRO
# ============================================================
@st.cache_data(show_spinner=False)
def get_full_stats(df, max_val, picks_per_draw, prefix="b", recent_window=30):
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols:
        return {}

    matrix = df[cols].to_numpy(dtype=int)
    total = len(df)
    p_theoretical = picks_per_draw / max_val
    expected = total * p_theoretical
    recent_n = max(1, min(int(recent_window), total))

    raw = {}
    pvals = []

    for n in range(1, max_val + 1):
        pres = np.any(matrix == n, axis=1)
        freq = int(np.sum(pres))
        recent_freq = int(np.sum(pres[:recent_n]))
        recent_rate = recent_freq / recent_n
        archive_rate = freq / total

        var = total * p_theoretical * (1 - p_theoretical)
        z = (freq - expected) / math.sqrt(var) if var > 0 else 0.0
        p_value = normal_two_sided_p(z)
        gap = next((i for i, x in enumerate(pres) if x), total)
        expected_failures = (1 - p_theoretical) / p_theoretical if p_theoretical > 0 else total

        raw[n] = {
            "freq": freq,
            "expected": expected,
            "archive_rate": archive_rate,
            "heat": archive_rate * 100,
            "recent_freq": recent_freq,
            "recent_rate": recent_rate,
            "vel": recent_rate * 100,
            "momentum": recent_rate / p_theoretical if p_theoretical > 0 else 1.0,
            "freq_ratio": freq / expected if expected > 0 else 1.0,
            "z": float(z),
            "p": float(p_value),
            "gap": int(gap),
            "gap_ratio": float(gap / expected_failures) if expected_failures > 0 else 0.0,
        }
        pvals.append(p_value)

    qvals = fdr_bh(pvals)
    for idx, n in enumerate(range(1, max_val + 1)):
        q = float(qvals[idx])
        z = raw[n]["z"]
        if q < 0.05 and z > 0:
            status = "EXCÈS FDR 🔥"
        elif q < 0.05 and z < 0:
            status = "DÉFICIT FDR 🧊"
        else:
            status = "COMPATIBLE ⚖️"
        raw[n]["q"] = q
        raw[n]["status"] = status

    return raw


def stats_frame(stats):
    return pd.DataFrame(
        [
            {
                "N°": n,
                "Fréq.": s["freq"],
                "Attendu": round(s["expected"], 2),
                "Archive %": round(s["heat"], 2),
                "Récent %": round(s["vel"], 2),
                "Momentum": round(s["momentum"], 2),
                "Écart": s["gap"],
                "Z": round(s["z"], 2),
                "p": s["p"],
                "q FDR": s["q"],
                "État": s["status"],
            }
            for n, s in stats.items()
        ]
    )


# ============================================================
# 5. MOTEUR DE PROFILS / PONDÉRATION
# ============================================================
def build_weights(stats, profile, strength=0.75, anti_share_threshold=31, allow_anti_share=True):
    nums = np.array(sorted(stats.keys()), dtype=int)
    if len(nums) == 0:
        return nums, np.array([], dtype=float)

    momentum = np.array([stats[n]["momentum"] for n in nums], dtype=float)
    freq_ratio = np.array([stats[n]["freq_ratio"] for n in nums], dtype=float)
    gap_ratio = np.array([stats[n]["gap_ratio"] for n in nums], dtype=float)
    z = np.array([stats[n]["z"] for n in nums], dtype=float)

    r_m = rank01(momentum)
    r_f = rank01(freq_ratio)
    r_g = rank01(gap_ratio)
    r_stability = rank01(-np.abs(freq_ratio - 1.0))
    r_zpos = rank01(np.maximum(z, 0))

    if profile == "🧠 Ensemble adaptatif":
        score = 0.35 * r_m + 0.20 * r_f + 0.20 * r_g + 0.15 * r_stability + 0.10 * r_zpos
    elif profile == "🚫 Anti-partage":
        if allow_anti_share:
            high = (nums > anti_share_threshold).astype(float)
            score = 0.20 * r_stability + 0.15 * r_m + 0.65 * high
        else:
            score = 0.60 * r_stability + 0.40 * r_m
    elif profile == "🎯 Équilibré":
        score = 0.70 * r_stability + 0.15 * r_m + 0.15 * r_g
    elif profile == "🔥 Momentum":
        score = 0.75 * r_m + 0.15 * r_f + 0.10 * r_zpos
    elif profile == "🧊 Retard":
        score = 0.80 * r_g + 0.10 * r_stability + 0.10 * r_f
    elif profile == "⚖️ Paritaire":
        score = 0.75 * r_stability + 0.25 * r_m
    else:
        score = np.full(len(nums), 0.5)

    # Transformation douce : évite les probabilités extrêmes et les poids nuls.
    centered = score - np.mean(score)
    heuristic = np.exp(np.clip(centered * 2.2, -2.0, 2.0))
    heuristic = heuristic / np.mean(heuristic)
    strength = float(np.clip(strength, 0.0, 1.0))
    weights = (1.0 - strength) * np.ones_like(heuristic) + strength * heuristic
    weights = np.clip(weights, 1e-6, None)
    return nums, weights


def strategy_score(grid, nums, weights):
    lookup = {int(n): float(w) for n, w in zip(nums, weights)}
    selected = np.array([lookup.get(int(n), 1.0) for n in grid], dtype=float)
    if len(selected) == 0:
        return 0.0
    # Percentile implicite par rapport au vecteur complet : score descriptif, pas probabilité de gain.
    rank_map = {int(n): r for n, r in zip(nums, rank01(weights))}
    return float(np.mean([rank_map.get(int(n), 0.5) for n in grid]) * 100)


def sample_grid(
    rng,
    nums,
    weights,
    k,
    sum_filter=None,
    parity_balanced=False,
    exclusions=None,
    previous_grids=None,
    max_overlap=None,
    attempts=4000,
):
    exclusions = set(exclusions or [])
    previous_grids = previous_grids or []

    w = np.array(weights, dtype=float).copy()
    for ex in exclusions:
        idx = np.where(nums == ex)[0]
        if len(idx):
            w[idx[0]] = 0.0

    if np.count_nonzero(w > 0) < k:
        raise ValueError("Trop de numéros exclus pour générer une grille valide.")

    p = w / np.sum(w)
    for _ in range(attempts):
        g = sorted(rng.choice(nums, k, replace=False, p=p).astype(int).tolist())
        if sum_filter and not (sum_filter[0] <= sum(g) <= sum_filter[1]):
            continue
        if parity_balanced:
            evens = sum(1 for n in g if n % 2 == 0)
            if evens not in (2, 3):
                continue
        if max_overlap is not None and previous_grids:
            if any(len(set(g).intersection(prev)) > max_overlap for prev in previous_grids):
                continue
        return g

    raise ValueError("Aucune grille ne satisfait les contraintes. Élargissez les filtres.")


def generate_portfolio(
    jeu,
    stats_b,
    stats_e,
    profile,
    nb_grids,
    strength,
    diversify,
    sum_filter,
    parity_balanced,
    exclusions,
    max_overlap,
    seed,
):
    rng = np.random.default_rng(int(seed))
    nums_b, base_w_b = build_weights(stats_b, profile, strength=strength, allow_anti_share=True)
    nums_e, base_w_e = build_weights(stats_e, profile, strength=strength, allow_anti_share=False)

    results = []
    previous = []
    use_counts = {int(n): 0 for n in nums_b}

    force_parity = profile == "⚖️ Paritaire"

    for _ in range(nb_grids):
        w_b = base_w_b.copy()
        if diversify:
            for i, n in enumerate(nums_b):
                if use_counts[int(n)] > 0:
                    w_b[i] *= 0.18 ** use_counts[int(n)]

        g = sample_grid(
            rng=rng,
            nums=nums_b,
            weights=w_b,
            k=jeu["nb_b"],
            sum_filter=sum_filter,
            parity_balanced=(parity_balanced or force_parity),
            exclusions=exclusions,
            previous_grids=previous,
            max_overlap=max_overlap if diversify else None,
        )

        for n in g:
            use_counts[int(n)] += 1
        previous.append(set(g))

        e = sorted(rng.choice(nums_e, jeu["nb_e"], replace=False, p=base_w_e / base_w_e.sum()).astype(int).tolist())
        results.append(
            {
                "balls": g,
                "extras": e,
                "score": strategy_score(g, nums_b, base_w_b),
                "extra_score": strategy_score(e, nums_e, base_w_e),
            }
        )

    return results


# ============================================================
# 6. VISUALISATIONS
# ============================================================
def draw_radar_card(grille, stats_b, jeu):
    recent = np.mean([stats_b[n]["momentum"] for n in grille])
    recent = float(np.clip(recent / 2.0, 0, 1))
    anti = sum(1 for n in grille if n > 31) / len(grille)
    entropy = float(np.clip(calc_entropy(grille, jeu["b_max"]) / 3.0, 0, 1))
    geo = float(np.clip(get_geometry_score(grille) / 10.0, 0, 1))
    evens = sum(1 for n in grille if n % 2 == 0)
    parity = 1.0 if evens in (2, 3) else max(0.0, 1.0 - abs(evens - 2.5) / 2.5)

    vals = [recent, anti, entropy, geo, parity, recent]
    axes = ["MOMENTUM", "ANTI-PARTAGE", "ENTROPIE", "GÉO", "PARITÉ", "MOMENTUM"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=vals,
            theta=axes,
            fill="toself",
            line_color="#fbbf24",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 1])),
        showlegend=False,
        height=210,
        margin=dict(l=30, r=30, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    return fig


def pair_analysis(df, jeu):
    bcols = [f"b{i}" for i in range(1, jeu["nb_b"] + 1)]
    n = jeu["b_max"]
    matrix = np.zeros((n, n), dtype=float)
    freq = np.zeros(n, dtype=float)

    for row in df[bcols].to_numpy(dtype=int):
        values = sorted(set(int(x) for x in row))
        for x in values:
            freq[x - 1] += 1
        for a, b in combinations(values, 2):
            matrix[a - 1, b - 1] += 1
            matrix[b - 1, a - 1] += 1

    total = len(df)
    k = jeu["nb_b"]
    correction = ((k - 1) / k) * (n / (n - 1))
    lift = np.ones_like(matrix)

    for i in range(n):
        for j in range(n):
            if i == j:
                lift[i, j] = 1.0
                continue
            expected = total * (freq[i] / total) * (freq[j] / total) * correction if total else 0
            lift[i, j] = matrix[i, j] / expected if expected > 0 else 0.0

    theoretical_pair_expected = total * (k * (k - 1) / (n * (n - 1)))
    return matrix, lift, theoretical_pair_expected


# ============================================================
# 7. BACKTEST WALK-FORWARD SANS FUITE D'INFORMATION
# ============================================================
@st.cache_data(show_spinner=False)
def walk_forward_backtest(
    df,
    jid,
    profile,
    depth,
    tickets_per_draw,
    recent_window,
    strength,
    use_sum_filter,
    use_parity,
    seed,
):
    jeu = JEUX[jid]
    min_train = max(40, recent_window + 10)
    max_eval = min(int(depth), max(0, len(df) - min_train))
    if max_eval <= 0:
        return pd.DataFrame()

    bcols = [f"b{i}" for i in range(1, jeu["nb_b"] + 1)]
    ecols = [f"e{i}" for i in range(1, jeu["nb_e"] + 1)]
    rows = []

    for idx in range(max_eval):
        target = df.iloc[idx]
        # Crucial : uniquement les tirages PLUS ANCIENS que le tirage testé.
        train = df.iloc[idx + 1 :].reset_index(drop=True)

        stats_b = get_full_stats(train, jeu["b_max"], jeu["nb_b"], "b", recent_window)
        stats_e = get_full_stats(train, jeu["e_max"], jeu["nb_e"], "e", recent_window)

        nums_b, w_b = build_weights(stats_b, profile, strength=strength, allow_anti_share=True)
        nums_e, w_e = build_weights(stats_e, profile, strength=strength, allow_anti_share=False)

        rng_s = np.random.default_rng(int(seed) + idx * 1009)
        rng_r = np.random.default_rng(int(seed) + 99991 + idx * 1013)

        target_b = set(int(target[c]) for c in bcols)
        target_e = set(int(target[c]) for c in ecols)
        sum_filter = jeu["sum_range"] if use_sum_filter else None
        parity = use_parity or profile == "⚖️ Paritaire"

        strat_hits = []
        rand_hits = []

        for _ in range(int(tickets_per_draw)):
            g_s = sample_grid(
                rng_s,
                nums_b,
                w_b,
                jeu["nb_b"],
                sum_filter=sum_filter,
                parity_balanced=parity,
            )
            e_s = sorted(rng_s.choice(nums_e, jeu["nb_e"], replace=False, p=w_e / w_e.sum()).astype(int).tolist())
            strat_hits.append((len(set(g_s) & target_b), len(set(e_s) & target_e)))

            # Baseline strictement comparable : mêmes filtres, poids uniformes.
            g_r = sample_grid(
                rng_r,
                nums_b,
                np.ones_like(w_b),
                jeu["nb_b"],
                sum_filter=sum_filter,
                parity_balanced=parity,
            )
            e_r = sorted(rng_r.choice(nums_e, jeu["nb_e"], replace=False).astype(int).tolist())
            rand_hits.append((len(set(g_r) & target_b), len(set(e_r) & target_e)))

        best_s = max(strat_hits, key=lambda x: (x[0], x[1]))
        best_r = max(rand_hits, key=lambda x: (x[0], x[1]))

        rows.append(
            {
                "index_test": idx,
                "strat_b": best_s[0],
                "strat_e": best_s[1],
                "random_b": best_r[0],
                "random_e": best_r[1],
                "strat_total": best_s[0] + best_s[1],
                "random_total": best_r[0] + best_r[1],
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 8. APPLICATION
# ============================================================
def main():
    st.sidebar.markdown(
        "<h1 style='color:#fbbf24;text-align:center;'>🧬 SMART-LOTO V37</h1>",
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Evidence Engine — analyse descriptive + stratégies testables")

    jid = st.sidebar.selectbox("JEU", list(JEUX.keys()), format_func=lambda x: JEUX[x]["nom"])
    jeu = JEUX[jid]

    file = st.sidebar.file_uploader("📥 ARCHIVE CSV", type="csv")
    recent_window = st.sidebar.slider("Fenêtre récente", 10, 100, 30, 5)

    # ---------- Chargement ----------
    if file:
        try:
            raw = read_raw_csv(file.getvalue())
            guessed_b, guessed_e, guessed_date = guess_mapping(raw, jeu)

            with st.sidebar.expander("🧭 Mapping CSV", expanded=False):
                st.caption("Vérifie les colonnes détectées. L'index 0 doit devenir le tirage le plus récent.")
                ball_cols = st.multiselect(
                    f"Colonnes boules ({jeu['nb_b']})",
                    list(raw.columns),
                    default=guessed_b,
                    max_selections=jeu["nb_b"],
                )
                extra_cols = st.multiselect(
                    f"Colonnes {jeu['extra_label'].lower()} ({jeu['nb_e']})",
                    [c for c in raw.columns if c not in ball_cols],
                    default=[c for c in guessed_e if c not in ball_cols],
                    max_selections=jeu["nb_e"],
                )
                date_options = ["— aucune —"] + list(raw.columns)
                default_idx = date_options.index(guessed_date) if guessed_date in date_options else 0
                date_col_choice = st.selectbox("Colonne date", date_options, index=default_idx)
                row_order = st.radio(
                    "Si aucune date exploitable",
                    ["Plus récent en premier", "Plus ancien en premier"],
                )

            date_col = None if date_col_choice == "— aucune —" else date_col_choice
            df, import_info = prepare_archive(raw, jeu, ball_cols, extra_cols, date_col, row_order)
            st.sidebar.success(f"{import_info['rows_clean']} tirages valides")
            if import_info["dropped"]:
                st.sidebar.warning(f"{import_info['dropped']} ligne(s) rejetée(s)")
        except Exception as exc:
            st.error(f"Import impossible : {exc}")
            st.stop()
    else:
        df = demo_archive(jid)
        import_info = {"rows_raw": len(df), "rows_clean": len(df), "dropped": 0}
        st.sidebar.warning("MODE DÉMO — archive synthétique, graine fixe 42")

    bcols = [f"b{i}" for i in range(1, jeu["nb_b"] + 1)]
    ecols = [f"e{i}" for i in range(1, jeu["nb_e"] + 1)]
    df = df.copy()
    df["total_sum"] = df[bcols].sum(axis=1)

    stats_b = get_full_stats(df, jeu["b_max"], jeu["nb_b"], "b", recent_window)
    stats_e = get_full_stats(df, jeu["e_max"], jeu["nb_e"], "e", recent_window)

    menu = st.sidebar.radio(
        "NAVIGATION",
        ["📊 Dashboard", "🎯 Générateur", "➕ Sommes", "🧬 Anomalies", "🔗 Clusters", "🧪 Backtest"],
    )

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------
    if menu == "📊 Dashboard":
        st.markdown(f"<div class='main-header'>Evidence Dashboard — {jeu['nom']}</div>", unsafe_allow_html=True)

        mu_sum, var_sum = theoretical_sum_stats(jeu)
        real_mean_sum = float(df["total_sum"].mean())
        se_mean = math.sqrt(var_sum / len(df))
        z_mean = (real_mean_sum - mu_sum) / se_mean if se_mean > 0 else 0.0
        p_mean = normal_two_sided_p(z_mean)
        anomalies = sum(1 for s in stats_b.values() if s["q"] < 0.05)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Archive", f"{len(df)} tirages")
        c2.metric("Somme moyenne", f"{real_mean_sum:.2f}", delta=f"théorie {mu_sum:.2f}")
        c3.metric("Z moyenne des sommes", f"{z_mean:.2f}", delta=f"p≈{p_mean:.3f}")
        c4.metric("Anomalies FDR 5%", str(anomalies), delta="à examiner" if anomalies else "aucune détectée")

        st.caption(
            "Une anomalie descriptive ou un écart de fréquence n'implique pas que le prochain tirage soit prédictible. "
            "Les tests multiples sont corrigés par Benjamini-Hochberg (FDR)."
        )

        for title, s_dict, mx, picks in [
            ("BOULES", stats_b, jeu["b_max"], jeu["nb_b"]),
            (jeu["extra_label"].upper(), stats_e, jeu["e_max"], jeu["nb_e"]),
        ]:
            st.subheader(f"Analyse fréquentielle — {title}")
            x = list(range(1, mx + 1))
            y_recent = [s_dict[n]["vel"] for n in x]
            y_archive = [s_dict[n]["heat"] for n in x]
            expected_pct = 100 * picks / mx

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.68, 0.32])
            fig.add_trace(go.Scatter(x=x, y=y_recent, mode="lines+markers", name="Récent", line=dict(color="#fbbf24", width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=x, y=y_archive, mode="lines", name="Archive", line=dict(color="#60a5fa", width=1.6)), row=1, col=1)
            fig.add_hline(y=expected_pct, line_dash="dash", line_color="#94a3b8", row=1, col=1)
            fig.add_trace(go.Heatmap(z=[[s_dict[n]["z"] for n in x]], x=x, colorscale="RdBu", zmid=0, showscale=False), row=2, col=1)
            fig.update_layout(height=390, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), margin=dict(l=10, r=10, t=20, b=10))
            fig.update_xaxes(dtick=5 if mx > 20 else 1, range=[0.5, mx + 0.5])
            st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------
    # GÉNÉRATEUR
    # --------------------------------------------------------
    elif menu == "🎯 Générateur":
        st.markdown("<div class='main-header'>Générateur Portfolio V37</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2.5])

        min_sum = sum(range(1, jeu["nb_b"] + 1))
        max_sum = sum(range(jeu["b_max"] - jeu["nb_b"] + 1, jeu["b_max"] + 1))

        with c1:
            prof = st.selectbox("Stratégie", list(PROFILS.keys()))
            st.caption(PROFILS[prof])
            nb = st.slider("Grilles", 1, 12, 4)
            strength = st.slider("Force de la pondération", 0, 100, 75, 5) / 100
            diversify = st.checkbox("Diversification du portefeuille", value=True)
            max_overlap = st.slider("Recouvrement max entre deux grilles", 0, 4, 2, disabled=not diversify)
            seed = st.number_input("Graine reproductible", min_value=0, max_value=2_147_483_647, value=20260915, step=1)

            with st.expander("🛠️ Filtres combinatoires"):
                f_sum = st.slider("Somme des numéros", min_sum, max_sum, jeu["sum_range"])
                f_par = st.checkbox("Parité équilibrée (2/3 ou 3/2)", value=True)
                excl = st.multiselect("Bannir des numéros", range(1, jeu["b_max"] + 1))

            btn = st.button("🚀 CALCULER LE PORTEFEUILLE", type="primary", use_container_width=True)

        with c2:
            if btn:
                try:
                    portfolio = generate_portfolio(
                        jeu=jeu,
                        stats_b=stats_b,
                        stats_e=stats_e,
                        profile=prof,
                        nb_grids=nb,
                        strength=strength,
                        diversify=diversify,
                        sum_filter=f_sum,
                        parity_balanced=f_par,
                        exclusions=excl,
                        max_overlap=max_overlap,
                        seed=seed,
                    )

                    for i, item in enumerate(portfolio, start=1):
                        g, et = item["balls"], item["extras"]
                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        st.markdown(f"<b>Grille {i}</b>", unsafe_allow_html=True)
                        b_h = "".join([f'<div class="boule">{b}</div>' for b in g])
                        e_h = "".join([f'<div class="etoile">{e}</div>' for e in et])
                        st.markdown(
                            f'<div style="display:flex;justify-content:center;align-items:center;flex-wrap:wrap;margin-bottom:12px;">'
                            f'{b_h}<div style="width:2px;height:35px;background:#334155;margin:0 15px;"></div>{e_h}</div>',
                            unsafe_allow_html=True,
                        )

                        ca1, ca2 = st.columns([1, 1.1])
                        with ca1:
                            st.plotly_chart(draw_radar_card(g, stats_b, jeu), use_container_width=True)
                        with ca2:
                            sab = sum(1 for n in g if n > 31)
                            evens = sum(1 for n in g if n % 2 == 0)
                            mini = " ".join(
                                [f"<div class='mini-cell {'active' if n in g else ''}'></div>" for n in range(1, jeu["b_max"] + 1)]
                            )
                            st.markdown(
                                f"""
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                                    <div><small class="metric-title">Somme</small><br><b class="metric-value">{sum(g)}</b></div>
                                    <div><small class="metric-title">Score stratégie</small><br><b class="metric-value">{item['score']:.0f}/100</b></div>
                                    <div><small class="metric-title">Pair / Impair</small><br><b class="metric-value">{evens}/{len(g)-evens}</b></div>
                                    <div><small class="metric-title">N° &gt; 31</small><br><b class="metric-value">{sab}/{len(g)}</b></div>
                                    <div style="grid-column:1 / span 2"><small class="metric-title">Ticket</small><br><div class="mini-grid">{mini}</div></div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        st.caption("Le score stratégie mesure l'alignement avec le profil choisi ; ce n'est pas une probabilité de gain.")
                        st.markdown("</div>", unsafe_allow_html=True)
                except Exception as exc:
                    st.error(str(exc))

    # --------------------------------------------------------
    # SOMMES
    # --------------------------------------------------------
    elif menu == "➕ Sommes":
        st.markdown("<div class='main-header'>Analyse des Sommes</div>", unsafe_allow_html=True)
        sums = df["total_sum"]
        mu_sum, var_sum = theoretical_sum_stats(jeu)
        sigma_sum = math.sqrt(var_sum)
        last_z = (float(sums.iloc[0]) - mu_sum) / sigma_sum if sigma_sum > 0 else 0.0

        col1, col2 = st.columns([1, 2.5])
        with col1:
            st.metric("Moyenne archive", f"{sums.mean():.2f}")
            st.metric("Moyenne théorique", f"{mu_sum:.2f}")
            st.metric("Z du dernier tirage", f"{last_z:.2f}")
            st.info("Le Z-score mesure l'atypicité de la somme. Une valeur extrême ne prédit pas un retour à la moyenne au tirage suivant.")

        with col2:
            fig_gauss = go.Figure()
            fig_gauss.add_trace(go.Histogram(x=sums, nbinsx=35, marker_color="#fbbf24", opacity=0.65, name="Archive"))
            fig_gauss.add_vline(x=mu_sum, line_dash="dash", line_color="#60a5fa", annotation_text="Moyenne théorique")
            fig_gauss.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_gauss, use_container_width=True)

        st.subheader("Tendance chronologique — 100 derniers tirages")
        recent_sums = sums.head(100).iloc[::-1].reset_index(drop=True)
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(y=recent_sums, mode="lines", line=dict(color="#64748b"), name="Somme"))
        fig_trend.add_trace(go.Scatter(y=recent_sums.rolling(window=5).mean(), mode="lines", line=dict(color="#fbbf24", width=3), name="Moyenne mobile 5"))
        fig_trend.add_hrect(y0=jeu["sum_range"][0], y1=jeu["sum_range"][1], fillcolor="green", opacity=0.08)
        fig_trend.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        st.plotly_chart(fig_trend, use_container_width=True)

    # --------------------------------------------------------
    # ANOMALIES
    # --------------------------------------------------------
    elif menu == "🧬 Anomalies":
        st.markdown("<div class='main-header'>Audit Fréquentiel FDR</div>", unsafe_allow_html=True)
        st.caption(
            "Le test compare la fréquence observée à la fréquence marginale théorique. La p-value utilise une approximation normale ; "
            "la colonne q applique Benjamini-Hochberg pour contrôler les tests multiples."
        )

        tab_b, tab_e = st.tabs(["Boules", jeu["extra_label"]])
        with tab_b:
            table_b = stats_frame(stats_b)
            table_b["|Z|"] = table_b["Z"].abs()
            st.dataframe(table_b.sort_values(["q FDR", "|Z|"], ascending=[True, False]).drop(columns="|Z|"), use_container_width=True, hide_index=True)
        with tab_e:
            table_e = stats_frame(stats_e)
            table_e["|Z|"] = table_e["Z"].abs()
            st.dataframe(table_e.sort_values(["q FDR", "|Z|"], ascending=[True, False]).drop(columns="|Z|"), use_container_width=True, hide_index=True)

    # --------------------------------------------------------
    # CLUSTERS
    # --------------------------------------------------------
    elif menu == "🔗 Clusters":
        st.markdown("<div class='main-header'>Cooccurrences & Affinités</div>", unsafe_allow_html=True)
        matrix, lift, expected_pair = pair_analysis(df, jeu)
        st.caption(
            f"Chaque paire aurait environ {expected_pair:.2f} occurrences attendues sous un tirage uniforme. "
            "Le lift corrige aussi les fréquences marginales et la dépendance mécanique due au tirage sans remise."
        )

        tab1, tab2, tab3 = st.tabs(["🔥 Matrice brute", "🧠 Lift ajusté", "👯 Paires & partenaires"])
        with tab1:
            fig = go.Figure(data=go.Heatmap(z=matrix, colorscale="Inferno"))
            fig.update_layout(height=650, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig = go.Figure(data=go.Heatmap(z=lift, colorscale="RdBu", zmid=1))
            fig.update_layout(height=650, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            pairs = []
            for i in range(jeu["b_max"]):
                for j in range(i + 1, jeu["b_max"]):
                    if matrix[i, j] > 0:
                        pairs.append(
                            {
                                "Paire": f"{i+1} + {j+1}",
                                "Occurrences": int(matrix[i, j]),
                                "Lift": round(float(lift[i, j]), 2),
                            }
                        )
            pairs_df = pd.DataFrame(pairs)
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Top sur-affinités")
                if not pairs_df.empty:
                    st.dataframe(pairs_df.sort_values(["Lift", "Occurrences"], ascending=[False, False]).head(15), use_container_width=True, hide_index=True)
            with c2:
                st.subheader("Partenaire d'un numéro")
                n_s = st.selectbox("Numéro", range(1, jeu["b_max"] + 1))
                idx = n_s - 1
                partner_rows = [
                    {"Partenaire": j + 1, "Occurrences": int(matrix[idx, j]), "Lift": round(float(lift[idx, j]), 2)}
                    for j in range(jeu["b_max"]) if j != idx and matrix[idx, j] > 0
                ]
                if partner_rows:
                    partners_df = pd.DataFrame(partner_rows).sort_values(["Lift", "Occurrences"], ascending=[False, False]).head(12)
                    st.dataframe(partners_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Aucun partenaire observé dans l'archive.")
            st.caption("Une cooccurrence élevée est descriptive : elle ne démontre pas une dépendance exploitable sur les tirages futurs.")

    # --------------------------------------------------------
    # BACKTEST
    # --------------------------------------------------------
    elif menu == "🧪 Backtest":
        st.markdown("<div class='main-header'>Backtest Walk-Forward</div>", unsafe_allow_html=True)
        st.caption(
            "Chaque tirage testé est simulé comme s'il était encore inconnu : le moteur n'utilise que les tirages plus anciens. "
            "La baseline aléatoire reçoit exactement les mêmes filtres combinatoires."
        )

        min_train = max(40, recent_window + 10)
        max_depth = max(1, min(100, len(df) - min_train))
        if max_depth < 5:
            st.warning(f"Il faut au moins {min_train + 5} tirages pour un backtest utile avec cette fenêtre récente.")
            return

        col1, col2 = st.columns([1, 2.2])
        with col1:
            prof_t = st.selectbox("Stratégie", list(PROFILS.keys()), key="bt_prof")
            depth = st.slider("Tirages testés", 5, max_depth, min(40, max_depth))
            tickets = st.slider("Tickets par tirage", 1, 10, 3)
            strength_t = st.slider("Force pondération", 0, 100, 75, 5, key="bt_strength") / 100
            use_sum = st.checkbox("Appliquer la plage de somme", value=True)
            use_par = st.checkbox("Appliquer la parité équilibrée", value=True)
            seed_t = st.number_input("Graine backtest", min_value=0, max_value=2_147_483_647, value=37037, step=1)
            run = st.button("🚀 LANCER LE BACKTEST", type="primary", use_container_width=True)

        with col2:
            if run:
                with st.spinner("Backtest walk-forward..."):
                    try:
                        bt = walk_forward_backtest(
                            df=df,
                            jid=jid,
                            profile=prof_t,
                            depth=depth,
                            tickets_per_draw=tickets,
                            recent_window=recent_window,
                            strength=strength_t,
                            use_sum_filter=use_sum,
                            use_parity=use_par,
                            seed=seed_t,
                        )
                    except Exception as exc:
                        st.error(f"Backtest interrompu : {exc}")
                        bt = pd.DataFrame()

                if not bt.empty:
                    avg_s = bt["strat_b"].mean()
                    avg_r = bt["random_b"].mean()
                    delta = avg_s - avg_r
                    paired = (bt["strat_b"] - bt["random_b"]).astype(float)
                    if len(paired) > 1:
                        se_delta = float(paired.std(ddof=1) / math.sqrt(len(paired)))
                        ci_low, ci_high = delta - 1.96 * se_delta, delta + 1.96 * se_delta
                    else:
                        ci_low = ci_high = delta
                    rate3_s = (bt["strat_b"] >= 3).mean() * 100
                    rate3_r = (bt["random_b"] >= 3).mean() * 100

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Moy. meilleur ticket", f"{avg_s:.3f} boules")
                    m2.metric("Baseline aléatoire", f"{avg_r:.3f} boules")
                    m3.metric("Delta stratégie", f"{delta:+.3f}", delta=f"IC95% [{ci_low:+.2f}; {ci_high:+.2f}]")
                    m4.metric("≥ 3 boules", f"{rate3_s:.1f}%", delta=f"random {rate3_r:.1f}%")

                    counts = pd.DataFrame({
                        "Hits": list(range(jeu["nb_b"] + 1)),
                        "Stratégie": [(bt["strat_b"] == i).sum() for i in range(jeu["nb_b"] + 1)],
                        "Aléatoire": [(bt["random_b"] == i).sum() for i in range(jeu["nb_b"] + 1)],
                    })
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=counts["Hits"], y=counts["Stratégie"], name="Stratégie"))
                    fig.add_trace(go.Bar(x=counts["Hits"], y=counts["Aléatoire"], name="Aléatoire"))
                    fig.update_layout(barmode="group", height=380, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), xaxis_title="Nombre de boules trouvées (meilleur ticket)")
                    st.plotly_chart(fig, use_container_width=True)

                    extra_s = bt["strat_e"].mean()
                    extra_r = bt["random_e"].mean()
                    st.caption(
                        f"Composante {jeu['extra_label'].lower()} — moyenne stratégie : {extra_s:.3f} ; baseline : {extra_r:.3f}. "
                        "Un delta positif sur un petit échantillon ne suffit pas à établir un avantage réel : augmentez la profondeur et répétez avec plusieurs graines."
                    )

                    with st.expander("Voir les résultats bruts"):
                        st.dataframe(bt, use_container_width=True, hide_index=True)

    with st.sidebar.expander("ℹ️ Méthodologie"):
        st.write(
            "V37 sépare les statistiques descriptives, les heuristiques de sélection et leur évaluation. "
            "Les anomalies fréquentielles utilisent un Z-score marginal et une correction FDR. "
            "Le backtest est walk-forward et évite la fuite d'information."
        )
        st.write(
            "Les tirages officiels restent conçus pour être aléatoires et indépendants. "
            "Les profils servent à construire et comparer des portefeuilles, pas à garantir une prédiction."
        )


if __name__ == "__main__":
    main()
