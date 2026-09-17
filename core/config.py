from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

JEUX = {
    "euromillions": {
        "nom": "Euromillions",
        "b_max": 50,
        "e_max": 12,
        "nb_b": 5,
        "nb_e": 2,
        "sum_range": (90, 165),
        "extra_label": "Étoiles",
        "data_file": DATA_DIR / "euromillions.csv",
    },
    "loto": {
        "nom": "Loto",
        "b_max": 49,
        "e_max": 10,
        "nb_b": 5,
        "nb_e": 1,
        "sum_range": (75, 175),
        "extra_label": "Chance",
        "data_file": DATA_DIR / "loto.csv",
    },
}

PROFILS = {
    "🧠 Ensemble adaptatif": (
        "Combine momentum, fréquence, retard normalisé et stabilité. "
        "Heuristique composite à valider par backtest."
    ),
    "🚫 Anti-partage": (
        "Favorise les numéros > 31 pour réduire le risque de partager un gain "
        "avec des grilles basées sur des dates de naissance."
    ),
    "🎯 Équilibré": (
        "Pondération sobre ; priorité à la stabilité statistique "
        "et à la structure de la grille."
    ),
    "🔥 Momentum": (
        "Accent sur les numéros les plus présents dans la fenêtre récente."
    ),
    "🧊 Retard": (
        "Accent sur les numéros dont l'écart depuis la dernière sortie est élevé."
    ),
    "⚖️ Paritaire": (
        "Pondération sobre + contrainte forte 2/3 ou 3/2 pair/impair."
    ),
}

APP_CSS = r"""
<style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap'
    );

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
        background:radial-gradient(
            circle at 30% 30%,
            #3b82f6,
            #1e40af
        );
        border:1px solid #60a5fa;
    }

    .etoile {
        background:radial-gradient(
            circle at 30% 30%,
            #fbbf24,
            #d97706
        );
        border:1px solid #fcd34d;
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

    .mini-cell.active {
        background:#fbbf24;
    }

    label,
    p,
    span,
    .stSlider,
    .stCheckbox {
        color:#fff !important;
    }

    div[data-baseweb="select"] > div {
        background-color:#1e293b !important;
        color:white !important;
        border:1px solid #334155 !important;
    }
    [data-testid="stHeader"] {
    background-color:#0f172a !important;
}

[data-testid="stToolbar"] {
    background-color:transparent !important;
}

[data-testid="stDecoration"] {
    background-color:#fbbf24 !important;
}

header[data-testid="stHeader"] {
    color:#f8fafc !important;
}
</style>
"""
