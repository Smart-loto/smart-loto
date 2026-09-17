from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ImportInfo:
    rows_raw: int
    rows_clean: int
    dropped: int


@dataclass
class PortfolioTicket:
    balls: List[int]
    extras: List[int]
    score: float
    extra_score: float
    metadata: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "balls": self.balls,
            "extras": self.extras,
            "score": self.score,
            "extra_score": self.extra_score,
            "metadata": self.metadata,
        }
