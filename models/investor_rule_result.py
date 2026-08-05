from dataclasses import dataclass

from models.explanation import Explanation


@dataclass(frozen=True, slots=True)
class InvestorRuleResult:
    summary: str
    explanation: Explanation
