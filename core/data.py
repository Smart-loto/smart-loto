import io
import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st

from core.config import JEUX


def normalize_name(name: str) -> str:
    txt = unicodedata.normalize(
        "NFKD",
        str(name),
    ).encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    txt = txt.lower().strip()

    return re.sub(
        r"[^a-z0-9]+",
        "",
        txt,
    )


@st.cache_data(show_spinner=False)
def read_raw_csv(file_content: bytes):
    if not file_content:
        return None

    attempts = [
        {
            "sep": None,
            "engine": "python",
            "encoding": "utf-8-sig",
        },
        {
            "sep": ";",
            "engine": "python",
            "encoding": "utf-8-sig",
        },
        {
            "sep": ",",
            "engine": "python",
            "encoding": "utf-8-sig",
        },
        {
            "sep": "\t",
            "engine": "python",
            "encoding": "utf-8-sig",
        },
        {
            "sep": ";",
            "engine": "python",
            "encoding": "latin-1",
        },
    ]

    last_error = None

    for kwargs in attempts:
        try:
            df = pd.read_csv(
                io.BytesIO(file_content),
                on_bad_lines="skip",
                **kwargs,
            )

            if df.shape[1] >= 2:
                df.columns = [
                    str(c).strip()
                    for c in df.columns
                ]
                return df

        except Exception as exc:
            last_error = exc

    raise ValueError(
        f"CSV illisible : {last_error}"
    )


def guess_mapping(raw: pd.DataFrame, jeu: dict):
    cols = list(raw.columns)

    norm = {
        c: normalize_name(c)
        for c in cols
    }

    ball_cols = []

    for i in range(
        1,
        jeu["nb_b"] + 1,
    ):
        aliases = {
            f"b{i}",
            f"boule{i}",
            f"numero{i}",
            f"num{i}",
            f"n{i}",
            f"ball{i}",
            f"number{i}",
        }

        found = next(
            (
                c
                for c in cols
                if norm[c] in aliases
                and c not in ball_cols
            ),
            None,
        )

        if found:
            ball_cols.append(found)

    extra_cols = []

    for i in range(
        1,
        jeu["nb_e"] + 1,
    ):
        aliases = {
            f"e{i}",
            f"etoile{i}",
            f"star{i}",
            f"chance{i}",
            f"numerochance{i}",
            f"luckynumber{i}",
        }

        if jeu["nb_e"] == 1:
            aliases |= {
                "chance",
                "numerochance",
                "luckynumber",
            }

        found = next(
            (
                c
                for c in cols
                if norm[c] in aliases
                and c not in extra_cols
                and c not in ball_cols
            ),
            None,
        )

        if found:
            extra_cols.append(found)

    numeric_candidates = []

    for c in cols:
        if (
            c in ball_cols
            or c in extra_cols
        ):
            continue

        if any(
            token in norm[c]
            for token in [
                "date",
                "annee",
                "year",
                "jour",
                "month",
                "mois",
                "rang",
                "gain",
                "rapport",
            ]
        ):
            continue

        vals = pd.to_numeric(
            raw[c],
            errors="coerce",
        )

        if vals.notna().mean() < 0.75:
            continue

        non_na = vals.dropna()

        if (
            len(non_na)
            and non_na.between(
                1,
                max(
                    jeu["b_max"],
                    jeu["e_max"],
                ),
            ).mean() >= 0.85
        ):
            numeric_candidates.append(c)

    for c in numeric_candidates:
        if len(ball_cols) < jeu["nb_b"]:
            ball_cols.append(c)

        elif len(extra_cols) < jeu["nb_e"]:
            extra_cols.append(c)

    date_candidates = [
        c
        for c in cols
        if any(
            token in norm[c]
            for token in [
                "date",
                "tirage",
                "drawdate",
            ]
        )
    ]

    date_col = (
        date_candidates[0]
        if date_candidates
        else None
    )

    return (
        ball_cols[: jeu["nb_b"]],
        extra_cols[: jeu["nb_e"]],
        date_col,
    )


def prepare_archive(
    raw: pd.DataFrame,
    jeu: dict,
    ball_cols,
    extra_cols,
    date_col=None,
    row_order="Plus récent en premier",
):
    if len(ball_cols) != jeu["nb_b"]:
        raise ValueError(
            f"Il faut sélectionner exactement "
            f"{jeu['nb_b']} colonnes de boules."
        )

    if len(extra_cols) != jeu["nb_e"]:
        raise ValueError(
            f"Il faut sélectionner exactement "
            f"{jeu['nb_e']} colonne(s) secondaire(s)."
        )

    if (
        len(set(ball_cols + extra_cols))
        != len(ball_cols + extra_cols)
    ):
        raise ValueError(
            "Une même colonne ne peut pas être utilisée deux fois."
        )

    clean = pd.DataFrame(
        index=raw.index
    )

    for i, c in enumerate(
        ball_cols,
        start=1,
    ):
        clean[f"b{i}"] = pd.to_numeric(
            raw[c],
            errors="coerce",
        )

    for i, c in enumerate(
        extra_cols,
        start=1,
    ):
        clean[f"e{i}"] = pd.to_numeric(
            raw[c],
            errors="coerce",
        )

    if (
        date_col
        and date_col in raw.columns
    ):
        parsed_date = pd.to_datetime(
            raw[date_col],
            errors="coerce",
            dayfirst=True,
        )

        if parsed_date.notna().mean() >= 0.5:
            clean["draw_date"] = parsed_date

    before = len(clean)

    required = [
        f"b{i}"
        for i in range(
            1,
            jeu["nb_b"] + 1,
        )
    ] + [
        f"e{i}"
        for i in range(
            1,
            jeu["nb_e"] + 1,
        )
    ]

    clean = clean.dropna(
        subset=required
    ).copy()

    for c in required:
        clean[c] = clean[c].astype(int)

    ball_names = [
        f"b{i}"
        for i in range(
            1,
            jeu["nb_b"] + 1,
        )
    ]

    extra_names = [
        f"e{i}"
        for i in range(
            1,
            jeu["nb_e"] + 1,
        )
    ]

    valid_b_range = clean[
        ball_names
    ].apply(
        lambda s: s.between(
            1,
            jeu["b_max"],
        )
    ).all(axis=1)

    valid_e_range = clean[
        extra_names
    ].apply(
        lambda s: s.between(
            1,
            jeu["e_max"],
        )
    ).all(axis=1)

    unique_b = (
        clean[ball_names].nunique(axis=1)
        == jeu["nb_b"]
    )

    unique_e = (
        clean[extra_names].nunique(axis=1)
        == jeu["nb_e"]
    )

    clean = clean[
        valid_b_range
        & valid_e_range
        & unique_b
        & unique_e
    ].copy()

    # Convention V39 :
    # index 0 = tirage le plus récent.
    if (
        "draw_date" in clean.columns
        and clean["draw_date"].notna().any()
    ):
        clean = clean.sort_values(
            "draw_date",
            ascending=False,
        )

    elif row_order == "Plus ancien en premier":
        clean = clean.iloc[::-1]

    clean = clean.reset_index(
        drop=True
    )

    dropped = before - len(clean)

    if len(clean) < 10:
        raise ValueError(
            "Archive insuffisante après validation : "
            "moins de 10 tirages exploitables."
        )

    return clean, {
        "rows_raw": before,
        "rows_clean": len(clean),
        "dropped": dropped,
    }


@st.cache_data(show_spinner=False)
def demo_archive(
    jid: str,
    rows: int = 400,
    seed: int = 42,
):
    """
    Archive synthétique déterministe.

    Utilisée uniquement comme mode démo.
    """

    jeu = JEUX[jid]
    rng = np.random.default_rng(seed)

    data = []

    start = pd.Timestamp.today().normalize()

    for i in range(rows):
        balls = sorted(
            rng.choice(
                np.arange(
                    1,
                    jeu["b_max"] + 1,
                ),
                jeu["nb_b"],
                replace=False,
            ).tolist()
        )

        extras = sorted(
            rng.choice(
                np.arange(
                    1,
                    jeu["e_max"] + 1,
                ),
                jeu["nb_e"],
                replace=False,
            ).tolist()
        )

        row = {
            f"b{j + 1}": balls[j]
            for j in range(
                jeu["nb_b"]
            )
        }

        row.update(
            {
                f"e{j + 1}": extras[j]
                for j in range(
                    jeu["nb_e"]
                )
            }
        )

        row["draw_date"] = (
            start
            - pd.Timedelta(
                days=i * 3
            )
        )

        data.append(row)

    return pd.DataFrame(data)
