"""RED-A through RED-T: obligations at their approved consequence boundaries."""

import pytest

from tests.test_support.design_c_fixture import OBLIGATION_IDS, case, rejected


@pytest.mark.parametrize("oid,boundary", [
    ("O21", "PRE_CANARY"), ("O22", "PRE_CANARY"), ("O26", "PRE_CANARY"),
    ("O28", "PRE_EXTERNAL_WORK"), ("C2", "PRE_CANARY"), ("X1", "PRE_CANARY"),
    ("X2", "PRE_PUSH_OR_PROMOTION"), ("X3", "PRE_CLOSURE"),
])
def test_red_a_h_i_j_each_required_open_obligation_blocks(case, oid, boundary):
    case.satisfy_all()
    case.obligation(oid).update(status="OPEN", evidence_refs=[])
    case.transition(boundary)
    rejected(case.run(), "OBLIGATION_DUE", oid)


def test_red_b_raw_closed_edit_without_proof_is_not_closure(case):
    case.satisfy_all()
    case.obligation("O21")["evidence_refs"] = []
    case.transition()
    rejected(case.run(), "EVIDENCE_MISSING", "O21")


def test_red_c_delete_required_obligation_fails_reverse_coverage(case):
    case.obligations["obligations"] = [o for o in case.obligations["obligations"]
                                          if o["obligation_id"] != "O21"]
    rejected(case.run(), "OBLIGATION_COVERAGE")


@pytest.mark.parametrize("remove_authority", [False, True])
def test_red_d_delete_both_sides_is_detected_from_baseline(case, remove_authority):
    authority = case.binding("B-O21")["authority"]["path"]
    case.bindings["bindings"] = [b for b in case.bindings["bindings"] if b["id"] != "B-O21"]
    case.obligations["obligations"] = [o for o in case.obligations["obligations"]
                                          if o["obligation_id"] != "O21"]
    if remove_authority:
        (case.root / authority).unlink()
    rejected(case.run(), "BASELINE_COVERAGE")


@pytest.mark.parametrize("mutation", ["level", "scope", "sha", "assertion", "receipt", "bytes", "missing_file"])
def test_red_e_invalid_evidence_cannot_satisfy_obligation(case, mutation):
    case.satisfy_all()
    evidence = next(e for e in case.evidence["evidence"] if e["obligation_id"] == "X3")
    if mutation == "level":
        evidence["proof_class"] = "LEVEL_1"
    elif mutation == "scope":
        evidence["scope"] = "different-unit"
    elif mutation == "sha":
        evidence["candidate_sha"] = "b" * 40
    elif mutation == "assertion":
        evidence["assertions"] = []
    elif mutation == "receipt":
        evidence.pop("validation")
    elif mutation == "bytes":
        case.write(evidence["path"], "tampered evidence")
    else:
        (case.root / evidence["path"]).unlink()
    case.transition("PRE_CLOSURE")
    rejected(case.run(), "EVIDENCE_INVALID", "X3")


def test_red_f_new_process_reconstructs_same_block_without_chat(case):
    case.transition()
    first = case.run()
    second = case.run()  # Separate subprocess, no in-memory SUT state or chat.
    rejected(first, "OBLIGATION_DUE", "O21")
    rejected(second, "OBLIGATION_DUE", "O21")
    assert first["obligations"] == second["obligations"]


def test_red_g_future_canary_obligations_allow_local_wds_diagnosis(case):
    case.request["mode"] = "transition"
    report = case.run()
    assert report["status"] == "TRANSITION_ALLOWED"
    assert {o["obligation_id"] for o in report["obligations"] if o["status"] == "OPEN"} >= set(OBLIGATION_IDS)


@pytest.mark.parametrize("mutation", ["unapproved", "circular", "wrong_scope"])
def test_red_k_supersession_and_cancellation_cannot_hide_obligations(case, mutation):
    obligation = case.obligation("O21")
    obligation.update(status="SUPERSEDED", disposition_ref="D1")
    disposition = {"id": "D1", "kind": "SUPERSESSION", "from": "O21", "to": "O22",
                   "scope": "R&D 002", "approval_ref": "MISSING"}
    case.evidence["dispositions"].append(disposition)
    if mutation != "unapproved":
        case.approve("SUPERSESSION")
        disposition["approval_ref"] = "TEST-PO-ACTION"
    if mutation == "circular":
        case.obligation("O22").update(status="SUPERSEDED", disposition_ref="D2")
        case.evidence["dispositions"].append({**disposition, "id": "D2", "from": "O22", "to": "O21"})
    if mutation == "wrong_scope":
        obligation["status"] = "NOT_APPLICABLE"
        disposition.update(kind="SCOPE_CHANGE", scope="unrelated-unit")
    rejected(case.run(), "DISPOSITION_INVALID")


def test_red_l_stale_station_snapshot_does_not_hide_register(case):
    case.station["obligation_snapshot"] = {"open_ids": [], "register_digest": "stale"}
    case.transition()
    rejected(case.run(), "STATION_DRIFT")


def test_red_m_direct_production_does_not_skip_canary_prerequisites(case):
    case.transition("PRE_PRODUCTION")
    rejected(case.run(), "OBLIGATION_DUE", "O21")


def test_red_n_prior_action_evidence_does_not_authorize_new_action(case):
    case.satisfy_all()
    case.transition("PRE_PUSH_OR_PROMOTION")
    case.request["action_id"] = "test-action-2"
    case.evidence["approvals"][0]["action_id"] = "test-action-2"
    rejected(case.run(), "EVIDENCE_INVALID", "X2")


def test_unconsumed_closed_fresh_evidence_is_not_rebound_to_unrelated_action(case):
    case.satisfy_all()
    case.transition("PRE_EXTERNAL_WORK")

    historical = next(
        obligation for obligation in case.obligations["obligations"]
        if obligation["required_before"] == ["PRE_CLOSURE"]
    )
    historical_evidence_ref = historical["evidence_refs"][0]
    case.request["action_id"] = "unrelated-external-work"
    case.evidence["approvals"][0]["action_id"] = "unrelated-external-work"
    for evidence in case.evidence["evidence"]:
        if evidence["id"] != historical_evidence_ref:
            evidence["action_id"] = "unrelated-external-work"

    report = case.run()

    assert report["status"] == "TRANSITION_ALLOWED", report["diagnostics"]


def test_red_p_new_applicable_binding_requires_followup_obligation(case):
    from copy import deepcopy

    binding = deepcopy(case.binding("B-O21"))
    binding["id"] = "B-NEW"
    binding["obligations"][0]["id"] = "proof-NEW"
    case.bindings["bindings"].append(binding)
    rejected(case.run(), "OBLIGATION_COVERAGE")


def test_red_q_orphaned_obligation_fails(case):
    case.obligation("O21")["binding_ref"] = "NONEXISTENT"
    rejected(case.run(), "ORPHANED_OBLIGATION", "O21")


def test_red_s_valid_proof_and_approval_allow_transition_not_closure(case):
    case.satisfy_all()
    case.transition("PRE_CLOSURE")
    report = case.run()
    assert report["status"] == "TRANSITION_ALLOWED"
    assert all(o["status"] == "CLOSED" for o in report["obligations"])


def test_red_t_prior_allowed_snapshot_cannot_be_reused_after_change(case):
    case.satisfy_all()
    case.transition()
    first = case.run()
    assert first["status"] == "TRANSITION_ALLOWED"
    case.request["expected_snapshot"] = first["snapshot"]
    case.obligation("O21").update(status="OPEN", evidence_refs=[])
    rejected(case.run(), "SNAPSHOT_CHANGED")


@pytest.mark.parametrize("action", ["PRE_COMMIT", "PRE_PUSH_OR_PROMOTION", "PRE_CANARY", "PRE_PRODUCTION"])
def test_po_gated_action_is_not_authorized_by_resolved_context(case, action):
    case.satisfy_all()
    case.request.update(mode="transition", action=action)
    rejected(case.run(), "APPROVAL_REQUIRED")


def test_agent_self_authored_approval_is_not_po_authority(case):
    case.satisfy_all()
    case.transition()
    case.evidence["approvals"][0]["issuer"] = "EXECUTION_AGENT"
    rejected(case.run(), "APPROVAL_INVALID")


def test_foundation_cannot_declare_itself_green_with_open_self_obligation(case):
    case.binding("B-O21")["obligations"][0]["required_before"] = ["FOUNDATION_GREEN"]
    case.obligation("O21")["required_before"] = ["FOUNDATION_GREEN"]
    case.pin_baseline()  # Independent synthetic approved self-application scenario.
    case.transition("FOUNDATION_GREEN")
    rejected(case.run(), "OBLIGATION_DUE", "O21")


# PO-approved independent candidate/action policy; synthetic inputs only.
def _candidate_policy_case(tmp_path, *, fresh=False, **policy):
    from tests.test_support.design_c_fixture import RepositoryCase, digest

    oid = "SYNTHETIC-PROOF"
    case = RepositoryCase(tmp_path, obligation_ids=(oid,))
    requirement = case.binding(f"B-{oid}")["obligations"][0]
    requirement.update(fresh_for_action=fresh, **policy)
    # Establish this synthetic policy before evidence or evaluation, without
    # changing the repository's approved baseline or historical records.
    case.pin_baseline()
    case.satisfy(oid)
    subject = "modules/sec_company_identity_resolver.py"
    body = "# unchanged synthetic governed subject\n"
    case.write(subject, body)
    case.evidence["evidence"][0]["subject_hashes"] = {subject: digest(body)}
    case.transition("PRE_CANARY")
    return case, oid, subject


def test_candidate_policy_independent_of_action_freshness(tmp_path):
    case, oid, _ = _candidate_policy_case(
        tmp_path, candidate_match_required=True,
    )
    case.request["action_id"] = "new-consuming-action"
    case.evidence["approvals"][0]["action_id"] = "new-consuming-action"
    historical = dict(case.evidence["evidence"][0])
    same_candidate = case.run()
    assert same_candidate["status"] == "TRANSITION_ALLOWED", same_candidate["diagnostics"]
    assert same_candidate["diagnostics"] == []

    # Only candidate applicability changes; current authorization stays valid.
    case.request["candidate_sha"] = "b" * 40
    case.evidence["approvals"][0]["candidate_sha"] = "b" * 40
    different_candidate = case.run()
    assert case.evidence["evidence"][0] == historical
    assert different_candidate["status"] == "TRANSITION_BLOCKED", (
        "Independent candidate policy must reject mismatched candidate even "
        "without action freshness", different_candidate["diagnostics"]
    )
    rejected(different_candidate, "EVIDENCE_INVALID", oid)


def test_candidate_policy_preserves_explicit_action_freshness(tmp_path):
    case, oid, _ = _candidate_policy_case(
        tmp_path, fresh=True, candidate_match_required=False,
    )
    assert case.run()["status"] == "TRANSITION_ALLOWED"
    case.request["action_id"] = "new-consuming-action"
    case.evidence["approvals"][0]["action_id"] = "new-consuming-action"
    rejected(case.run(), "EVIDENCE_INVALID", oid)


@pytest.mark.parametrize("fresh", [False, True])
@pytest.mark.parametrize("dimension", ["none", "candidate_sha", "action_id"])
def test_candidate_policy_absent_field_preserves_legacy(tmp_path, fresh, dimension):
    case, oid, _ = _candidate_policy_case(tmp_path, fresh=fresh)
    assert "candidate_match_required" not in case.binding(f"B-{oid}")["obligations"][0]
    if dimension != "none":
        value = "b" * 40 if dimension == "candidate_sha" else "new-consuming-action"
        case.request[dimension] = value
        case.evidence["approvals"][0][dimension] = value
    report = case.run()
    if fresh and dimension != "none":
        rejected(report, "EVIDENCE_INVALID", oid)
    else:
        assert report["status"] == "TRANSITION_ALLOWED", report["diagnostics"]
        assert report["diagnostics"] == []


@pytest.mark.parametrize("value", [None, "false", 0, 1])
def test_candidate_policy_non_boolean_fails_closed(tmp_path, value):
    case, _, _ = _candidate_policy_case(tmp_path, candidate_match_required=value)
    rejected(case.run(), "INVALID_SCHEMA")


@pytest.mark.parametrize("fault", ["wrong_obligation", "changed_subject", "old_approval"])
def test_candidate_policy_preserves_context_subject_and_authorization(tmp_path, fault):
    case, oid, subject = _candidate_policy_case(tmp_path, candidate_match_required=True)
    assert case.run()["status"] == "TRANSITION_ALLOWED"
    if fault == "wrong_obligation":
        case.evidence["evidence"][0]["obligation_id"] = "UNRELATED-PROOF"
    elif fault == "changed_subject":
        case.write(subject, "# changed governed subject\n")
    else:
        case.request["action_id"] = "new-consuming-action"
    report = case.run()
    if fault == "old_approval":
        rejected(report, "APPROVAL_INVALID")
    else:
        rejected(report, "EVIDENCE_INVALID", oid)
