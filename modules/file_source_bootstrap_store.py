import json
import os
import tempfile
from hashlib import sha256
from datetime import datetime
from pathlib import Path

from models.company_identity import CompanyIdentity
from models.portfolio_holding import PortfolioHolding
from models.source_bootstrap_state import (
    OpeningFactCandidate,
    OpeningFactDecision,
    OpeningFactDisposition,
    OpeningResearchResult,
    SourceBootstrapResearchRequest,
    SourceBootstrapState,
)
from models.source_evidence import SourceEvidence


class SourceBootstrapStorageError(RuntimeError):
    pass


class FileSourceBootstrapStore:
    _SCHEMA = "stock-sentinel.source-bootstrap"
    _VERSION = 2

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def load(
        self,
        *,
        target_holding: PortfolioHolding,
    ) -> SourceBootstrapState | None:
        try:
            state_path = self._state_path(target_holding.symbol)
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            state = self._deserialize(payload)
            if state.request.holding.symbol != target_holding.symbol:
                raise ValueError(
                    "persisted state does not belong to target holding"
                )
            return state
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
            message = (
                "Persisted Source Bootstrap state does not belong to "
                "target holding"
                if "does not belong to target holding" in str(exc)
                else "Unable to load Source Bootstrap state"
            )
            raise SourceBootstrapStorageError(message) from exc

    def save(self, state: SourceBootstrapState) -> None:
        temporary_path: Path | None = None
        try:
            state_path = self._state_path(state.request.holding.symbol)
            serialized = json.dumps(
                self._serialize(state),
                ensure_ascii=False,
                indent=2,
            )
            state_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=state_path.parent,
                prefix=f".{state_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(serialized)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, state_path)
            temporary_path = None
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            raise SourceBootstrapStorageError(
                "Unable to save Source Bootstrap state"
            ) from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _state_path(self, symbol: str) -> Path:
        key = sha256(symbol.encode("utf-8")).hexdigest()
        return self._path / f"{key}.json"

    @classmethod
    def _serialize(cls, state: SourceBootstrapState) -> dict:
        identity = state.verified_identity
        research = state.research_output
        if identity is not None and not isinstance(identity, CompanyIdentity):
            raise ValueError("verified identity is required")
        if research is not None and not isinstance(research, OpeningResearchResult):
            raise ValueError("Opening research result is required")

        if state.decisions and not isinstance(research, OpeningResearchResult):
            raise ValueError("decisions require an Opening research result")

        available_indices = list(
            range(len(research.candidates))
            if isinstance(research, OpeningResearchResult)
            else ()
        )
        decisions = []
        for decision in state.decisions:
            matching_index = next(
                (
                    index
                    for index in available_indices
                    if research.candidates[index] == decision.candidate
                ),
                None,
            )
            if matching_index is None:
                raise ValueError("decision candidate is not in research")
            available_indices.remove(matching_index)
            decisions.append({
                "candidate_index": matching_index,
                "disposition": decision.disposition.value,
            })

        return {
            "schema": cls._SCHEMA,
            "version": cls._VERSION,
            "request": {
                "holding": cls._holding(state.request.holding),
                "time_zero": state.time_zero.isoformat(),
            },
            "verified_identity": (
                cls._identity(identity) if identity is not None else None
            ),
            "research_output": (
                {
                    "completed_successfully": research.completed_successfully,
                    "candidates": [
                        cls._candidate(candidate)
                        for candidate in research.candidates
                    ],
                }
                if isinstance(research, OpeningResearchResult)
                else None
            ),
            "decisions": decisions,
        }

    @classmethod
    def _deserialize(cls, payload: object) -> SourceBootstrapState:
        value = cls._object(payload, "persisted state")
        if set(value) != {
            "schema",
            "version",
            "request",
            "verified_identity",
            "research_output",
            "decisions",
        }:
            raise ValueError("persisted state has unexpected fields")
        if value["schema"] != cls._SCHEMA:
            raise ValueError("incompatible Source Bootstrap schema")
        if value["version"] != cls._VERSION:
            raise ValueError("incompatible Source Bootstrap version")

        request_payload = cls._object(value["request"], "request")
        if set(request_payload) != {"holding", "time_zero"}:
            raise ValueError("request has unexpected fields")
        research_payload = value["research_output"]
        if research_payload is None:
            candidates = ()
            research_output = None
        else:
            research_value = cls._object(research_payload, "research output")
            if set(research_value) != {
                "completed_successfully",
                "candidates",
            }:
                raise ValueError("research output has unexpected fields")
            candidates = tuple(
                cls._load_candidate(candidate)
                for candidate in cls._array(
                    research_value["candidates"], "candidates"
                )
            )
            completed_successfully = research_value["completed_successfully"]
            if not isinstance(completed_successfully, bool):
                raise ValueError("research completion must be boolean")
            research_output = OpeningResearchResult(
                candidates=candidates,
                completed_successfully=completed_successfully,
            )

        decisions = []
        used_indices: set[int] = set()
        for item in cls._array(value["decisions"], "decisions"):
            decision = cls._object(item, "decision")
            if set(decision) != {"candidate_index", "disposition"}:
                raise ValueError("decision has unexpected fields")
            index = decision["candidate_index"]
            if (
                isinstance(index, bool)
                or not isinstance(index, int)
                or index < 0
                or index >= len(candidates)
                or index in used_indices
            ):
                raise ValueError("decision candidate association is invalid")
            used_indices.add(index)
            decisions.append(OpeningFactDecision(
                candidate=candidates[index],
                disposition=OpeningFactDisposition(decision["disposition"]),
            ))

        state = SourceBootstrapState(
            request=SourceBootstrapResearchRequest(
                holding=cls._load_holding(request_payload["holding"]),
                time_zero=cls._datetime(request_payload["time_zero"]),
            ),
            verified_identity=(
                cls._load_identity(value["verified_identity"])
                if value["verified_identity"] is not None
                else None
            ),
            research_output=research_output,
            decisions=tuple(decisions),
        )
        return state

    @staticmethod
    def _holding(value: PortfolioHolding) -> dict:
        return {
            "symbol": value.symbol,
            "quantity": str(value.quantity),
            "average_cost": value.average_cost,
        }

    @staticmethod
    def _identity(value: CompanyIdentity) -> dict:
        return {
            "ticker": value.ticker,
            "company_name": value.company_name,
            "cik": value.cik,
            "exchange": value.exchange,
        }

    @staticmethod
    def _candidate(value: OpeningFactCandidate) -> dict:
        return {
            "fact": value.fact,
            "category": value.category,
            "evidence": [
                {
                    "source_url": evidence.source_url,
                    "text": evidence.text,
                    "locator": evidence.locator,
                }
                for evidence in value.evidence
            ],
        }

    @classmethod
    def _load_holding(cls, payload: object) -> PortfolioHolding:
        value = cls._object(payload, "holding")
        if set(value) not in (
            {"symbol", "quantity"},
            {"symbol", "quantity", "average_cost"},
        ):
            raise ValueError("holding has unexpected fields")
        return PortfolioHolding(
            symbol=value["symbol"],
            quantity=value["quantity"],
            average_cost=value.get("average_cost"),
        )

    @classmethod
    def _load_identity(cls, payload: object) -> CompanyIdentity:
        value = cls._object(payload, "verified identity")
        if set(value) != {"ticker", "company_name", "cik", "exchange"}:
            raise ValueError("verified identity has unexpected fields")
        return CompanyIdentity(
            ticker=value["ticker"],
            company_name=value["company_name"],
            cik=value["cik"],
            exchange=value["exchange"],
        )

    @classmethod
    def _load_candidate(cls, payload: object) -> OpeningFactCandidate:
        value = cls._object(payload, "candidate")
        if set(value) != {"fact", "category", "evidence"}:
            raise ValueError("candidate has unexpected fields")
        return OpeningFactCandidate(
            fact=value["fact"],
            category=value["category"],
            evidence=tuple(
                cls._load_evidence(item)
                for item in cls._array(value["evidence"], "evidence")
            ),
        )

    @classmethod
    def _load_evidence(cls, payload: object) -> SourceEvidence:
        value = cls._object(payload, "evidence")
        if set(value) != {"source_url", "text", "locator"}:
            raise ValueError("evidence has unexpected fields")
        return SourceEvidence(
            source_url=value["source_url"],
            text=value["text"],
            locator=value["locator"],
        )

    @staticmethod
    def _object(value: object, name: str) -> dict:
        if not isinstance(value, dict):
            raise ValueError(f"{name} must be an object")
        return value

    @staticmethod
    def _array(value: object, name: str) -> list:
        if not isinstance(value, list):
            raise ValueError(f"{name} must be an array")
        return value

    @staticmethod
    def _datetime(value: object) -> datetime:
        if not isinstance(value, str):
            raise ValueError("time_zero must be an ISO-8601 string")
        return datetime.fromisoformat(value)
