import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from models.accepted_portfolio_truth import AcceptedPortfolioTruth
from models.portfolio_holding import PortfolioHolding


class PortfolioTruthStorageError(RuntimeError):
    pass


class FilePortfolioTruthStore:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def load(self) -> AcceptedPortfolioTruth | None:
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            return self._deserialize(payload)
        except FileNotFoundError:
            return None
        except (
            OSError,
            UnicodeError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as exc:
            raise PortfolioTruthStorageError(
                "Unable to load authoritative portfolio truth"
            ) from exc

    def save(self, truth: AcceptedPortfolioTruth) -> None:
        temporary_path: Path | None = None

        try:
            serialized = json.dumps(
                self._serialize(truth),
                ensure_ascii=False,
                indent=2,
            )
            self._path.parent.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(serialized)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, self._path)
            temporary_path = None
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            raise PortfolioTruthStorageError(
                "Unable to save authoritative portfolio truth"
            ) from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def _serialize(truth: AcceptedPortfolioTruth) -> dict:
        return {
            "positions": [
                {
                    "symbol": holding.symbol,
                    "quantity": str(holding.quantity),
                    "average_cost": holding.average_cost,
                }
                for holding in truth.positions
            ],
            "source_as_of": truth.source_as_of.isoformat(),
            "accepted_at": truth.accepted_at.isoformat(),
        }

    @classmethod
    def _deserialize(cls, payload: object) -> AcceptedPortfolioTruth:
        if not isinstance(payload, dict):
            raise ValueError("persisted truth must be an object")

        positions_payload = payload["positions"]
        if not isinstance(positions_payload, list):
            raise ValueError("positions must be an array")

        return AcceptedPortfolioTruth(
            positions=tuple(
                cls._deserialize_holding(position)
                for position in positions_payload
            ),
            source_as_of=cls._parse_datetime(payload["source_as_of"]),
            accepted_at=cls._parse_datetime(payload["accepted_at"]),
        )

    @staticmethod
    def _deserialize_holding(payload: object) -> PortfolioHolding:
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
    def _parse_datetime(value: object) -> datetime:
        if not isinstance(value, str):
            raise ValueError("timestamp must be an ISO-8601 string")
        return datetime.fromisoformat(value)
