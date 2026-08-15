from pydantic import BaseModel, Field

from models.significance_assessment import (
    SignificanceAssessment,
    SignificanceDecision,
)
from models.source_document import SourceDocument
from models.source_finding_candidate import SourceFindingCandidate


class _SignificanceResponse(BaseModel):
    decision: SignificanceDecision
    significance: int | None = Field(
        default=None,
        ge=1,
        le=10,
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    rationale: str


class OpenAISemanticSignificanceAssessor:
    def __init__(
        self,
        client,
        model: str,
        max_output_tokens: int = 500,
    ) -> None:
        if not model.strip():
            raise ValueError("model is required")

        if max_output_tokens < 16:
            raise ValueError(
                "max_output_tokens must be at least 16"
            )

        self._client = client
        self._model = model
        self._max_output_tokens = max_output_tokens

    def assess(
        self,
        candidate: SourceFindingCandidate,
        document: SourceDocument,
    ) -> SignificanceAssessment:
        evidence_text = "\n".join(
            evidence.text
            for evidence in candidate.evidence
        )

        response = self._client.responses.parse(
            model=self._model,
            input=(
                "Assess the investor significance of the "
                "grounded finding below.\n\n"
                "Use only the supplied source document and evidence.\n"
                "Do not invent facts, numbers, dates, causes, "
                "consequences, or company context not supported "
                "by the source.\n\n"
                "Return one decision:\n"
                "- assessed: there is enough evidence to assess "
                "investor significance.\n"
                "- unresolved: the evidence is insufficient to "
                "assess significance reliably.\n\n"
                "If decision is assessed, significance must be "
                "an integer from 1 to 10.\n"
                "If decision is unresolved, significance must be null.\n\n"
                "Confidence means confidence in the decision returned, "
                "not confidence that the finding is important.\n\n"
                f"SOURCE: {document.source}\n"
                f"TITLE: {document.title}\n"
                f"SOURCE URL: {document.source_url}\n\n"
                f"FINDING:\n{candidate.statement}\n\n"
                f"EVIDENCE:\n{evidence_text}\n\n"
                f"FULL SOURCE DOCUMENT:\n{document.text}"
            ),
            text_format=_SignificanceResponse,
            max_output_tokens=self._max_output_tokens,
        )

        parsed = self._find_parsed_output(response)

        return SignificanceAssessment(
            decision=SignificanceDecision(
                parsed.decision
            ),
            significance=parsed.significance,
            confidence=parsed.confidence,
            rationale=parsed.rationale,
        )

    @staticmethod
    def _find_parsed_output(
        response,
    ) -> _SignificanceResponse:
        for output_item in response.output:
            if getattr(output_item, "type", None) != "message":
                continue

            for content_item in getattr(
                output_item,
                "content",
                (),
            ):
                parsed = getattr(
                    content_item,
                    "parsed",
                    None,
                )

                if parsed is not None:
                    return parsed

        raise ValueError(
            "OpenAI response did not contain parsed "
            "significance assessment output"
        )
