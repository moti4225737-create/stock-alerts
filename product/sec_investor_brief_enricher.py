from dataclasses import replace
from typing import Protocol

from models.investor_brief import InvestorBrief


class FilingExtractor(Protocol):
    def extract(
        self,
        url: str | None,
    ) -> str:
        ...


class SignalExtractor(Protocol):
    def extract(
        self,
        text: str,
    ) -> dict[str, str]:
        ...


class SummaryBuilder(Protocol):
    def build(
        self,
        signals: dict[str, str],
    ) -> str:
        ...


class SECInvestorBriefEnricher:
    def __init__(
        self,
        filing_extractor: FilingExtractor,
        signal_extractor: SignalExtractor,
        summary_builder: SummaryBuilder,
    ) -> None:
        self._filing_extractor = filing_extractor
        self._signal_extractor = signal_extractor
        self._summary_builder = summary_builder

    def enrich(
        self,
        brief: InvestorBrief,
    ) -> InvestorBrief:
        event = brief.event

        if event.source.upper() != "SEC":
            return brief

        if not event.url:
            return brief

        try:
            filing_text = self._filing_extractor.extract(
                event.url
            )

            if not filing_text:
                return brief

            signals = self._signal_extractor.extract(
                filing_text
            )

            if not signals:
                return brief

            summary = self._summary_builder.build(
                signals
            )

            if not summary:
                return brief

            return replace(
                brief,
                summary=summary,
            )
        except Exception:
            return brief
