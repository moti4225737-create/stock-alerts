"""Foundation RED: repository authority retrieval, not live WDS diagnosis."""

from copy import deepcopy

import pytest

from tests.test_support.design_c_fixture import (
    ARCHITECTURE, BASELINE, case, rejected,
)


def test_prior_decision_wds_retrieves_actual_four_field_authority(case):
    report = case.run()
    assert report["status"] == "RESOLVED_CONTEXT"
    identity = next(c for c in report["controls"] if c["id"] == "D06")
    assert identity["authority"]["path"] == ARCHITECTURE
    for field in ("ticker", "company_name", "CIK", "exchange", "מאותה רשומת SEC"):
        assert field in identity["text"]
    assert "contract_change_authorized" not in report


def test_cross_provider_applicability_from_ct_change(case):
    case.request.update(paths=["modules/clinical_trials_provider.py"], task="Change CT observation")
    report = case.run()
    assert report["status"] == "RESOLVED_CONTEXT"
    for bid in ("B-O21", "B-O22"):
        control = next(c for c in report["controls"] if c["id"] == bid)
        assert set(control["consumers"]) >= {"SEC", "FDA", "ClinicalTrials.gov"}


@pytest.mark.parametrize("mutation,code", [
    ("missing_file", "AUTHORITY_MISSING"),
    ("missing_anchor", "ANCHOR_MISSING"),
    ("stale", "AUTHORITY_STALE"),
    ("duplicate_id", "DUPLICATE_BINDING"),
    ("schema", "INVALID_SCHEMA"),
    ("removed_binding", "BASELINE_COVERAGE"),
    ("removed_consumer", "CONSUMER_COVERAGE"),
    ("renamed_authority", "AUTHORITY_MISSING"),
])
def test_authority_corruption_is_not_empty_success(case, mutation, code):
    if mutation == "missing_file":
        (case.root / ARCHITECTURE).unlink()
    elif mutation == "missing_anchor":
        case.binding("D06")["authority"]["anchor"] = "## Does not exist"
    elif mutation == "stale":
        with (case.root / ARCHITECTURE).open("a", encoding="utf-8") as stream:
            stream.write("\nChanged authoritative requirement.\n")
    elif mutation == "duplicate_id":
        case.bindings["bindings"].append(deepcopy(case.binding("D06")))
    elif mutation == "schema":
        case.bindings["schema_version"] = 999
    elif mutation == "removed_binding":
        case.bindings["bindings"] = [b for b in case.bindings["bindings"] if b["id"] != "D06"]
    elif mutation == "removed_consumer":
        case.bindings["components"]["observation"]["consumers"].remove("FDA")
    elif mutation == "renamed_authority":
        (case.root / ARCHITECTURE).rename(case.root / "renamed-authority.md")
    rejected(case.run(), code)


def test_new_unmapped_consumer_is_reported(case):
    case.write("modules/provider_manager.py", 'PROVIDERS = ("SEC", "FDA", "ClinicalTrials.gov", "NEW")\n')
    case.request["observed_changes"] = ["modules/provider_manager.py"]
    rejected(case.run(), "CONSUMER_COVERAGE")


def test_unknown_changed_scope_is_not_no_applicable_controls(case):
    case.request["paths"] = ["new_domain/unmapped.py"]
    rejected(case.run(), "SCOPE_UNRESOLVED")


def test_supersession_requires_explicit_approved_authority(case):
    replacement = deepcopy(case.binding("D06"))
    replacement["id"] = "D06-REPLACEMENT"
    case.bindings["bindings"].append(replacement)
    case.binding("D06")["supersession_ref"] = "missing-approved-transition"
    rejected(case.run(), "SUPERSESSION_INVALID")


def test_approved_supersession_resolves_without_rewriting_history(case):
    replacement = deepcopy(case.binding("D06"))
    replacement["id"] = "D06-REPLACEMENT"
    case.bindings["bindings"].append(replacement)
    case.binding("D06")["supersession_ref"] = "REPLACE-06"
    case.evidence["dispositions"].append({"id": "REPLACE-06", "kind": "SUPERSESSION",
        "from": "D06", "to": "D06-REPLACEMENT", "approval_ref": "TEST-PO-ACTION",
        "authority_ref": ARCHITECTURE, "scope": "R&D 002"})
    case.approve("SUPERSESSION")
    report = case.run()
    assert report["status"] == "RESOLVED_CONTEXT"
    assert "D06-REPLACEMENT" in {c["id"] for c in report["controls"]}
    assert "D06" not in {c["id"] for c in report["controls"]}


def test_baseline_cannot_be_replaced_with_current_empty_state(case):
    case.bindings["bindings"] = []
    case.obligations["obligations"] = []
    case.dump(BASELINE, {"schema_version": 1, "bindings": [], "obligations": []})
    rejected(case.run(), "BASELINE_COVERAGE")


def test_missing_independently_pinned_baseline_is_unresolved(case):
    case.baseline.unlink()
    rejected(case.run(), "BASELINE_MISSING")


def test_modified_pinned_baseline_fails_integrity_check(case):
    case.baseline.write_text("{}", encoding="utf-8")
    rejected(case.run(), "BASELINE_INTEGRITY")

def test_r11_x2_has_one_authoritative_lineage(case):
    x2 = next(
        obligation
        for obligation in case.obligations["obligations"]
        if obligation["obligation_id"] == "X2"
    )
    case.obligations["obligations"].append(deepcopy(x2))

    report = case.run()

    assert report["status"] not in {"RESOLVED_CONTEXT", "TRANSITION_ALLOWED"}, (
        "A duplicated X2 obligation must fail closed; X2 has one authoritative lineage",
        report,
    )