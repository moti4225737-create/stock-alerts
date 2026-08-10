import re

from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationDecision,
    StoryCorrelationResult,
)


class StoryCorrelator:
    _ACQUISITION_TERMS = {
        "acquisition",
        "acquire",
        "acquired",
        "purchasing",
        "purchase",
        "purchased",
        "buy",
        "bought",
        "closing",
        "closed",
    }

    _COMMERCIAL_CONTRACT_TERMS = {
        "customer",
        "contract",
        "services",
        "utility",
        "order",
        "award",
        "deployment",
    }

    _REGULATORY_TERMS = {
        "fda",
        "approval",
        "approves",
        "approved",
        "application",
        "accepted",
        "review",
        "regulatory",
    }

    _LITIGATION_TERMS = {
        "litigation",
        "patent",
        "lawsuit",
        "court",
        "injunction",
        "legal",
    }

    _EARNINGS_TERMS = {
        "earnings",
        "revenue",
        "quarter",
        "quarterly",
        "results",
        "operating",
    }

    _NON_SUBJECT_TERMS = {
        "ondas",
        "liquidia",
        "holdings",
        "technologies",
        "company",
        "corporation",
        "corp",
        "inc",
        "limited",
        "ltd",
        "form",
        "sec",
        "fda",
        "strategic",
        "transaction",
        "acquisition",
        "acquire",
        "acquired",
        "purchase",
        "purchased",
        "closing",
        "closed",
        "completed",
        "completes",
        "completion",
        "announced",
        "announcement",
        "agreement",
        "agreed",
        "update",
        "reported",
        "reports",
        "provided",
        "previously",
        "inspection",
        "business",
        "drone",
        "uk",
        "based",
        "application",
        "review",
        "approval",
        "approves",
        "approved",
        "treatment",
        "pulmonary",
        "hypertension",
        "revenue",
        "operating",
        "results",
        "quarter",
        "quarterly",
        "first",
        "second",
        "third",
        "fourth",
        "customer",
        "contract",
        "services",
        "utility",
        "order",
        "award",
        "deployment",
        "patent",
        "litigation",
        "developments",
        "involving",
    }

    def correlate(
        self,
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        if self._symbol(earlier_event) != self._symbol(current_event):
            return StoryCorrelationResult(
                decision=StoryCorrelationDecision.NO_MATCH,
                confidence=1.0,
                reason="Events belong to different symbols.",
            )

        earlier_domain = self._story_domain(
            earlier_event
        )
        current_domain = self._story_domain(
            current_event
        )

        if (
            earlier_domain is not None
            and current_domain is not None
            and earlier_domain != current_domain
        ):
            return StoryCorrelationResult(
                decision=StoryCorrelationDecision.NO_MATCH,
                confidence=1.0,
                reason=(
                    "Events belong to different "
                    "story domains."
                ),
            )

        earlier_period = self._reporting_period(
            earlier_event
        )
        current_period = self._reporting_period(
            current_event
        )

        if (
            earlier_domain == "earnings"
            and current_domain == "earnings"
            and earlier_period is not None
            and current_period is not None
            and earlier_period != current_period
        ):
            return StoryCorrelationResult(
                decision=StoryCorrelationDecision.NO_MATCH,
                confidence=1.0,
                reason=(
                    "Events refer to different "
                    "reporting periods."
                ),
            )

        earlier_subjects = self._explicit_subjects(
            earlier_event
        )
        current_subjects = self._explicit_subjects(
            current_event
        )

        shared_subjects = (
            earlier_subjects
            & current_subjects
        )

        if shared_subjects:
            return StoryCorrelationResult(
                decision=StoryCorrelationDecision.MATCH,
                confidence=1.0,
                reason=(
                    "Events share an explicit subject "
                    "within a compatible story domain: "
                    + ", ".join(
                        sorted(shared_subjects)
                    )
                ),
            )

        if (
            earlier_subjects
            and current_subjects
            and not shared_subjects
        ):
            return StoryCorrelationResult(
                decision=StoryCorrelationDecision.NO_MATCH,
                confidence=1.0,
                reason=(
                    "Events identify different explicit "
                    "story subjects."
                ),
            )

        return StoryCorrelationResult(
            decision=StoryCorrelationDecision.UNRESOLVED,
            confidence=0.5,
            reason=(
                "Story domain is compatible, but explicit "
                "subject identity is insufficient for a "
                "deterministic decision."
            ),
        )

    @staticmethod
    def _symbol(
        event: Event,
    ) -> str:
        return event.symbol.strip().upper()

    def _story_domain(
        self,
        event: Event,
    ) -> str | None:
        terms = self._lower_terms(event)

        if terms & self._LITIGATION_TERMS:
            return "litigation"

        if terms & self._COMMERCIAL_CONTRACT_TERMS:
            return "commercial_contract"

        if terms & self._ACQUISITION_TERMS:
            return "acquisition"

        if terms & self._REGULATORY_TERMS:
            return "regulatory"

        if terms & self._EARNINGS_TERMS:
            return "earnings"

        return None

    def _explicit_subjects(
        self,
        event: Event,
    ) -> set[str]:
        text = " ".join(
            (
                event.title or "",
                event.summary or "",
            )
        )

        tokens = re.findall(
            r"\b[A-Za-z][A-Za-z0-9-]*\b",
            text,
        )

        subjects: set[str] = set()

        for token in tokens:
            normalized = token.lower()

            if normalized in self._NON_SUBJECT_TERMS:
                continue

            if len(normalized) < 4:
                continue

            is_named_token = (
                token.isupper()
                or (
                    token[0].isupper()
                    and token.lower()
                    not in {
                        "the",
                        "this",
                        "both",
                    }
                )
            )

            if is_named_token:
                subjects.add(normalized)

        return subjects

    def _reporting_period(
        self,
        event: Event,
    ) -> str | None:
        text = " ".join(
            (
                event.title or "",
                event.summary or "",
            )
        ).lower()

        patterns = (
            (r"\bq1\b|\bfirst-quarter\b", "q1"),
            (r"\bq2\b|\bsecond-quarter\b", "q2"),
            (r"\bq3\b|\bthird-quarter\b", "q3"),
            (r"\bq4\b|\bfourth-quarter\b", "q4"),
        )

        for pattern, period in patterns:
            if re.search(pattern, text):
                return period

        return None

    @staticmethod
    def _lower_terms(
        event: Event,
    ) -> set[str]:
        text = " ".join(
            (
                event.title or "",
                event.summary or "",
            )
        ).lower()

        return set(
            re.findall(
                r"[a-z0-9][a-z0-9-]*",
                text,
            )
        )
