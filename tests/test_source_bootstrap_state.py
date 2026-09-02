from datetime import datetime
from decimal import Decimal

import pytest

from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import SourceBootstrapResearchRequest


def test_source_bootstrap_research_request_rejects_naive_time_zero() -> None:
    with pytest.raises(ValueError, match="time_zero must be timezone-aware"):
        SourceBootstrapResearchRequest(
            holding=PortfolioHolding(
                symbol="ONDS",
                quantity=Decimal("25"),
            ),
            time_zero=datetime(2026, 8, 24, 13, 0),
        )
