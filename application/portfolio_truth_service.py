from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone

from application.portfolio_source import PortfolioSource
from application.portfolio_truth_reconciler import PortfolioTruthReconciler
from models.accepted_portfolio_truth import AcceptedPortfolioTruth
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import (
    SourceBootstrapResearchRequest,
    SourceBootstrapState,
)
from modules.file_portfolio_truth_store import (
    FilePortfolioTruthStore,
    PortfolioTruthStorageError,
)


class PortfolioTruthService:
    def __init__(
        self,
        source: PortfolioSource,
        store: FilePortfolioTruthStore,
        clock: Callable[[], datetime],
    ) -> None:
        self._source = source
        self._store = store
        self._clock = clock
        self._reconciler: PortfolioTruthReconciler | None = None
        self._source_bootstraps: dict[str, SourceBootstrapState] = {}
        self._introduced_holdings: tuple[PortfolioHolding, ...] = ()

    @property
    def portfolio(self) -> Portfolio | None:
        if self._reconciler is None:
            return None
        return self._reconciler.portfolio

    @property
    def introduced_holdings(self) -> tuple[PortfolioHolding, ...]:
        return tuple(self._introduced_holdings)

    def restore(self) -> bool:
        restored_truth = self._store.load()
        if restored_truth is None:
            return False

        try:
            restored_portfolio = Portfolio(restored_truth.positions)
        except ValueError as exc:
            raise PortfolioTruthStorageError(
                "Restored portfolio truth is invalid"
            ) from exc

        reconciler = PortfolioTruthReconciler()
        reconciler.restore(restored_portfolio)
        self._reconciler = reconciler
        return True

    def refresh(self) -> bool:
        result = self._source.acquire()
        candidate = result.candidate
        if candidate is None or not candidate.is_eligible_for_acceptance:
            return False

        Portfolio(candidate.positions)
        previous_symbols = {
            holding.symbol
            for holding in (
                self.portfolio.holdings
                if self.portfolio is not None
                else ()
            )
        }
        candidate_symbols = {
            holding.symbol for holding in candidate.positions
        }

        accepted_at = self._clock()
        if accepted_at.tzinfo is None or accepted_at.utcoffset() is None:
            raise ValueError("accepted_at must be timezone-aware")

        accepted_truth = AcceptedPortfolioTruth(
            positions=candidate.positions,
            source_as_of=candidate.source_as_of,
            accepted_at=accepted_at.astimezone(timezone.utc),
        )
        self._store.save(accepted_truth)

        reconciler = self._reconciler or PortfolioTruthReconciler()
        reconciler.apply(result)
        self._reconciler = reconciler
        for removed_symbol in previous_symbols - candidate_symbols:
            self._source_bootstraps.pop(removed_symbol, None)
        self._introduced_holdings = tuple(
            holding
            for holding in candidate.positions
            if holding.symbol not in previous_symbols
        )
        return True

    def begin_source_bootstrap(
        self,
        *,
        target_holding: PortfolioHolding,
        research: Callable[[SourceBootstrapResearchRequest], object],
    ) -> SourceBootstrapState | None:
        portfolio = self.portfolio
        if portfolio is None:
            raise RuntimeError("Portfolio Truth is unavailable")

        holding = portfolio.get(target_holding.symbol)
        if holding is None:
            return None

        existing = self._source_bootstraps.get(holding.symbol)
        if existing is not None:
            return existing

        if not any(
            introduced.symbol == holding.symbol
            for introduced in self._introduced_holdings
        ):
            return None

        time_zero = self._clock()
        request = SourceBootstrapResearchRequest(
            holding=holding,
            time_zero=time_zero,
        )
        state = SourceBootstrapState(request=request)
        self._source_bootstraps[holding.symbol] = state

        state = replace(state, research_output=research(request))
        self._source_bootstraps[holding.symbol] = state
        return state

    def record_source_bootstrap(self, state: SourceBootstrapState) -> None:
        portfolio = self.portfolio
        if portfolio is None:
            raise RuntimeError("Portfolio Truth is unavailable")

        symbol = state.request.holding.symbol
        if portfolio.get(symbol) is None:
            raise RuntimeError(
                "Source Bootstrap state does not belong to current Portfolio Truth"
            )

        existing = self._source_bootstraps.get(symbol)
        if existing is None or existing.time_zero != state.time_zero:
            raise RuntimeError(
                "Source Bootstrap state does not belong to active lifecycle"
            )
        self._source_bootstraps[symbol] = state
