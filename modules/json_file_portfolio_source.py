import json
from datetime import datetime
from pathlib import Path

from application.portfolio_truth_reconciler import PortfolioAcquisitionResult
from models.candidate_portfolio_snapshot import (
    CandidatePortfolioSnapshot,
    SnapshotCompleteness,
)
from models.portfolio_holding import PortfolioHolding


class JsonFilePortfolioSource:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def acquire(self) -> PortfolioAcquisitionResult:
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            candidate = self._parse_candidate(payload)
        except (
            OSError,
            UnicodeError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ):
            return PortfolioAcquisitionResult.failed()

        return PortfolioAcquisitionResult.succeeded(candidate)

    @classmethod
    def _parse_candidate(cls, payload: object) -> CandidatePortfolioSnapshot:
        if not isinstance(payload, dict):
            raise ValueError("candidate payload must be an object")

        positions_payload = payload["positions"]
        if not isinstance(positions_payload, list):
            raise ValueError("positions must be an array")

        source_as_of = cls._parse_aware_datetime(payload["source_as_of"])
        completeness = SnapshotCompleteness(payload["completeness"])
        positions = tuple(
            cls._parse_holding(position) for position in positions_payload
        )

        return CandidatePortfolioSnapshot(
            positions=positions,
            source_as_of=source_as_of,
            completeness=completeness,
        )

    @staticmethod
    def _parse_holding(payload: object) -> PortfolioHolding:
        if not isinstance(payload, dict):
            raise ValueError("position must be an object")

        quantity = payload["quantity"]
        if not isinstance(quantity, str):
            raise ValueError("quantity must be a decimal string")

        average_cost = payload.get("average_cost")
        if average_cost is not None and (
            isinstance(average_cost, bool)
            or not isinstance(average_cost, (int, float))
        ):
            raise ValueError("average_cost must be numeric or null")

        return PortfolioHolding(
            symbol=payload["symbol"],
            quantity=quantity,
            average_cost=average_cost,
        )

    @staticmethod
    def _parse_aware_datetime(value: object) -> datetime:
        if not isinstance(value, str):
            raise ValueError("timestamp must be an ISO-8601 string")

        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")

        return parsed
