import numpy as np

from analytics.scoring import (
    build_weights,
    sample_grid,
    strategy_score,
)


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
    rng = np.random.default_rng(
        int(seed)
    )

    nums_b, base_w_b = build_weights(
        stats_b,
        profile,
        strength=strength,
        allow_anti_share=True,
    )

    nums_e, base_w_e = build_weights(
        stats_e,
        profile,
        strength=strength,
        allow_anti_share=False,
    )

    if (
        len(nums_b) == 0
        or len(nums_e) == 0
    ):
        raise ValueError(
            "Statistiques insuffisantes "
            "pour générer un portefeuille."
        )

    results = []
    previous = []

    use_counts = {
        int(n): 0
        for n in nums_b
    }

    force_parity = (
        profile
        == "⚖️ Paritaire"
    )

    for _ in range(
        int(nb_grids)
    ):
        w_b = (
            base_w_b.copy()
        )

        if diversify:
            for i, n in enumerate(
                nums_b
            ):
                count = use_counts[
                    int(n)
                ]

                if count > 0:
                    w_b[i] *= (
                        0.18 ** count
                    )

        g = sample_grid(
            rng=rng,
            nums=nums_b,
            weights=w_b,
            k=jeu["nb_b"],
            sum_filter=sum_filter,
            parity_balanced=(
                parity_balanced
                or force_parity
            ),
            exclusions=exclusions,
            previous_grids=previous,
            max_overlap=(
                max_overlap
                if diversify
                else None
            ),
        )

        for n in g:
            use_counts[
                int(n)
            ] += 1

        previous.append(
            set(g)
        )

        e = sorted(
            rng.choice(
                nums_e,
                jeu["nb_e"],
                replace=False,
                p=(
                    base_w_e
                    / base_w_e.sum()
                ),
            ).astype(
                int
            ).tolist()
        )

        results.append(
            {
                "balls": g,
                "extras": e,
                "score": strategy_score(
                    g,
                    nums_b,
                    base_w_b,
                ),
                "extra_score": strategy_score(
                    e,
                    nums_e,
                    base_w_e,
                ),
            }
        )

    return results
