import os
import tempfile
from pathlib import Path


class NotificationHistory:
    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path is not None else None
        self._delivered_event_ids: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self._path or not self._path.exists():
            return

        self._delivered_event_ids = {
            line.strip()
            for line in self._path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }

    def has_delivered(self, event_id: str) -> bool:
        return event_id in self._delivered_event_ids

    def record(self, event_id: str) -> None:
        if not event_id:
            return

        candidate = self._delivered_event_ids | {event_id}
        self._persist(candidate)
        self._delivered_event_ids = candidate

    def _persist(self, candidate: set[str]) -> None:
        if not self._path:
            return

        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n",
                dir=self._path.parent, prefix=f".{self._path.name}.",
                suffix=".tmp", delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write("\n".join(sorted(candidate)) + ("\n" if candidate else ""))
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self._path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
