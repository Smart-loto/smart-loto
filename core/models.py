# ============================================================
# SMART-LOTO V38/V39
# CORE DATA MODELS
# ============================================================


from dataclasses import dataclass, field
from typing import List, Dict



# ============================================================
# Evidence d'un numéro
# ============================================================

@dataclass
class NumberEvidence:


    number: int


    observed_frequency: int = 0

    expected_frequency: float = 0.0



    bayesian_score: float = 0.0

    posterior_probability: float = 0.0



    windows: Dict = field(
        default_factory=dict
    )



    explainability: Dict = field(
        default_factory=dict
    )



    confidence: str = "unknown"



# ============================================================
# Grille individuelle
# ============================================================

@dataclass
class Ticket:



    numbers: List[int]

    extras: List[int] = field(
        default_factory=list
    )



    score: float = 0.0



    metrics: Dict = field(
        default_factory=dict
    )



# ============================================================
# Individu génétique
# ============================================================

@dataclass
class Individual:



    ticket: Ticket



    fitness: float = 0.0



    generation: int = 0



    history: List = field(
        default_factory=list
    )



# ============================================================
# Portefeuille
# ============================================================

@dataclass
class Portfolio:



    tickets: List[Ticket]



    global_score: float = 0.0



    coverage_score: float = 0.0



    overlap_score: float = 0.0



    diversity_score: float = 0.0
