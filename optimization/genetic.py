import numpy as np

from analytics.scoring import sample_grid
from optimization.fitness import structural_fitness


def _valid_grid(
    grid,
    k,
    sum_filter=None,
    parity_balanced=False,
):
    if (
        len(grid) != k
        or len(set(grid)) != k
    ):
        return False

    if (
        sum_filter
        and not (
            sum_filter[0]
            <= sum(grid)
            <= sum_filter[1]
        )
    ):
        return False

    if parity_balanced:
        evens = sum(
            1
            for n in grid
            if n % 2 == 0
        )

        if evens not in (
            2,
            3,
        ):
            return False

    return True


def evolve_grid(
    jeu,
    nums,
    weights,
    seed=39039,
    generations=60,
    population_size=80,
    elite_size=12,
    mutation_rate=0.25,
    sum_filter=None,
    parity_balanced=True,
    exclusions=None,
):
    """
    Optimiseur génétique exploratoire.

    Il optimise uniquement le score
    structurel défini dans fitness.py.

    Il ne modifie pas la probabilité
    théorique du tirage.
    """

    rng = np.random.default_rng(
        int(seed)
    )

    k = int(
        jeu["nb_b"]
    )

    exclusions = set(
        exclusions or []
    )

    allowed_mask = np.array(
        [
            int(n)
            not in exclusions
            for n in nums
        ],
        dtype=bool,
    )

    allowed_nums = np.asarray(
        nums
    )[allowed_mask]

    allowed_weights = np.asarray(
        weights,
        dtype=float,
    )[allowed_mask]

    if len(allowed_nums) < k:
        raise ValueError(
            "Pas assez de numéros "
            "disponibles après exclusions."
        )

    allowed_weights = np.clip(
        allowed_weights,
        1e-9,
        None,
    )

    allowed_weights = (
        allowed_weights
        / allowed_weights.sum()
    )

    population_size = max(
        int(population_size),
        10,
    )

    elite_size = max(
        2,
        min(
            int(elite_size),
            population_size // 2,
        ),
    )

    population = []

    for _ in range(
        population_size
    ):
        population.append(
            sample_grid(
                rng=rng,
                nums=allowed_nums,
                weights=allowed_weights,
                k=k,
                sum_filter=sum_filter,
                parity_balanced=parity_balanced,
                attempts=5000,
            )
        )

    def fitness(grid):
        return structural_fitness(
            grid,
            jeu,
            nums,
            weights,
        )

    for _ in range(
        max(
            1,
            int(generations),
        )
    ):
        ranked = sorted(
            (
                (
                    fitness(grid),
                    grid,
                )
                for grid
                in population
            ),
            key=lambda x: x[0],
            reverse=True,
        )

        elites = [
            list(grid)
            for _, grid
            in ranked[
                :elite_size
            ]
        ]

        next_population = (
            elites.copy()
        )

        while (
            len(next_population)
            < population_size
        ):
            p1 = elites[
                int(
                    rng.integers(
                        0,
                        len(elites),
                    )
                )
            ]

            p2 = elites[
                int(
                    rng.integers(
                        0,
                        len(elites),
                    )
                )
            ]

            pool = sorted(
                set(p1)
                | set(p2)
            )

            if len(pool) < k:
                pool = sorted(
                    set(pool)
                    | set(
                        allowed_nums.tolist()
                    )
                )

            pool_arr = np.array(
                pool,
                dtype=int,
            )

            weight_lookup = {
                int(n): float(w)
                for n, w
                in zip(
                    nums,
                    weights,
                )
            }

            pool_w = np.array(
                [
                    weight_lookup.get(
                        int(n),
                        1.0,
                    )
                    for n in pool_arr
                ]
            )

            pool_w = np.clip(
                pool_w,
                1e-9,
                None,
            )

            pool_w = (
                pool_w
                / pool_w.sum()
            )

            child = sorted(
                rng.choice(
                    pool_arr,
                    k,
                    replace=False,
                    p=pool_w,
                ).astype(
                    int
                ).tolist()
            )

            if (
                rng.random()
                < float(
                    mutation_rate
                )
            ):
                replace_idx = int(
                    rng.integers(
                        0,
                        k,
                    )
                )

                available = [
                    int(n)
                    for n
                    in allowed_nums
                    if int(n)
                    not in child
                ]

                if available:
                    child[
                        replace_idx
                    ] = int(
                        rng.choice(
                            available
                        )
                    )

                    child = sorted(
                        set(child)
                    )

            if _valid_grid(
                child,
                k=k,
                sum_filter=sum_filter,
                parity_balanced=parity_balanced,
            ):
                next_population.append(
                    child
                )

            else:
                next_population.append(
                    sample_grid(
                        rng=rng,
                        nums=allowed_nums,
                        weights=allowed_weights,
                        k=k,
                        sum_filter=sum_filter,
                        parity_balanced=parity_balanced,
                        attempts=5000,
                    )
                )

        population = (
            next_population
        )

    best = max(
        population,
        key=fitness,
    )

    return {
        "balls": sorted(
            int(n)
            for n in best
        ),
        "fitness": float(
            fitness(best)
        ),
    }
