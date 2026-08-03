from models.investor_brief import InvestorBrief
from presentation.telegram_formatter import TelegramFormatter
from product.investor_intelligence_card_orchestrator import (
    InvestorIntelligenceCardOrchestrator,
)


class TelegramIntelligenceMessageBuilder:
    def __init__(
        self,
        orchestrator: InvestorIntelligenceCardOrchestrator | None = None,
        formatter: TelegramFormatter | None = None,
    ) -> None:
        self._orchestrator = (
            orchestrator or InvestorIntelligenceCardOrchestrator()
        )
        self._formatter = formatter or TelegramFormatter()

    def build(self, brief: InvestorBrief) -> str:
        card = self._orchestrator.build(brief)
        return self._formatter.format(card)