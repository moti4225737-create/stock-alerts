from pydantic import BaseModel, Field

from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationDecision,
    StoryCorrelationResult,
)


class _StoryCorrelationResponse(BaseModel):
    decision: StoryCorrelationDecision
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    reason: str


class OpenAISemanticStoryAnalyzer:
    def __init__(
        self,
        client,
        model: str,
        max_output_tokens: int = 300,
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
        earlier_event: Event,
        current_event: Event,
    ) -> StoryCorrelationResult:
        response = self._client.responses.parse(
            model=self._model,
            input=(
                "Determine whether these two events belong "
                "to the SAME SPECIFIC continuing investment story.\n\n"

                "A story is a specific transaction, regulatory process, "
                "legal proceeding, financing event, clinical program "
                "milestone, or other identifiable catalyst/process.\n\n"

                "Return exactly one decision:\n"
                "- match: the later event continues, confirms, completes, "
                "reverses, corrects, or validates the SAME specific "
                "underlying process or catalyst.\n"
                "- no_match: the events concern different specific "
                "processes or catalysts.\n"
                "- unresolved: the available evidence does not establish "
                "whether they concern the same specific process.\n\n"

                "STRICT IDENTITY RULES:\n"
                "1. Same company is not enough.\n"
                "2. Same product or asset is not enough.\n"
                "3. Same broad topic or investment theme is not enough.\n"
                "4. Chronological sequence is not enough.\n"
                "5. Similar transaction type is not enough.\n"
                "6. Do not infer that two acquisitions are the same "
                "without sufficient target or transaction identity.\n"
                "7. Different story domains involving the same asset "
                "are separate stories unless the text explicitly "
                "establishes a direct continuation of the same process.\n"
                "8. Separate quarterly reporting periods are separate "
                "stories unless the later event explicitly restates, "
                "corrects, or otherwise continues the earlier report.\n"
                "9. References such as 'previously announced', "
                "'the transaction', 'the application', or equivalent "
                "may establish continuity when the surrounding evidence "
                "resolves the reference reliably.\n"
                "10. If identity remains plausible but unproven, return "
                "unresolved rather than match.\n\n"

                "Confidence means confidence in the DECISION returned. "
                "Therefore an unresolved decision may have high confidence "
                "when it is clear that the evidence is insufficient.\n\n"

                "EARLIER EVENT\n"
                f"Symbol: {earlier_event.symbol}\n"
                f"Title: {earlier_event.title}\n"
                f"Summary: {earlier_event.summary}\n"
                f"Published: {earlier_event.published_at}\n\n"

                "CURRENT EVENT\n"
                f"Symbol: {current_event.symbol}\n"
                f"Title: {current_event.title}\n"
                f"Summary: {current_event.summary}\n"
                f"Published: {current_event.published_at}"
            ),
            text_format=_StoryCorrelationResponse,
            max_output_tokens=self._max_output_tokens,
        )

        parsed = self._find_parsed_output(response)

        return StoryCorrelationResult(
            decision=parsed.decision,
            confidence=parsed.confidence,
            reason=parsed.reason,
        )

    @staticmethod
    def _find_parsed_output(
        response,
    ) -> _StoryCorrelationResponse:
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
            "story correlation output"
        )
