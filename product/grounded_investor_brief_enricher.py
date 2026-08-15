from dataclasses import replace
from typing import Protocol

from models.event import Event
from models.investor_brief import InvestorBrief
from models.source_document import SourceDocument
from models.source_grounded_brief import SourceGroundedBrief


class SourceDocumentProvider(Protocol):
    def build(
        self,
        event: Event,
    ) -> SourceDocument | None:
        ...


class GroundedBriefService(Protocol):
    def build(
        self,
        document: SourceDocument,
    ) -> SourceGroundedBrief | None:
        ...


class GroundedBriefSummaryBuilder(Protocol):
    def build(
        self,
        brief: SourceGroundedBrief,
    ) -> str:
        ...


class GroundedInvestorBriefEnricher:
    def __init__(
        self,
        document_provider: SourceDocumentProvider,
        grounded_brief_service: GroundedBriefService,
        summary_builder: GroundedBriefSummaryBuilder,
    ) -> None:
        self._document_provider = document_provider
        self._grounded_brief_service = grounded_brief_service
        self._summary_builder = summary_builder

    def enrich(
        self,
        brief: InvestorBrief,
    ) -> InvestorBrief:
        document = self._document_provider.build(
            brief.event
        )

        if document is None:
            return brief

        grounded_brief = self._grounded_brief_service.build(
            document
        )

        if grounded_brief is None:
            return brief

        summary = self._summary_builder.build(
            grounded_brief
        )

        if not summary.strip():
            return brief

        return replace(
            brief,
            summary=summary,
        )
