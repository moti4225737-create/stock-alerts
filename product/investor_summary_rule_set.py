from collections.abc import Iterable
from typing import Protocol

from models.event import Event
from models.investor_rule_result import InvestorRuleResult


class InvestorSummaryRule(Protocol):
    rule_id: str
    priority: int

    def matches(self, event: Event) -> bool:
        ...

    def build_summary(self, event: Event) -> str:
        ...


class InvestorInterpretationRule(Protocol):
    rule_id: str
    priority: int

    def matches(self, event: Event) -> bool:
        ...

    def build_result(self, event: Event) -> InvestorRuleResult:
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

    def interpret(self, event: Event) -> InvestorRuleResult:
        for rule in self._rules:
            if not rule.matches(event):
                continue

            build_result = getattr(rule, "build_result", None)
            if callable(build_result):
                return build_result(event)

            raise LookupError(
                f"Rule {rule.rule_id} has no structured interpretation"
            )

        raise LookupError("No matching interpretation rule")
