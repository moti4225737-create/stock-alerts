"""Prevent mutating the meaning of a pinned obligation to evade a boundary."""
import pytest
from copy import deepcopy
from hashlib import sha256
import json

from tests.test_support.design_c_fixture import case, rejected


def _seal(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode()).hexdigest()


def _evolved(case):
    """Approved synthetic material transition; no real records or approvals."""
    old = case.binding("B-O21")
    old["obligations"][0]["fresh_for_action"] = True
    case.pin_baseline()
    case.satisfy("O21")
    successor = deepcopy(old)
    successor["id"] = "B-REUSABLE"
    successor["obligations"][0]["fresh_for_action"] = False
    successor["obligations"][0]["candidate_match_required"] = False
    case.bindings["bindings"].append(successor)
    obligation = deepcopy(case.obligation("O21"))
    obligation.update(obligation_id="REUSABLE", binding_ref="B-REUSABLE")
    case.obligations["obligations"].append(obligation)

    def contract(binding):
        value = deepcopy(binding)
        value["authority"].pop("digest")
        for r in value["obligations"]:
            r.setdefault("candidate_match_required", r.get("fresh_for_action"))
        return value

    def obligation_contract(o):
        return {k: v for k, v in o.items()
                if k not in {"status", "evidence_refs", "disposition_ref"}}

    d = {"id": "EVOLUTION", "kind": "SUPERSESSION", "from": "B-O21",
         "to": "B-REUSABLE", "scope": "R&D 002",
         "authority_ref": old["authority"]["path"],
         "approval_ref": "TEST-PO-ACTION", "evolution": {
             "contracts": {"B-O21": _seal(contract(old)),
                           "B-REUSABLE": _seal(contract(successor))},
             "consumers": {"B-O21": ["ClinicalTrials.gov", "FDA", "SEC"],
                           "B-REUSABLE": ["ClinicalTrials.gov", "FDA", "SEC"]},
             "obligations": [{"from": "O21", "to": "REUSABLE",
                 "contracts": {"O21": _seal(obligation_contract(case.obligation("O21"))),
                               "REUSABLE": _seal(obligation_contract(obligation))},
                 "historical_status": "CLOSED", "historical_evidence_refs": ["E-O21"],
                 "evidence_policy": "REUSABLE", "reason": "Unchanged proven subjects; identity is not proof freshness.",
                 "reusable_evidence": {"E-O21": _seal(case.evidence["evidence"][0])}}]}}
    case.approve("SUPERSESSION")
    case.evidence["approvals"][-1]["disposition_sha256"] = _seal(d)
    case.evidence["dispositions"].append(d)
    old["supersession_ref"] = "EVOLUTION"
    case.obligation("O21").update(status="SUPERSEDED", disposition_ref="EVOLUTION")
    return d


def test_evolution_durable_relation_does_not_authorize_current_action(case):
    _evolved(case)
    historical = deepcopy(case.evidence["evidence"])
    case.request.update(action_id="later-action", candidate_sha="b" * 40)
    case.station["approval_refs"] = []
    report = case.run()
    assert report["status"] == "RESOLVED_CONTEXT", report["diagnostics"]
    assert "B-REUSABLE" in {c["id"] for c in report["controls"]}
    assert "B-O21" not in {c["id"] for c in report["controls"]}
    case.request.update(mode="transition", action="PRE_COMMIT")
    rejected(case.run(), "APPROVAL_REQUIRED")
    assert case.evidence["evidence"] == historical


def test_evolution_can_evolve_again_without_rewriting_first_contract(case):
    first = _evolved(case)
    historical = deepcopy(first)
    current = case.binding("B-REUSABLE")
    latest = deepcopy(current)
    latest["id"] = "B-LATEST"
    case.bindings["bindings"].append(latest)
    latest_contract = deepcopy(latest)
    latest_contract["authority"].pop("digest")
    current_obligation = case.obligation("REUSABLE")
    latest_obligation = deepcopy(current_obligation)
    latest_obligation.update(obligation_id="LATEST", binding_ref="B-LATEST")
    case.obligations["obligations"].append(latest_obligation)
    latest_obligation_contract = {k: v for k, v in latest_obligation.items()
                                  if k not in {"status", "evidence_refs"}}
    case.bindings["components"]["observation"]["consumers"].append("NEW")
    second = deepcopy(first)
    second.update(id="EVOLUTION-NEXT", **{"from": "B-REUSABLE", "to": "B-LATEST"},
                  approval_ref="TEST-PO-ACTION1")
    second["evolution"]["contracts"] = {
        "B-REUSABLE": first["evolution"]["contracts"]["B-REUSABLE"],
        "B-LATEST": _seal(latest_contract)}
    second["evolution"]["consumers"] = {
        "B-REUSABLE": first["evolution"]["consumers"]["B-REUSABLE"],
        "B-LATEST": ["ClinicalTrials.gov", "FDA", "NEW", "SEC"]}
    migration = second["evolution"]["obligations"][0]
    migration.update({"from": "REUSABLE", "to": "LATEST", "contracts": {
        "REUSABLE": first["evolution"]["obligations"][0]["contracts"]["REUSABLE"],
        "LATEST": _seal(latest_obligation_contract)}})
    case.approve("SUPERSESSION")
    case.evidence["approvals"][-1]["disposition_sha256"] = _seal(second)
    case.evidence["dispositions"].append(second)
    current["supersession_ref"] = "EVOLUTION-NEXT"
    current_obligation.update(status="SUPERSEDED", disposition_ref="EVOLUTION-NEXT")
    report = case.run()
    assert report["status"] == "RESOLVED_CONTEXT", report["diagnostics"]
    assert {c["id"] for c in report["controls"]} >= {"B-LATEST"}
    assert not {"B-O21", "B-REUSABLE"} & {c["id"] for c in report["controls"]}
    assert first == historical


def test_evolution_approval_cannot_rewrite_pinned_obligation_provenance(case):
    d = _evolved(case)
    case.obligation("O21")["origin_ref"] = "invented-origin"
    contract = {k: v for k, v in case.obligation("O21").items()
                if k not in {"status", "evidence_refs", "disposition_ref"}}
    d["evolution"]["obligations"][0]["contracts"]["O21"] = _seal(contract)
    case.evidence["approvals"][0]["disposition_sha256"] = _seal(d)
    rejected(case.run(), "BASELINE_COVERAGE", "O21")


@pytest.mark.parametrize("fault", ["assertion", "consumer", "obligation", "history", "policy", "receipt"])
def test_evolution_protects_contract_and_complete_migration(case, fault):
    d = _evolved(case)
    if fault == "assertion":
        case.binding("B-REUSABLE")["obligations"][0]["required_assertions"] = ["weaker"]
    elif fault == "consumer":
        case.bindings["components"]["observation"]["consumers"].append("NEW")
    elif fault == "obligation":
        case.obligation("REUSABLE")["required_before"] = ["PRE_CLOSURE"]
    elif fault == "history":
        case.binding("B-O21")["obligations"][0]["fresh_for_action"] = False
    elif fault == "policy":
        d["evolution"]["obligations"][0]["evidence_policy"] = "NOT_APPLICABLE"
    else:
        case.evidence["evidence"][0]["action_id"] = "rewritten-history"
    rejected(case.run(), "EVOLUTION_INVALID")


@pytest.mark.parametrize("field,value", [("scope", "other-unit"),
                                        ("binding_ref", "B-X3"),
                                        ("required_before", ["PRE_CLOSURE"])])
def test_pinned_obligation_cannot_be_retargeted_without_disposition(case, field, value):
    case.obligation("O21")[field] = value
    rejected(case.run(), "BASELINE_COVERAGE", "O21")


def test_lowering_required_proof_does_not_redefine_approved_baseline(case):
    case.binding("B-X3")["obligations"][0]["proof_class"] = "LEVEL_1"
    rejected(case.run(), "BASELINE_COVERAGE", "B-X3")


def test_unknown_due_boundary_is_not_a_never_due_obligation(case):
    case.binding("B-O21")["obligations"][0]["required_before"] = ["TYPO_CANARY"]
    case.obligation("O21")["required_before"] = ["TYPO_CANARY"]
    case.pin_baseline()
    rejected(case.run(), "INVALID_SCHEMA")
