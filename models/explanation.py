from dataclasses import dataclass


@dataclass(frozen=True)
class Explanation:
    why_it_matters: str
    market_context: str
