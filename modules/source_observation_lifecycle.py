from abc import ABC, abstractmethod


class ManagedSourceObservationProvider(ABC):
    """
    Shared lifecycle contract for providers participating in Source Observation.

    Source-specific acquisition, identity, normalization, occurrence semantics,
    delta construction, and attempt setup remain provider responsibilities.
    """

    @abstractmethod
    def acknowledge_pending(self) -> None:
        """Acknowledge pending events exposed by successful processing."""
        raise NotImplementedError