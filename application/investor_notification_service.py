from models.investor_brief import InvestorBrief
from presentation.telegram_intelligence_message_builder import (
    TelegramIntelligenceMessageBuilder,
)


class InvestorNotificationService:
    def __init__(
        self,
        telegram_builder: TelegramIntelligenceMessageBuilder | None = None,
    ) -> None:
        self._telegram_builder = telegram_builder or TelegramIntelligenceMessageBuilder()

    def generate_messages(self, briefs: list[InvestorBrief]) -> tuple[str, ...]:
        return tuple(self._telegram_builder.build(brief) for brief in briefs)
