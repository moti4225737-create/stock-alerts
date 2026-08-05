from collections.abc import Iterable
from typing import Protocol

from models.event import Event


class InvestorSummaryRule(Protocol):
    rule_id: str
    priority: int

    def matches(self, event: Event) -> bool:
        ...

    def build_summary(self, event: Event) -> str:
        ...


class InvestorSummaryRuleSet:
    def __init__(
        self,
        rules: Iterable[InvestorSummaryRule],
    ) -> None:
        self._rules = tuple(
            sorted(
                rules,
                key=lambda rule: rule.priority,
                reverse=True,
            )
        )

    def build(self, event: Event) -> str:
        for rule in self._rules:
            if rule.matches(event):
                return rule.build_summary(event)

        return event.summary