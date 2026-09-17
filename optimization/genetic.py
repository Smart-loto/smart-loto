import numpy as np

from analytics.scoring import strategy_score
from analytics.statistics import (
    calc_entropy,
    get_geometry_score,
)


def grid_overlap(
    a,
    b,
) -> int:
    return len(
        set(a).intersection(b)
    )


def portfolio_diversity(
    grids,
) -> float:
    grids = [
        list(g)
        for g in grids
    ]

    if len(grids) < 2:
        return 1.0

    k = max(
        1,
        len(grids[0]),
    )

    overlaps = []

    for i in range(
        len(grids)
    ):
        for j in range(
            i + 1,
            len(grids),
        ):
            overlaps.append(
                grid_overlap(
                    grids[i],
                    grids[j],
                )
                / k
            )

    return (
        float(
            1.0
            - np.mean(overlaps)
        )
        if overlaps
        else 1.0
    )


def parity_score(
    grid,
) -> float:
    if not grid:
        return 0.0

    evens = sum(
        1
        for n in grid
        if int(n) % 2 == 0
    )

    if evens in (
        2,
        3,
    ):
        return 1.0

    return max(
        0.0,
        1.0
        - abs(
            evens - 2.5
        )
        / 2.5,
    )


def sum_balance_score(
    grid,
    target_range,
) -> float:
    if not grid:
        return 0.0

    low, high = (
        target_range
    )

    center = (
        low + high
    ) / 2

    half_width = max(
        (
            high - low
        ) / 2,
        1.0,
    )

    distance = abs(
        sum(grid)
        - center
    )

    return float(
        max(
            0.0,
            1.0
            - distance
            / (
                2.0
                * half_width
            ),
        )
    )


def structural_fitness(
    grid,
    jeu,
    nums,
    weights,
) -> float:
    """
    Score heuristique 0-100.

    Il combine :
    - alignement avec le profil
    - entropie
    - géométrie
    - parité
    - somme

    Ce score n'est pas une
    probabilité de gain.
    """

    if not grid:
        return 0.0

    strategy = (
        strategy_score(
            grid,
            nums,
            weights,
        )
        / 100.0
    )

    entropy = np.clip(
        calc_entropy(
            grid,
            jeu["b_max"],
        )
        / 3.0,
        0.0,
        1.0,
    )

    geometry = np.clip(
        get_geometry_score(
            grid
        )
        / 10.0,
        0.0,
        1.0,
    )

    parity = parity_score(
        grid
    )

    sum_score = sum_balance_score(
        grid,
        jeu["sum_range"],
    )

    score = (
        0.55 * strategy
        + 0.15 * entropy
        + 0.10 * geometry
        + 0.10 * parity
        + 0.10 * sum_score
    )

    return float(
        np.clip(
            score * 100.0,
            0.0,
            100.0,
        )
    )
