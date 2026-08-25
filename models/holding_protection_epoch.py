from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class HoldingProtectionEpoch:
    canonical_instrument_id: str
    time_zero: datetime

    def __post_init__(self) -> None:
        canonical_instrument_id = self.canonical_instrument_id.strip()

        if not canonical_instrument_id:
            raise ValueError("canonical_instrument_id must not be empty")

        if (
            not isinstance(self.time_zero, datetime)
            or self.time_zero.tzinfo is None
            or self.time_zero.utcoffset() is None
        ):
            raise ValueError("time_zero must be timezone-aware")

        object.__setattr__(
            self,
            "canonical_instrument_id",
            canonical_instrument_id,
        )


class HoldingProtectionEpochs:
    def __init__(
        self,
        *,
        clock: Callable[[], datetime],
        restored_epochs: Iterable[HoldingProtectionEpoch] = (),
    ) -> None:
        self._clock = clock
        self._epochs: dict[str, HoldingProtectionEpoch] = {}

        for epoch in restored_epochs:
            if not isinstance(epoch, HoldingProtectionEpoch):
                raise TypeError(
                    "restored_epochs must contain HoldingProtectionEpoch"
                )

            if epoch.canonical_instrument_id in self._epochs:
                raise ValueError(
                    "duplicate restored canonical instrument identity"
                )

            self._epochs[epoch.canonical_instrument_id] = epoch

    def establish(
        self,
        canonical_instrument_id: str,
    ) -> HoldingProtectionEpoch:
        normalized_identity = canonical_instrument_id.strip()

        existing = self._epochs.get(normalized_identity)
        if existing is not None:
            return existing

        epoch = HoldingProtectionEpoch(
            canonical_instrument_id=normalized_identity,
            time_zero=self._clock(),
        )
        self._epochs[normalized_identity] = epoch

        return epoch
