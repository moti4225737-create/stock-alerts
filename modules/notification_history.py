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

        self._delivered_event_ids.add(event_id)
        self._persist()

    def _persist(self) -> None:
        if not self._path:
            return

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            "\n".join(sorted(self._delivered_event_ids)) + ("\n" if self._delivered_event_ids else ""),
            encoding="utf-8",
        )
