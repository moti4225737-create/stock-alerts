"""Documentation Checkpoint continuous-accountability domain contract."""

from dataclasses import dataclass


PENDING = "PENDING"
RESOLVED = "RESOLVED"


@dataclass
class CheckpointOutcome:
    outcome_id: str
    provenance_ref: str
    responsibility_ref: str
    status: str = PENDING
    technical_state: str | None = None
    resolution_basis: str | None = None
    parent_outcome_id: str | None = None
    resolution_valid: bool = False
    invalidity_basis: str | None = None


class SprintCheckpointCollection:
    """Sprint-scoped checkpoint accounting; not a Closure authority."""

    def __init__(self, sprint_id: str):
        if not sprint_id:
            raise ValueError("sprint_id is required")
        self.sprint_id = sprint_id
        self.outcomes: dict[str, CheckpointOutcome] = {}
        self.population_review_valid = False
        self.population_comparison_ref: str | None = None

    def intake(
        self,
        *,
        outcome_id: str,
        provenance_ref: str,
        responsibility_ref: str,
        parent_outcome_id: str | None = None,
    ) -> CheckpointOutcome:
        if outcome_id in self.outcomes:
            existing = self.outcomes[outcome_id]
            if existing.provenance_ref != provenance_ref:
                raise ValueError(
                    "existing outcome_id has conflicting provenance"
                )
            return existing

        if (
            parent_outcome_id is not None
            and parent_outcome_id not in self.outcomes
        ):
            raise ValueError("parent_outcome_id must reference an existing outcome")

        outcome = CheckpointOutcome(
            outcome_id=outcome_id,
            provenance_ref=provenance_ref,
            responsibility_ref=responsibility_ref,
            parent_outcome_id=parent_outcome_id,
        )
        self.outcomes[outcome_id] = outcome
        self.population_review_valid = False
        self.population_comparison_ref = None
        return outcome

    def get(self, outcome_id: str) -> CheckpointOutcome:
        return self.outcomes[outcome_id]

    def record_technical_state(
        self,
        *,
        outcome_id: str,
        technical_state: str,
    ) -> None:
        self.get(outcome_id).technical_state = technical_state

    def transfer_responsibility(
        self,
        *,
        outcome_id: str,
        responsibility_ref: str,
    ) -> CheckpointOutcome:
        if not responsibility_ref:
            raise ValueError("responsibility_ref is required")

        outcome = self.get(outcome_id)
        outcome.responsibility_ref = responsibility_ref
        return outcome

    def resolve(
        self,
        *,
        outcome_id: str,
        resolution_basis: str,
    ) -> CheckpointOutcome:
        if not resolution_basis:
            raise ValueError("resolution_basis is required")

        outcome = self.get(outcome_id)
        outcome.resolution_basis = resolution_basis
        outcome.resolution_valid = True
        outcome.invalidity_basis = None
        outcome.status = RESOLVED
        return outcome

    def invalidate_resolution(
        self,
        *,
        outcome_id: str,
        invalidity_basis: str,
    ) -> CheckpointOutcome:
        if not invalidity_basis:
            raise ValueError("invalidity_basis is required")

        outcome = self.get(outcome_id)
        if outcome.status != RESOLVED or not outcome.resolution_basis:
            raise ValueError("only a resolved outcome can be invalidated")

        outcome.resolution_valid = False
        outcome.invalidity_basis = invalidity_basis
        return outcome

    def review_current_population(
        self,
        *,
        comparison_ref: str,
    ) -> None:
        if not comparison_ref:
            raise ValueError("comparison_ref is required")

        self.population_comparison_ref = comparison_ref
        self.population_review_valid = True

    def can_complete_checkpoint(self) -> bool:
        return (
            self.population_review_valid
            and all(
                outcome.status == RESOLVED and outcome.resolution_valid
                for outcome in self.outcomes.values()
            )
        )
