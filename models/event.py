from dataclasses import dataclass
from typing import Optional


@dataclass
class Event:
    symbol: str
    source: str
    title: str
    summary: str
    published_at: str
    importance: int
    sentiment: str
    url: Optional[str] = None