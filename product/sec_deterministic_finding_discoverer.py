from typing import Protocol

from models.source_document import SourceDocument
from models.source_evidence import SourceEvidence
from models.source_finding_candidate import SourceFindingCandidate


class SignalExtractor(Protocol):
    def extract(
        self,
        text: str,
    ) -> dict[str, str]:
        ...


class SECDeterministicFindingDiscoverer:
    def __init__(
        self,
        signal_extractor: SignalExtractor,
    ) -> None:
        self._signal_extractor = signal_extractor

    def discover(
        self,
        document: SourceDocument,
    ) -> tuple[SourceFindingCandidate, ...]:
        if document.source.upper() != "SEC":
            return ()

        signals = self._signal_extractor.extract(
            document.text
        )

        candidates: list[SourceFindingCandidate] = []

        revenue = signals.get("revenue")
        if revenue:
            candidates.append(
                SourceFindingCandidate(
                    statement=f"Revenue {revenue}.",
                    evidence=(
                        SourceEvidence(
                            source_url=document.source_url,
                            text=f"Revenue {revenue}",
                        ),
                    ),
                )
            )

        cash = signals.get("cash")
        if cash:
            candidates.append(
                SourceFindingCandidate(
                    statement=(
                        "Cash and cash equivalents were "
                        f"{cash}."
                    ),
                    evidence=(
                        SourceEvidence(
                            source_url=document.source_url,
                            text=(
                                "Cash and cash equivalents were "
                                f"{cash}"
                            ),
                        ),
                    ),
                )
            )

        net_loss = signals.get("net_loss")
        if net_loss:
            candidates.append(
                SourceFindingCandidate(
                    statement=f"Net loss was {net_loss}.",
                    evidence=(
                        SourceEvidence(
                            source_url=document.source_url,
                            text=f"Net loss was {net_loss}",
                        ),
                    ),
                )
            )

        return tuple(candidates)
