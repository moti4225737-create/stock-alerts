from dataclasses import dataclass
from enum import Enum

from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)


class InstrumentClass(str, Enum):
    OPERATING_COMPANY_EQUITY = "operating_company_equity"
    ETF_OR_FUND = "etf_or_fund"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class HoldingIdentityEvidence:
    source: str
    reference: str

    def __post_init__(self) -> None:
        source = self.source.strip()
        reference = self.reference.strip()

        if not source:
            raise ValueError("evidence source must not be empty")
        if not reference:
            raise ValueError("evidence reference must not be empty")

        object.__setattr__(self, "source", source)
        object.__setattr__(self, "reference", reference)


@dataclass(frozen=True, slots=True)
class VerifiedHoldingIdentity:
    canonical_instrument_id: str
    symbol: str
    instrument_class: InstrumentClass

    def __post_init__(self) -> None:
        canonical_instrument_id = self.canonical_instrument_id.strip()
        symbol = self.symbol.strip().upper()

        if not canonical_instrument_id:
            raise ValueError("canonical_instrument_id must not be empty")
        if not symbol:
            raise ValueError("symbol must not be empty")
        if not isinstance(self.instrument_class, InstrumentClass):
            raise TypeError("instrument_class must be an InstrumentClass")

        object.__setattr__(
            self,
            "canonical_instrument_id",
            canonical_instrument_id,
        )
        object.__setattr__(self, "symbol", symbol)


@dataclass(frozen=True, slots=True)
class HoldingIdentityResult:
    status: OpeningPictureMemberResultStatus
    identity: VerifiedHoldingIdentity | None
    evidence: tuple[HoldingIdentityEvidence, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, OpeningPictureMemberResultStatus):
            raise TypeError(
                "status must be an OpeningPictureMemberResultStatus"
            )
        if self.identity is not None and not isinstance(
            self.identity,
            VerifiedHoldingIdentity,
        ):
            raise TypeError("identity must be a VerifiedHoldingIdentity")

        evidence = tuple(self.evidence)
        if not all(
            isinstance(item, HoldingIdentityEvidence)
            for item in evidence
        ):
            raise TypeError(
                "evidence must contain HoldingIdentityEvidence"
            )

        if self.status is OpeningPictureMemberResultStatus.ESTABLISHED:
            if self.identity is None:
                raise ValueError("ESTABLISHED identity must be present")
            if not evidence:
                raise ValueError("ESTABLISHED identity requires evidence")
        elif self.identity is not None:
            raise ValueError(
                "identity is authoritative only for ESTABLISHED results"
            )

        object.__setattr__(self, "evidence", evidence)
