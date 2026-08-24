from collections.abc import Callable
from datetime import datetime, timezone

from application.portfolio_source import PortfolioSource
from application.portfolio_truth_reconciler import PortfolioTruthReconciler
from models.accepted_portfolio_truth import AcceptedPortfolioTruth
from models.portfolio import Portfolio
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

    @property
    def portfolio(self) -> Portfolio | None:
        if self._reconciler is None:
            return None
        return self._reconciler.portfolio

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
        return True
