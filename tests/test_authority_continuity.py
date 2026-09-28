"""RED-U..Y and continuity: same-station routing in existing natural homes."""

from copy import deepcopy
from hashlib import sha256
import posixpath

import pytest

from tools.resolve_authority import Resolver

from tests.test_support.design_c_fixture import CHRONICLE, REGISTER, TRACE, case, rejected


def _traceability_artifact_case(case):
    """Reproduce heading reference -> explicit durable-copy links + hashes."""
    paths = ("docs/artifacts/sample-a.xml", "docs/artifacts/sample-b.xml")
    unrelated = "docs/artifacts/sample-c.xml"
    for path in (*paths, unrelated):
        case.write(path, "TEST ONLY retained artifact: " + path + "\n")
    case.satisfy_all()
    case.outcome(
        "PROOF_EVIDENCE", classification="CLASSIFIED_AND_PERSISTED",
        obligation_ref="O21", evidence_ref="E-O21",
        traceability_ref=f"{TRACE}#Synthetic retained event",
    )
    case.transition("PRE_COMMIT")
    case.request["paths"] = list(paths)
    return paths, unrelated


def _resolve_traceability_artifact_case(case, paths, unrelated):
    # flush first: the shared fixture otherwise overwrites appended Markdown.
    case.flush()
    trace = case.root / TRACE
    text = trace.read_text(encoding="utf-8")
    for heading, artifacts in (
        ("Synthetic retained event", paths),
        ("Separate unrelated event", (unrelated,)),
    ):
        text += f"\n### {heading}\n\nDurable copies:\n"
        for path in artifacts:
            target = posixpath.relpath(path, posixpath.dirname(TRACE))
            digest = sha256((case.root / path).read_bytes()).hexdigest()
            text += f"- [Retained artifact]({target});\n  SHA256 {digest}.\n"
    case.write(TRACE, text)
    resolver = Resolver(case.root, case.request, case.baseline, case.baseline_digest)
    return resolver, resolver.resolve()


def test_traceability_consumption_classifies_two_explicit_artifacts(case):
    paths, unrelated = _traceability_artifact_case(case)
    _, report = _resolve_traceability_artifact_case(case, paths, unrelated)
    missing = {d["subject"] for d in report["diagnostics"]
               if d["code"] == "UNCLASSIFIED_CHANGE"}
    assert not missing.intersection(paths), (
        "Referenced Traceability record's two explicit artifacts were not consumed",
        report["diagnostics"],
    )
    assert report["diagnostics"] == []
    assert report["status"] == "TRANSITION_ALLOWED"


def test_traceability_consumption_does_not_scan_unrelated_record(case):
    paths, unrelated = _traceability_artifact_case(case)
    case.request["paths"].append(unrelated)
    _, report = _resolve_traceability_artifact_case(case, paths, unrelated)
    rejected(report, "UNCLASSIFIED_CHANGE", unrelated)
    assert all(d["code"] == "UNCLASSIFIED_CHANGE" for d in report["diagnostics"])
    assert report["status"] == "TRANSITION_BLOCKED"


def test_traceability_consumption_has_no_evidentiary_power(case):
    paths, unrelated = _traceability_artifact_case(case)
    case.transition("PRE_CANARY")
    case.evidence["evidence"] = [e for e in case.evidence["evidence"]
                                 if e["id"] != "E-O22"]
    case.obligation("O22")["evidence_refs"] = [paths[0]]
    before_evidence = deepcopy(case.evidence)
    before_obligations = deepcopy(case.obligations)
    before_outcomes = deepcopy(case.station["material_outcomes"])
    resolver, report = _resolve_traceability_artifact_case(case, paths, unrelated)
    rejected(report, "EVIDENCE_INVALID", "O22")
    rejected(report, "OBLIGATION_DUE", "O22")
    assert report["status"] == "TRANSITION_BLOCKED"
    assert "closure_pass" not in report
    assert report["material_outcomes"] == before_outcomes
    assert report["obligations"] == before_obligations["obligations"]
    assert list(resolver.evidence.values()) == before_evidence["evidence"]
    assert case.evidence == before_evidence
    assert case.obligations == before_obligations
    assert {d["code"] for d in report["diagnostics"]} <= {
        "EVIDENCE_INVALID", "OBLIGATION_DUE", "UNCLASSIFIED_CHANGE",
    }


def test_register_next_conflicts_with_active_durable_station(case):
    case.write(REGISTER, "# R&D Register\n\nR&D 002 | NEXT — NOT OPEN\n")
    rejected(case.run(), "CONTINUITY_CONFLICT")


def test_pause_reconstructs_exact_station_without_chat(case):
    case.request["task"] = "הפסקה"
    report = case.run()
    assert report["status"] == "RESOLVED_CONTEXT"
    assert report["station"]["station"] == "FOUNDATION_RED"
    assert report["station"]["objective_ref"] == f"{CHRONICLE}#objective"
    assert report["station"]["next_action"] == "REVIEW_RED"
    assert report["station"]["alignment"] == "VERIFIED"
    assert "approval_refs" in report["station"]
    assert "restriction_refs" in report["station"]


def test_missing_station_is_not_reconstructed_from_model_guess(case):
    case.request["station_ref"] = "docs/missing-station.md"
    rejected(case.run(), "STATION_MISSING")


def test_red_u_approved_material_decision_requires_same_station_authority(case):
    case.approve("DECISION_CHANGE")
    case.outcome("AUTHORITATIVE_DECISION", approval_ref="TEST-PO-ACTION",
                 authority_ref="docs/missing-new-decision.md#decision",
                 classification="CLASSIFIED_AND_PERSISTED")
    case.transition("STATION_COMPLETE")
    rejected(case.run(), "PERSISTENCE_MISSING", "M1")


def test_red_v_carried_followup_requires_durable_obligation(case):
    case.outcome("CARRIED_FOLLOW_UP", classification="CLASSIFIED_AND_PERSISTED",
                 obligation_ref="O-NEW-MISSING", required_before=["PRE_CANARY"])
    case.transition("STATION_COMPLETE")
    rejected(case.run(), "OBLIGATION_COVERAGE", "M1")


def test_red_w_produced_proof_unlinked_from_obligation_does_not_satisfy_it(case):
    case.satisfy_all()
    case.obligation("O21").update(status="OPEN", evidence_refs=[])
    case.outcome("PROOF_EVIDENCE", classification="CLASSIFIED_AND_PERSISTED",
                 evidence_ref="E-O21", obligation_ref="O21", traceability_ref=TRACE)
    case.transition()
    rejected(case.run(), "EVIDENCE_NOT_LINKED", "M1")


def test_red_x_genuine_no_material_outcome_does_not_force_new_record(case):
    case.request.update(mode="transition", action="STATION_COMPLETE")
    report = case.run()
    assert report["status"] == "TRANSITION_ALLOWED"
    assert report["material_outcomes"] == []
    assert report["station"]["outcome_classification"] == "NO_MATERIAL_OUTCOME"


def test_red_y_new_agent_recovers_persisted_outcomes_and_carried_work(case):
    case.outcome("CARRIED_FOLLOW_UP", classification="CLASSIFIED_AND_PERSISTED",
                 obligation_ref="O21", required_before=["PRE_CANARY"])
    first = case.run()
    second = case.run()
    assert first["status"] == second["status"] == "RESOLVED_CONTEXT"
    assert second["material_outcomes"][0]["obligation_ref"] == "O21"
    assert first["material_outcomes"] == second["material_outcomes"]
    case.transition()
    rejected(case.run(), "OBLIGATION_DUE", "O21")


def test_known_unresolved_classification_blocks_station_completion(case):
    case.outcome("GOVERNANCE_GAP")
    case.transition("STATION_COMPLETE")
    rejected(case.run(), "UNRESOLVED_CLASSIFICATION", "M1")


def test_no_outcome_claim_cannot_hide_observed_authority_change(case):
    case.write("docs/new-authoritative-decision.md", "# Material decision\nApproved change.\n")
    case.request["observed_changes"] = ["docs/new-authoritative-decision.md"]
    case.transition("STATION_COMPLETE")
    rejected(case.run(), "UNCLASSIFIED_CHANGE")


@pytest.mark.parametrize("kind", ["APPROVAL_RESTRICTION", "SCOPE_CHANGE", "CONTRADICTION", "STATION_CHANGE"])
def test_known_material_outcome_cannot_be_lost_on_transition(case, kind):
    case.outcome(kind)
    case.transition("STATION_COMPLETE")
    rejected(case.run(), "UNRESOLVED_CLASSIFICATION", "M1")


def test_historical_disposition_explicit_path_classifies_persistence(case):
    path = "docs/audit/retained-output.txt"
    case.write(path, "Retained output; provenance unresolved.\n")
    case.station["artifact_dispositions"] = {
        path: "HISTORICAL_PROVENANCE_UNRESOLVED",
    }
    case.request["paths"] = [path]
    case.satisfy_all()
    case.transition("PRE_COMMIT")

    report = case.run()

    assert report["diagnostics"] == [], report["diagnostics"]
    assert report["status"] == "TRANSITION_ALLOWED"
    assert report["material_outcomes"] == []


def test_historical_disposition_has_no_evidentiary_power(case):
    path = "docs/audit/retained-output.txt"
    case.write(path, "Retained output; provenance unresolved.\n")
    case.station["artifact_dispositions"] = {
        path: "HISTORICAL_PROVENANCE_UNRESOLVED",
    }
    case.request["paths"] = [path]
    case.satisfy_all()
    # Remove the actual prerequisite receipt. Neither declaring a historical
    # artifact nor listing its path as evidence may replace that receipt.
    case.evidence["evidence"] = [
        e for e in case.evidence["evidence"] if e["id"] != "E-O21"
    ]
    case.obligation("O21").update(evidence_refs=[path])
    case.transition("PRE_CANARY")

    report = case.run()

    rejected(report, "EVIDENCE_INVALID", "O21")
    rejected(report, "OBLIGATION_DUE", "O21")
    assert report["material_outcomes"] == []
    assert all(e["id"] != path for e in case.evidence["evidence"])
    assert {d["code"] for d in report["diagnostics"]} <= {
        "EVIDENCE_INVALID", "OBLIGATION_DUE", "UNCLASSIFIED_CHANGE",
    }


def test_historical_disposition_unlisted_path_remains_fail_closed(case):
    retained = "docs/audit/retained-output.txt"
    unlisted = "docs/audit/unlisted-output.txt"
    case.write(retained, "Retained output; provenance unresolved.\n")
    case.write(unlisted, "No disposition or material outcome.\n")
    case.station["artifact_dispositions"] = {
        retained: "HISTORICAL_PROVENANCE_UNRESOLVED",
    }
    case.request["paths"] = [unlisted]
    case.satisfy_all()
    case.transition("PRE_COMMIT")

    report = case.run()

    rejected(report, "UNCLASSIFIED_CHANGE", unlisted)
    assert report["diagnostics"] == [
        {"code": "UNCLASSIFIED_CHANGE", "subject": unlisted},
    ]


def test_proven_historical_disposition_classifies_exact_path(case):
    path = "docs/audit/retained-version.txt"
    case.write(path, "TEST ONLY proven historical version; no active persistence.\n")
    case.station["artifact_dispositions"] = {
        path: "HISTORICAL_PROVENANCE_PROVEN_NOT_ACTIVE_PERSISTENCE",
    }
    case.request["paths"] = [path]
    case.satisfy_all()
    case.transition("PRE_COMMIT")

    report = case.run()

    assert report["diagnostics"] == [], report["diagnostics"]
    assert report["status"] == "TRANSITION_ALLOWED"
    assert report["material_outcomes"] == []


def test_proven_historical_disposition_unlisted_path_stays_unclassified(case):
    retained = "docs/audit/retained-version.txt"
    unlisted = "docs/audit/retained-version-other.txt"
    for path in (retained, unlisted):
        case.write(path, "TEST ONLY historical output.\n")
    case.station["artifact_dispositions"] = {
        retained: "HISTORICAL_PROVENANCE_PROVEN_NOT_ACTIVE_PERSISTENCE",
    }
    case.request["paths"] = [unlisted]
    case.satisfy_all()
    case.transition("PRE_COMMIT")

    report = case.run()

    assert report["diagnostics"] == [
        {"code": "UNCLASSIFIED_CHANGE", "subject": unlisted},
    ]
    assert report["status"] == "TRANSITION_BLOCKED"


def test_proven_historical_disposition_has_no_active_evidentiary_power(case):
    path = "docs/audit/retained-version.txt"
    case.write(path, "TEST ONLY proven history; not active evidence.\n")
    case.station["artifact_dispositions"] = {
        path: "HISTORICAL_PROVENANCE_PROVEN_NOT_ACTIVE_PERSISTENCE",
    }
    case.request["paths"] = [path]
    case.satisfy_all()
    case.evidence["evidence"] = [
        e for e in case.evidence["evidence"] if e["id"] != "E-O21"
    ]
    case.obligation("O21")["evidence_refs"] = [path]
    case.transition("PRE_CANARY")
    before_evidence = deepcopy(case.evidence)
    before_obligations = deepcopy(case.obligations)
    before_station = deepcopy(case.station)

    report = case.run()

    rejected(report, "EVIDENCE_INVALID", "O21")
    rejected(report, "OBLIGATION_DUE", "O21")
    assert report["status"] == "TRANSITION_BLOCKED"
    assert "closure_pass" not in report
    assert report["material_outcomes"] == []
    assert report["obligations"] == before_obligations["obligations"]
    assert case.evidence == before_evidence
    assert case.station == before_station
    assert {d["code"] for d in report["diagnostics"]} <= {
        "EVIDENCE_INVALID", "OBLIGATION_DUE", "UNCLASSIFIED_CHANGE",
    }


def test_checkpoint_accounting_survives_station_state_replacement(case):
    """Canonical checkpoint accounting is Chronicle-level, not station-state-owned."""
    case.checkpoint_outcome(
        outcome_id="KMO-1",
        provenance_ref=f"{CHRONICLE}#material-development",
        responsibility_ref="R&D 002",
        status="PENDING",
    )

    first = case.run()

    # Replace station-local state as a later station would.
    case.station["station"] = "NEXT_STATION"
    case.station["next_action"] = "NEXT_ACTION"
    case.station["material_outcomes"] = []
    case.station["outcome_classification"] = "NO_MATERIAL_OUTCOME"

    second = case.run()

    assert first["checkpoint_outcomes"] == second["checkpoint_outcomes"]
    assert second["checkpoint_outcomes"][0]["outcome_id"] == "KMO-1"
    assert second["checkpoint_outcomes"][0]["status"] == "PENDING"
    assert second["material_outcomes"] == []
