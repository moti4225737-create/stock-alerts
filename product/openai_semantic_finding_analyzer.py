from typing import Any

from pydantic import BaseModel

from models.analyzer_execution_result import AnalyzerExecutionResult
from models.semantic_finding_proposal import SemanticFindingProposal
from models.source_document import SourceDocument


class _Finding(BaseModel):
    statement: str
    evidence_text: str
    locator: str | None = None


class _FindingResponse(BaseModel):
    findings: list[_Finding]


class OpenAISemanticFindingAnalyzer:
    def __init__(
        self,
        client: Any,
        model: str,
        max_output_tokens: int = 2000,
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

    def analyze(
        self,
        document: SourceDocument,
    ) -> AnalyzerExecutionResult:
        response = self._client.responses.parse(
            model=self._model,
            input=(
                "Analyze the following primary-source document. "
                "Identify only material investor-relevant findings. "
                "For every finding, provide a concise factual statement, "
                "exact supporting evidence from the source, and a locator "
                "when available. Do not infer facts not supported by the "
                "document.\n\n"
                f"SOURCE DOCUMENT:\n{document.text}"
            ),
            text_format=_FindingResponse,
            max_output_tokens=self._max_output_tokens,
        )

        parsed = None

        for output_item in response.output:
            if getattr(output_item, "type", None) != "message":
                continue

            for content_item in output_item.content:
                if getattr(content_item, "type", None) != "output_text":
                    continue

                parsed = getattr(
                    content_item,
                    "parsed",
                    None,
                )

                if parsed is not None:
                    break

            if parsed is not None:
                break

        if parsed is None:
            raise ValueError(
                "OpenAI response did not contain parsed output_text"
            )

        proposals = tuple(
            SemanticFindingProposal(
                statement=finding.statement,
                evidence_text=finding.evidence_text,
                locator=finding.locator,
            )
            for finding in parsed.findings
        )

        return AnalyzerExecutionResult(
            proposals=proposals,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
