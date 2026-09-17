import math

import numpy as np
import pandas as pd

from analytics.scoring import (
    build_weights,
    sample_grid,
)

from analytics.statistics import (
    get_full_stats,
)

from core.config import JEUX


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

    min_train = max(
        40,
        int(recent_window) + 10,
    )

    max_eval = min(
        int(depth),
        max(
            0,
            len(df)
            - min_train,
        ),
    )

    if max_eval <= 0:
        return pd.DataFrame()

    bcols = [
        f"b{i}"
        for i in range(
            1,
            jeu["nb_b"] + 1,
        )
    ]

    ecols = [
        f"e{i}"
        for i in range(
            1,
            jeu["nb_e"] + 1,
        )
    ]

    rows = []

    for idx in range(
        max_eval
    ):
        target = df.iloc[
            idx
        ]

        # Seulement les tirages
        # plus anciens.
        train = df.iloc[
            idx + 1 :
        ].reset_index(
            drop=True
        )

        stats_b = get_full_stats(
            train,
            jeu["b_max"],
            jeu["nb_b"],
            "b",
            recent_window,
        )

        stats_e = get_full_stats(
            train,
            jeu["e_max"],
            jeu["nb_e"],
            "e",
            recent_window,
        )

        nums_b, w_b = build_weights(
            stats_b,
            profile,
            strength=strength,
            allow_anti_share=True,
        )

        nums_e, w_e = build_weights(
            stats_e,
            profile,
            strength=strength,
            allow_anti_share=False,
        )

        rng_s = np.random.default_rng(
            int(seed)
            + idx * 1009
        )

        rng_r = np.random.default_rng(
            int(seed)
            + 99991
            + idx * 1013
        )

        target_b = set(
            int(
                target[c]
            )
            for c in bcols
        )

        target_e = set(
            int(
                target[c]
            )
            for c in ecols
        )

        sum_filter = (
            jeu["sum_range"]
            if use_sum_filter
            else None
        )

        parity = bool(
            use_parity
            or profile
            == "⚖️ Paritaire"
        )

        strat_hits = []
        rand_hits = []

        for _ in range(
            int(tickets_per_draw)
        ):
            g_s = sample_grid(
                rng=rng_s,
                nums=nums_b,
                weights=w_b,
                k=jeu["nb_b"],
                sum_filter=sum_filter,
                parity_balanced=parity,
            )

            e_s = sorted(
                rng_s.choice(
                    nums_e,
                    jeu["nb_e"],
                    replace=False,
                    p=(
                        w_e
                        / w_e.sum()
                    ),
                ).astype(
                    int
                ).tolist()
            )

            strat_hits.append(
                (
                    len(
                        set(g_s)
                        .intersection(
                            target_b
                        )
                    ),
                    len(
                        set(e_s)
                        .intersection(
                            target_e
                        )
                    ),
                )
            )

            # Baseline aléatoire :
            # mêmes contraintes,
            # poids uniformes.
            g_r = sample_grid(
                rng=rng_r,
                nums=nums_b,
                weights=np.ones_like(
                    w_b
                ),
                k=jeu["nb_b"],
                sum_filter=sum_filter,
                parity_balanced=parity,
            )

            e_r = sorted(
                rng_r.choice(
                    nums_e,
                    jeu["nb_e"],
                    replace=False,
                ).astype(
                    int
                ).tolist()
            )

            rand_hits.append(
                (
                    len(
                        set(g_r)
                        .intersection(
                            target_b
                        )
                    ),
                    len(
                        set(e_r)
                        .intersection(
                            target_e
                        )
                    ),
                )
            )

        best_s = max(
            strat_hits,
            key=lambda x: (
                x[0],
                x[1],
            ),
        )

        best_r = max(
            rand_hits,
            key=lambda x: (
                x[0],
                x[1],
            ),
        )

        rows.append(
            {
                "index_test": idx,
                "strat_b": best_s[0],
                "strat_e": best_s[1],
                "random_b": best_r[0],
                "random_e": best_r[1],
                "strat_total": (
                    best_s[0]
                    + best_s[1]
                ),
                "random_total": (
                    best_r[0]
                    + best_r[1]
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


def summarize_backtest(
    bt: pd.DataFrame,
) -> dict:
    if (
        bt is None
        or bt.empty
    ):
        return {}

    avg_s = float(
        bt["strat_b"].mean()
    )

    avg_r = float(
        bt["random_b"].mean()
    )

    delta = (
        avg_s
        - avg_r
    )

    paired = (
        bt["strat_b"]
        - bt["random_b"]
    ).astype(float)

    if len(paired) > 1:
        se_delta = float(
            paired.std(
                ddof=1
            )
            / math.sqrt(
                len(paired)
            )
        )

        ci_low = (
            delta
            - 1.96 * se_delta
        )

        ci_high = (
            delta
            + 1.96 * se_delta
        )

    else:
        ci_low = delta
        ci_high = delta

    return {
        "avg_strategy": avg_s,
        "avg_random": avg_r,
        "delta": delta,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "rate3_strategy": float(
            (
                bt["strat_b"] >= 3
            ).mean()
            * 100
        ),
        "rate3_random": float(
            (
                bt["random_b"] >= 3
            ).mean()
            * 100
        ),
        "extra_strategy": float(
            bt["strat_e"].mean()
        ),
        "extra_random": float(
            bt["random_e"].mean()
        ),
    }
