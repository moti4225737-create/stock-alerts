from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from models.asset_kind import AssetKind


@dataclass(frozen=True, slots=True)
class Asset:
    name: str
    kind: AssetKind
    subtype: str | None = None
    aliases: tuple[str, ...] = ()
    status: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )