from dataclasses import replace
from collections.abc import Callable

from application.portfolio_truth_service import PortfolioTruthService
from models.source_bootstrap_state import (
    SourceBootstrapResearchRequest,
    SourceBootstrapState,
)
from models.portfolio_holding import PortfolioHolding
from modules.file_source_bootstrap_store import FileSourceBootstrapStore
from modules.sec_company_identity_resolver import SECCompanyIdentityResolver


class SourceBootstrapApplication:
    def __init__(
        self,
        *,
        portfolio_service: PortfolioTruthService,
        store: FileSourceBootstrapStore,
    ) -> None:
        self._portfolio_service = portfolio_service
        self._store = store

    def run(
        self,
        *,
        target_holding: PortfolioHolding,
        research: Callable[..., object],
        identity_resolver: SECCompanyIdentityResolver,
        opening_verification: Callable[[SourceBootstrapState], object],
    ) -> SourceBootstrapState:
        is_introduced = any(
            holding.symbol == target_holding.symbol
            for holding in self._portfolio_service.introduced_holdings
        )
        restored = (
            None
            if is_introduced
            else self._store.load(target_holding=target_holding)
        )
        if restored is not None:
            if restored.request.holding.symbol != target_holding.symbol:
                raise RuntimeError(
                    "Persisted Source Bootstrap state does not belong to "
                    "target holding"
                )
            return restored

        verified_identity = None

        def research_with_verified_identity(
            request: SourceBootstrapResearchRequest,
        ) -> object:
            nonlocal verified_identity
            identity = identity_resolver.resolve(request.holding.symbol)
            verified_identity = identity
            return research(request, known_identity=identity)

        state = self._portfolio_service.begin_source_bootstrap(
            target_holding=target_holding,
            research=research_with_verified_identity,
        )
        if state is None:
            raise RuntimeError("No newly introduced holding to bootstrap")
        if state.request.holding.symbol != target_holding.symbol:
            raise RuntimeError(
                "Source Bootstrap state does not belong to target holding"
            )

        completed = replace(
            state,
            verified_identity=verified_identity,
        )
        completed = replace(
            completed,
            decisions=tuple(opening_verification(completed)),
        )
        self._store.save(completed)
        self._portfolio_service.record_source_bootstrap(completed)
        return completed
