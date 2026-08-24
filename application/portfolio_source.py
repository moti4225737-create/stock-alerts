from typing import Protocol

from application.portfolio_truth_reconciler import PortfolioAcquisitionResult


class PortfolioSource(Protocol):
    def acquire(self) -> PortfolioAcquisitionResult:
        ...
