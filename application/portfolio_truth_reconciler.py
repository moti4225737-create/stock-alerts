from dataclasses import dataclass

from models.candidate_portfolio_snapshot import CandidatePortfolioSnapshot
from models.portfolio import Portfolio


@dataclass(frozen=True)
class PortfolioAcquisitionResult:
    candidate: CandidatePortfolioSnapshot | None

    @classmethod
    def succeeded(
        cls,
        candidate: CandidatePortfolioSnapshot,
    ) -> "PortfolioAcquisitionResult":
        return cls(candidate=candidate)

    @classmethod
    def failed(cls) -> "PortfolioAcquisitionResult":
        return cls(candidate=None)


class PortfolioTruthReconciler:
    def __init__(self) -> None:
        self._portfolio = Portfolio([])

    @property
    def portfolio(self) -> Portfolio:
        return Portfolio(self._portfolio.holdings)

    def restore(self, portfolio: Portfolio) -> None:
        self._portfolio = Portfolio(portfolio.holdings)

    def apply(self, result: PortfolioAcquisitionResult) -> None:
        candidate = result.candidate
        if candidate is None or not candidate.is_eligible_for_acceptance:
            return

        self._portfolio = Portfolio(candidate.positions)
