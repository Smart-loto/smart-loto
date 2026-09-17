import math
from itertools import combinations

import numpy as np
import pandas as pd


def normal_two_sided_p(z: float) -> float:
    """
    p-value bilatérale via approximation normale,
    sans dépendance SciPy.
    """
    return float(
        math.erfc(
            abs(float(z))
            / math.sqrt(2.0)
        )
    )


def fdr_bh(p_values):
    """
    Correction de Benjamini-Hochberg
    pour contrôle du FDR.
    """

    p = np.asarray(
        p_values,
        dtype=float,
    )

    n = len(p)

    if n == 0:
        return p

    order = np.argsort(p)
    ranked = p[order]

    adjusted = (
        ranked
        * n
        / np.arange(
            1,
            n + 1,
        )
    )

    adjusted = np.minimum.accumulate(
        adjusted[::-1]
    )[::-1]

    adjusted = np.clip(
        adjusted,
        0,
        1,
    )

    out = np.empty_like(
        adjusted
    )

    out[order] = adjusted

    return out


def rank01(values):
    s = pd.Series(
        np.asarray(
            values,
            dtype=float,
        )
    )

    if s.nunique(
        dropna=True
    ) <= 1:
        return np.full(
            len(s),
            0.5,
        )

    return s.rank(
        method="average",
        pct=True,
    ).to_numpy(
        dtype=float
    )


def calc_entropy(
    grille,
    b_max,
):
    g = sorted(
        int(x)
        for x in grille
    )

    if not g:
        return 0.0

    gaps = [g[0]]

    gaps += [
        g[i] - g[i - 1]
        for i in range(
            1,
            len(g),
        )
    ]

    gaps += [
        (b_max + 1)
        - g[-1]
    ]

    total = sum(gaps)

    if total <= 0:
        return 0.0

    return float(
        -sum(
            (gap / total)
            * np.log2(
                gap / total
            )
            for gap in gaps
            if gap > 0
        )
    )


def get_geometry_score(
    grille,
):
    if not grille:
        return 0.0

    rows = [
        (int(n) - 1) // 10
        for n in grille
    ]

    cols = [
        (int(n) - 1) % 10
        for n in grille
    ]

    return float(
        round(
            min(
                10.0,
                (
                    np.std(rows)
                    + np.std(cols)
                ) * 2.2,
            ),
            1,
        )
    )


def theoretical_sum_stats(
    jeu,
):
    """
    Moyenne et variance théoriques
    de la somme d'un échantillon
    uniforme sans remise.
    """

    n = jeu["b_max"]
    k = jeu["nb_b"]

    mean_one = (
        n + 1
    ) / 2

    pop_var = (
        n**2 - 1
    ) / 12

    var_sum = (
        k
        * pop_var
        * (
            (n - k)
            / (n - 1)
        )
    )

    return (
        k * mean_one,
        var_sum,
    )


def get_full_stats(
    df,
    max_val,
    picks_per_draw,
    prefix="b",
    recent_window=30,
):
    cols = [
        c
        for c in df.columns
        if c.startswith(prefix)
    ]

    if not cols:
        return {}

    matrix = df[
        cols
    ].to_numpy(
        dtype=int
    )

    total = len(df)

    if total == 0:
        return {}

    p_theoretical = (
        picks_per_draw
        / max_val
    )

    expected = (
        total
        * p_theoretical
    )

    recent_n = max(
        1,
        min(
            int(recent_window),
            total,
        ),
    )

    raw = {}
    pvals = []

    for n in range(
        1,
        max_val + 1,
    ):
        pres = np.any(
            matrix == n,
            axis=1,
        )

        freq = int(
            np.sum(pres)
        )

        recent_freq = int(
            np.sum(
                pres[:recent_n]
            )
        )

        recent_rate = (
            recent_freq
            / recent_n
        )

        archive_rate = (
            freq
            / total
        )

        var = (
            total
            * p_theoretical
            * (
                1
                - p_theoretical
            )
        )

        z = (
            (freq - expected)
            / math.sqrt(var)
            if var > 0
            else 0.0
        )

        p_value = normal_two_sided_p(
            z
        )

        # index 0 = tirage récent
        gap = next(
            (
                i
                for i, present
                in enumerate(pres)
                if present
            ),
            total,
        )

        expected_failures = (
            (
                1
                - p_theoretical
            )
            / p_theoretical
            if p_theoretical > 0
            else total
        )

        raw[n] = {
            "freq": freq,
            "expected": expected,
            "archive_rate": archive_rate,
            "heat": archive_rate * 100,
            "recent_freq": recent_freq,
            "recent_rate": recent_rate,
            "vel": recent_rate * 100,
            "momentum": (
                recent_rate
                / p_theoretical
                if p_theoretical > 0
                else 1.0
            ),
            "freq_ratio": (
                freq
                / expected
                if expected > 0
                else 1.0
            ),
            "z": float(z),
            "p": float(p_value),
            "gap": int(gap),
            "gap_ratio": (
                float(
                    gap
                    / expected_failures
                )
                if expected_failures > 0
                else 0.0
            ),
        }

        pvals.append(
            p_value
        )

    qvals = fdr_bh(
        pvals
    )

    for idx, n in enumerate(
        range(
            1,
            max_val + 1,
        )
    ):
        q = float(
            qvals[idx]
        )

        z = raw[n]["z"]

        if (
            q < 0.05
            and z > 0
        ):
            status = "EXCÈS FDR 🔥"

        elif (
            q < 0.05
            and z < 0
        ):
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
                "Attendu": round(
                    s["expected"],
                    2,
                ),
                "Archive %": round(
                    s["heat"],
                    2,
                ),
                "Récent %": round(
                    s["vel"],
                    2,
                ),
                "Momentum": round(
                    s["momentum"],
                    2,
                ),
                "Écart": s["gap"],
                "Z": round(
                    s["z"],
                    2,
                ),
                "p": s["p"],
                "q FDR": s["q"],
                "État": s["status"],
            }
            for n, s
            in stats.items()
        ]
    )


def pair_analysis(
    df,
    jeu,
):
    bcols = [
        f"b{i}"
        for i in range(
            1,
            jeu["nb_b"] + 1,
        )
    ]

    n = jeu["b_max"]

    matrix = np.zeros(
        (n, n),
        dtype=float,
    )

    freq = np.zeros(
        n,
        dtype=float,
    )

    for row in df[
        bcols
    ].to_numpy(
        dtype=int
    ):
        values = sorted(
            set(
                int(x)
                for x in row
            )
        )

        for x in values:
            freq[
                x - 1
            ] += 1

        for a, b in combinations(
            values,
            2,
        ):
            matrix[
                a - 1,
                b - 1,
            ] += 1

            matrix[
                b - 1,
                a - 1,
            ] += 1

    total = len(df)
    k = jeu["nb_b"]

    correction = (
        (
            k - 1
        )
        / k
    ) * (
        n
        / (
            n - 1
        )
    )

    lift = np.ones_like(
        matrix
    )

    for i in range(n):
        for j in range(n):

            if i == j:
                lift[
                    i,
                    j,
                ] = 1.0
                continue

            expected = (
                total
                * (
                    freq[i]
                    / total
                )
                * (
                    freq[j]
                    / total
                )
                * correction
                if total
                else 0
            )

            lift[
                i,
                j,
            ] = (
                matrix[
                    i,
                    j,
                ]
                / expected
                if expected > 0
                else 0.0
            )

    theoretical_pair_expected = (
        total
        * (
            k
            * (
                k - 1
            )
            / (
                n
                * (
                    n - 1
                )
            )
        )
    )

    return (
        matrix,
        lift,
        theoretical_pair_expected,
    )
