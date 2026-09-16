# ============================================================
# SMART-LOTO V38/V39
# CORE CONFIGURATION
# ============================================================


APP_NAME = "SMART-LOTO V38/V39"


# ------------------------------------------------------------
# Jeux supportés
# ------------------------------------------------------------

JEUX = {

    "euromillions": {

        "nom": "Euromillions",

        "b_max": 50,
        "e_max": 12,

        "nb_b": 5,
        "nb_e": 2,

        "sum_range": (90, 165),

        "extra_label": "Étoiles"
    },


    "loto": {

        "nom": "Loto",

        "b_max": 49,
        "e_max": 10,

        "nb_b": 5,
        "nb_e": 1,

        "sum_range": (75, 175),

        "extra_label": "Chance"
    }
}



# ------------------------------------------------------------
# V38 Bayesian Engine
# ------------------------------------------------------------

WINDOWS = {

    "court_terme": 10,

    "moyen_terme": 50,

    "long_terme": 200,

    "historique": None

}



BAYES_CONFIG = {

    # force du lissage bayésien

    "alpha_prior": 1,

    "beta_prior": 1,

    # seuils interprétation

    "confidence_low": 0.55,

    "confidence_medium": 0.70,

    "confidence_high": 0.85
}



# ------------------------------------------------------------
# V39 Genetic Optimizer
# ------------------------------------------------------------

GENETIC_CONFIG = {

    "population_size": 500,

    "generations": 50,

    "elite_ratio": 0.10,

    "mutation_rate": 0.15
}



# ------------------------------------------------------------
# Score explicable
# ------------------------------------------------------------

SCORING_WEIGHTS = {

    "bayesian": 0.35,

    "momentum": 0.25,

    "historical": 0.20,

    "stability": 0.10,

    "diversity": 0.10
}
