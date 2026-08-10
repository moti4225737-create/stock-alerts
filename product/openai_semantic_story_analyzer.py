from pydantic import BaseModel, Field

from models.event import Event
from models.story_correlation_result import (
    StoryCorrelationResult,
)


class _StoryCorrelationResponse(BaseModel):
    is_correlated: bool
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
                "to the same continuing investment story.\n\n"
                "Do not correlate events merely because they "
                "mention the same company, product, or asset.\n"
                "Correlate only when the later event is a "
                "continuation, confirmation, completion, "
                "reversal, or validation of the earlier event.\n"
                "If the available text is insufficient, do not "
                "invent a relationship and use lower confidence.\n\n"
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
            is_correlated=parsed.is_correlated,
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
