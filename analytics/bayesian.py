import numpy as np
import pandas as pd


def beta_binomial_summary(
    df,
    max_val,
    picks_per_draw,
    prefix="b",
    prior_strength=20.0,
):
    """
    Résumé bayésien Beta-Binomial
    de la fréquence marginale
    de chaque numéro.

    Le prior est centré sur la
    probabilité théorique :

        picks_per_draw / max_val

    L'intervalle 95 % est une
    approximation normale du
    posterior Beta afin de rester
    sans dépendance SciPy.
    """

    cols = [
        c
        for c in df.columns
        if c.startswith(prefix)
    ]

    if (
        not cols
        or len(df) == 0
    ):
        return pd.DataFrame()

    matrix = df[
        cols
    ].to_numpy(
        dtype=int
    )

    total = len(df)

    p0 = (
        picks_per_draw
        / max_val
    )

    prior_strength = max(
        float(prior_strength),
        1e-6,
    )

    alpha0 = (
        p0
        * prior_strength
    )

    beta0 = (
        (1.0 - p0)
        * prior_strength
    )

    rows = []

    for n in range(
        1,
        max_val + 1,
    ):
        present = np.any(
            matrix == n,
            axis=1,
        )

        successes = int(
            present.sum()
        )

        failures = (
            total
            - successes
        )

        alpha = (
            alpha0
            + successes
        )

        beta = (
            beta0
            + failures
        )

        mean = (
            alpha
            / (
                alpha
                + beta
            )
        )

        var = (
            alpha
            * beta
        ) / (
            (
                alpha
                + beta
            ) ** 2
            * (
                alpha
                + beta
                + 1
            )
        )

        sd = float(
            np.sqrt(var)
        )

        low = max(
            0.0,
            mean
            - 1.96 * sd,
        )

        high = min(
            1.0,
            mean
            + 1.96 * sd,
        )

        rows.append(
            {
                "N°": n,
                "Observations": successes,
                "Posterior %": (
                    mean * 100
                ),
                "IC95 bas %": (
                    low * 100
                ),
                "IC95 haut %": (
                    high * 100
                ),
                "Théorie %": (
                    p0 * 100
                ),
                "Ratio posterior/théorie": (
                    mean / p0
                    if p0 > 0
                    else 1.0
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


def bayesian_rank(
    summary: pd.DataFrame,
) -> pd.DataFrame:

    if summary.empty:
        return summary.copy()

    out = summary.copy()

    out[
        "Rang posterior"
    ] = out[
        "Posterior %"
    ].rank(
        ascending=False,
        method="average",
    )

    return out.sort_values(
        [
            "Posterior %",
            "N°",
        ],
        ascending=[
            False,
            True,
        ],
    ).reset_index(
        drop=True
    )
