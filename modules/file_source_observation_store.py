import json
import os
import tempfile
from hashlib import sha256
from pathlib import Path

from models.source_observation import SourceObservationState


class SourceObservationStorageError(RuntimeError):
    pass


class FileSourceObservationStore:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def load(self, *, source: str, scope: str) -> SourceObservationState | None:
        try:
            payload = json.loads(
                self._state_path(source, scope).read_text(encoding="utf-8")
            )
            state = self._deserialize(payload)
            if state.source != source or state.scope != scope:
                raise ValueError("persisted observation belongs to another scope")
            return state
        except FileNotFoundError:
            return None
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            raise SourceObservationStorageError(
                "Unable to load Source Observation state"
            ) from exc

    def save(self, state: SourceObservationState) -> None:
        temporary_path: Path | None = None
        try:
            state_path = self._state_path(state.source, state.scope)
            serialized = json.dumps(
                self._serialize(state),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
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
            raise SourceObservationStorageError(
                "Unable to save Source Observation state"
            ) from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _state_path(self, source: str, scope: str) -> Path:
        key = sha256(f"{source}\0{scope}".encode("utf-8")).hexdigest()
        return self._path / f"{key}.json"

    @staticmethod
    def _serialize(state: SourceObservationState) -> dict:
        return {
            "schema": state.schema,
            "version": state.version,
            "source": state.source,
            "scope": state.scope,
            "objects": state.objects,
            "pending": list(state.pending),
            "observed_through": state.observed_through,
        }

    @staticmethod
    def _deserialize(payload: object) -> SourceObservationState:
        if not isinstance(payload, dict):
            raise ValueError("persisted observation must be an object")
        if set(payload) not in ({
            "schema", "version", "source", "scope", "objects", "pending"
        }, {
            "schema", "version", "source", "scope", "objects", "pending",
            "observed_through",
        }):
            raise ValueError("persisted observation has unexpected fields")
        if payload["schema"] != "stock-sentinel.source-observation":
            raise ValueError("incompatible Source Observation schema")
        if type(payload["version"]) is not int or payload["version"] != 1:
            raise ValueError("unsupported Source Observation version")
        if not isinstance(payload["objects"], dict):
            raise ValueError("objects must be an object")
        if not isinstance(payload["pending"], list):
            raise ValueError("pending must be an array")
        return SourceObservationState(
            schema=payload["schema"],
            version=payload["version"],
            source=payload["source"],
            scope=payload["scope"],
            objects=payload["objects"],
            pending=tuple(payload["pending"]),
            observed_through=payload.get("observed_through"),
        )
