"""RED contract tests for Documentation Checkpoint continuous accountability."""

import importlib


def _load_contract():
    """
    The production module intentionally does not exist before GREEN.

    RED defines the minimum approved accounting boundary without introducing
    another Gate, obligation register, workflow engine, or authority.
    """
    return importlib.import_module("modules.documentation_checkpoint_accountability")


def test_known_material_outcome_enters_checkpoint_accounting_as_pending():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    outcome = collection.get("OUTCOME-1")

    assert outcome.outcome_id == "OUTCOME-1"
    assert outcome.status == "PENDING"


def test_repeated_intake_preserves_same_outcome_identity():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")

    first = collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )
    second = collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    assert first is second
    assert len(collection.outcomes) == 1


def test_technical_completion_does_not_auto_resolve_checkpoint_accounting():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    collection.record_technical_state(
        outcome_id="OUTCOME-1",
        technical_state="VALIDATED",
    )

    assert collection.get("OUTCOME-1").status == "PENDING"


def test_checkpoint_completion_is_blocked_while_registered_pending_exists():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    assert collection.can_complete_checkpoint() is False


def test_resolution_requires_explicit_resolution_basis():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    try:
        collection.resolve(outcome_id="OUTCOME-1")
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("resolution without basis must fail")

    assert collection.get("OUTCOME-1").status == "PENDING"


def test_resolution_with_basis_marks_registered_outcome_resolved():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    collection.resolve(
        outcome_id="OUTCOME-1",
        resolution_basis="documentation-checkpoint#validated-disposition",
    )

    outcome = collection.get("OUTCOME-1")
    assert outcome.status == "RESOLVED"
    assert outcome.resolution_basis == (
        "documentation-checkpoint#validated-disposition"
    )


def test_later_material_development_creates_new_linked_pending_outcome():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    original = collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )
    collection.resolve(
        outcome_id="OUTCOME-1",
        resolution_basis="documentation-checkpoint#validated-disposition",
    )

    later = collection.intake(
        outcome_id="OUTCOME-2",
        provenance_ref="chronicle#later-development",
        responsibility_ref="R&D 002",
        parent_outcome_id="OUTCOME-1",
    )

    assert original.status == "RESOLVED"
    assert later.status == "PENDING"
    assert later.parent_outcome_id == "OUTCOME-1"
    assert len(collection.outcomes) == 2


def test_handoff_preserves_pending_identity_and_transfers_responsibility():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    original = collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    transferred = collection.transfer_responsibility(
        outcome_id="OUTCOME-1",
        responsibility_ref="R&D 003",
    )

    assert transferred is original
    assert transferred.outcome_id == "OUTCOME-1"
    assert transferred.status == "PENDING"
    assert transferred.responsibility_ref == "R&D 003"
    assert len(collection.outcomes) == 1


def test_linked_material_development_requires_existing_parent():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")

    try:
        collection.intake(
            outcome_id="OUTCOME-2",
            provenance_ref="chronicle#later-development",
            responsibility_ref="R&D 002",
            parent_outcome_id="MISSING",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("missing parent must fail closed")

    assert len(collection.outcomes) == 0


def test_repeated_identity_with_conflicting_provenance_fails_closed():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    try:
        collection.intake(
            outcome_id="OUTCOME-1",
            provenance_ref="chronicle#different-event",
            responsibility_ref="R&D 002",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("conflicting identity provenance must fail closed")

    outcome = collection.get("OUTCOME-1")
    assert outcome.provenance_ref == "chronicle#decision"
    assert len(collection.outcomes) == 1


def test_invalid_resolution_preserves_history_but_blocks_completion():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    outcome = collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    collection.resolve(
        outcome_id="OUTCOME-1",
        resolution_basis="documentation-checkpoint#original-resolution",
    )
    collection.invalidate_resolution(
        outcome_id="OUTCOME-1",
        invalidity_basis="traceability#resolution-proof-invalid",
    )

    assert outcome.status == "RESOLVED"
    assert outcome.resolution_basis == (
        "documentation-checkpoint#original-resolution"
    )
    assert outcome.resolution_valid is False
    assert outcome.invalidity_basis == "traceability#resolution-proof-invalid"
    assert collection.can_complete_checkpoint() is False


def test_valid_resolution_remains_eligible_for_checkpoint_completion():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    outcome = collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    collection.resolve(
        outcome_id="OUTCOME-1",
        resolution_basis="documentation-checkpoint#validated-disposition",
    )

    assert outcome.status == "RESOLVED"
    assert outcome.resolution_valid is True

    collection.review_current_population(
        comparison_ref="chronicle#reviewed-version-1",
    )

    assert collection.can_complete_checkpoint() is True


def test_invalidating_unresolved_outcome_fails_closed():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    outcome = collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )

    try:
        collection.invalidate_resolution(
            outcome_id="OUTCOME-1",
            invalidity_basis="traceability#invalid",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unresolved outcome cannot have resolution invalidated")

    assert outcome.status == "PENDING"


def test_checkpoint_completion_requires_current_population_review():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )
    collection.resolve(
        outcome_id="OUTCOME-1",
        resolution_basis="documentation-checkpoint#validated-disposition",
    )

    assert collection.can_complete_checkpoint() is False

    collection.review_current_population(
        comparison_ref="chronicle#reviewed-version-1",
    )

    assert collection.can_complete_checkpoint() is True


def test_new_outcome_after_population_review_invalidates_previous_review():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")
    collection.intake(
        outcome_id="OUTCOME-1",
        provenance_ref="chronicle#decision",
        responsibility_ref="R&D 002",
    )
    collection.resolve(
        outcome_id="OUTCOME-1",
        resolution_basis="documentation-checkpoint#validated-disposition",
    )
    collection.review_current_population(
        comparison_ref="chronicle#reviewed-version-1",
    )

    assert collection.can_complete_checkpoint() is True

    collection.intake(
        outcome_id="OUTCOME-2",
        provenance_ref="chronicle#later-material-development",
        responsibility_ref="R&D 002",
        parent_outcome_id="OUTCOME-1",
    )

    assert collection.can_complete_checkpoint() is False


def test_population_review_requires_comparison_reference():
    contract = _load_contract()

    collection = contract.SprintCheckpointCollection(sprint_id="R&D 002")

    try:
        collection.review_current_population(comparison_ref="")
    except ValueError:
        pass
    else:
        raise AssertionError("population review without comparison_ref must fail")

    assert collection.population_review_valid is False
