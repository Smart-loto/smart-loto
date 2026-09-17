import numpy as np

from analytics.statistics import rank01


def build_weights(
    stats,
    profile,
    strength=0.75,
    anti_share_threshold=31,
    allow_anti_share=True,
):
    nums = np.array(
        sorted(
            stats.keys()
        ),
        dtype=int,
    )

    if len(nums) == 0:
        return (
            nums,
            np.array(
                [],
                dtype=float,
            ),
        )

    momentum = np.array(
        [
            stats[n]["momentum"]
            for n in nums
        ],
        dtype=float,
    )

    freq_ratio = np.array(
        [
            stats[n]["freq_ratio"]
            for n in nums
        ],
        dtype=float,
    )

    gap_ratio = np.array(
        [
            stats[n]["gap_ratio"]
            for n in nums
        ],
        dtype=float,
    )

    z = np.array(
        [
            stats[n]["z"]
            for n in nums
        ],
        dtype=float,
    )

    r_m = rank01(
        momentum
    )

    r_f = rank01(
        freq_ratio
    )

    r_g = rank01(
        gap_ratio
    )

    r_stability = rank01(
        -np.abs(
            freq_ratio - 1.0
        )
    )

    r_zpos = rank01(
        np.maximum(
            z,
            0,
        )
    )

    if profile == "🧠 Ensemble adaptatif":
        score = (
            0.35 * r_m
            + 0.20 * r_f
            + 0.20 * r_g
            + 0.15 * r_stability
            + 0.10 * r_zpos
        )

    elif profile == "🚫 Anti-partage":

        if allow_anti_share:
            high = (
                nums
                > anti_share_threshold
            ).astype(float)

            score = (
                0.20 * r_stability
                + 0.15 * r_m
                + 0.65 * high
            )

        else:
            score = (
                0.60 * r_stability
                + 0.40 * r_m
            )

    elif profile == "🎯 Équilibré":
        score = (
            0.70 * r_stability
            + 0.15 * r_m
            + 0.15 * r_g
        )

    elif profile == "🔥 Momentum":
        score = (
            0.75 * r_m
            + 0.15 * r_f
            + 0.10 * r_zpos
        )

    elif profile == "🧊 Retard":
        score = (
            0.80 * r_g
            + 0.10 * r_stability
            + 0.10 * r_f
        )

    elif profile == "⚖️ Paritaire":
        score = (
            0.75 * r_stability
            + 0.25 * r_m
        )

    else:
        score = np.full(
            len(nums),
            0.5,
        )

    centered = (
        score
        - np.mean(score)
    )

    heuristic = np.exp(
        np.clip(
            centered * 2.2,
            -2.0,
            2.0,
        )
    )

    heuristic = (
        heuristic
        / np.mean(heuristic)
    )

    strength = float(
        np.clip(
            strength,
            0.0,
            1.0,
        )
    )

    weights = (
        (
            1.0
            - strength
        )
        * np.ones_like(
            heuristic
        )
        + strength
        * heuristic
    )

    weights = np.clip(
        weights,
        1e-6,
        None,
    )

    return (
        nums,
        weights,
    )


def strategy_score(
    grid,
    nums,
    weights,
):
    if (
        len(grid) == 0
        or len(nums) == 0
    ):
        return 0.0

    rank_map = {
        int(n): float(r)
        for n, r
        in zip(
            nums,
            rank01(weights),
        )
    }

    return float(
        np.mean(
            [
                rank_map.get(
                    int(n),
                    0.5,
                )
                for n in grid
            ]
        )
        * 100
    )


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
    exclusions = set(
        exclusions or []
    )

    previous_grids = (
        previous_grids
        or []
    )

    w = np.array(
        weights,
        dtype=float,
    ).copy()

    for ex in exclusions:
        idx = np.where(
            nums == ex
        )[0]

        if len(idx):
            w[
                idx[0]
            ] = 0.0

    if (
        np.count_nonzero(
            w > 0
        )
        < k
    ):
        raise ValueError(
            "Trop de numéros exclus "
            "pour générer une grille valide."
        )

    p = (
        w
        / np.sum(w)
    )

    for _ in range(
        int(attempts)
    ):
        g = sorted(
            rng.choice(
                nums,
                k,
                replace=False,
                p=p,
            ).astype(
                int
            ).tolist()
        )

        if (
            sum_filter
            and not (
                sum_filter[0]
                <= sum(g)
                <= sum_filter[1]
            )
        ):
            continue

        if parity_balanced:
            evens = sum(
                1
                for n in g
                if n % 2 == 0
            )

            if evens not in (
                2,
                3,
            ):
                continue

        if (
            max_overlap is not None
            and previous_grids
        ):
            if any(
                len(
                    set(g).intersection(
                        prev
                    )
                )
                > max_overlap
                for prev
                in previous_grids
            ):
                continue

        return g

    raise ValueError(
        "Aucune grille ne satisfait "
        "les contraintes. "
        "Élargissez les filtres."
    )
