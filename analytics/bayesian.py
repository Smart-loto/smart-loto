# ============================================================
# SMART-LOTO V38
# BAYESIAN ENGINE
# ============================================================

"""
Moteur bayésien simplifié.

Objectif :
- lisser les fréquences
- éviter les réactions excessives aux petits échantillons
- produire une mesure d'évidence explicable

Ce module ne prédit pas les tirages.
Il mesure uniquement l'adéquation des observations
avec différentes hypothèses statistiques.
"""


from math import comb

from core.models import NumberEvidence

from core.config import BAYES_CONFIG



# ============================================================
# Fréquence théorique
# ============================================================

def expected_frequency(
        draws_count,
        picks_per_draw,
        total_numbers
):

    probability = picks_per_draw / total_numbers

    return draws_count * probability



# ============================================================
# Score bayésien Beta-Binomial
# ============================================================


def bayesian_probability(
        observed,
        total_draws,
        picks_per_draw,
        total_numbers
):


    alpha = BAYES_CONFIG["alpha_prior"]

    beta = BAYES_CONFIG["beta_prior"]



    expected_probability = (
        picks_per_draw / total_numbers
    )



    prior_success = (
        alpha
        +
        expected_probability * 10
    )


    prior_failure = (
        beta
        +
        (1 - expected_probability) * 10
    )



    posterior = (

        prior_success + observed

    ) / (

        prior_success
        +
        prior_failure
        +
        total_draws

    )



    return float(posterior)



# ============================================================
# Niveau de confiance
# ============================================================


def confidence_level(score):


    if score >= BAYES_CONFIG["confidence_high"]:

        return "high"



    if score >= BAYES_CONFIG["confidence_medium"]:

        return "medium"



    return "low"



# ============================================================
# Analyse d'un numéro
# ============================================================


def analyse_number(
        number,
        observed,
        total_draws,
        picks_per_draw,
        total_numbers,
        windows=None
):


    expected = expected_frequency(
        total_draws,
        picks_per_draw,
        total_numbers
    )



    posterior = bayesian_probability(
        observed,
        total_draws,
        picks_per_draw,
        total_numbers
    )



    evidence = NumberEvidence(

        number=number,

        observed_frequency=observed,

        expected_frequency=expected,

        bayesian_score=posterior * 100,

        posterior_probability=posterior,

        windows=windows or {},

        confidence=confidence_level(
            posterior
        )

    )



    evidence.explainability = {

        "observed": observed,

        "expected": round(expected,2),

        "difference":
            round(
                observed - expected,
                2
            ),

        "confidence":
            evidence.confidence
    }



    return evidence



# ============================================================
# Analyse complète d'une archive
# ============================================================


def analyse_archive(
        frequency_table,
        draws_count,
        picks_per_draw,
        total_numbers,
        windows=None
):


    results = {}



    for number, freq in frequency_table.items():


        results[number] = analyse_number(

            number,

            freq,

            draws_count,

            picks_per_draw,

            total_numbers,

            windows.get(number,{})
            if windows else {}

        )



    return results
