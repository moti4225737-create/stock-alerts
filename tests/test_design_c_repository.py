"""Exercise the real repository registers without executing protected actions.

The pin is the approved initial coverage sample captured during foundation
bootstrap. A future authorized baseline migration must explicitly update it;
the test never calculates its expected value from the candidate manifest.
"""
import json
from copy import deepcopy
from fnmatch import fnmatch
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from tests.test_support.design_c_fixture import RepositoryCase, digest


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "docs/03-ניהול-הפיתוח-ההנדסי/obligation-coverage-baseline.json"
PIN = "872509619f0e55fec4901c0a2a29e369302bff4e2e81553ea3ab9367603cced2"
STATION = "docs/06-ניהול-הידע-ורציפות-התיעוד/chronicle/ספרינטים/2026-09-06-alpha-portfolio-initial-integration.md"
TRACE = "docs/06-ניהול-הידע-ורציפות-התיעוד/traceability.md"
BINDINGS = "docs/03-ניהול-הפיתוח-ההנדסי/decision-bindings.json"


def test_bounded_intermediate_green_contract(tmp_path, record_property):
    """PO-approved complete missing contract; no production action support.

    Recognition is the first necessary condition of intermediate permission.
    Diagnosis is used only to audit proof, never to stand in for GREEN.
    """
    action = "BOUNDED_INTERMEDIATE_GREEN"
    oid = "SYNTHETIC-DEV"
    case = RepositoryCase(tmp_path, obligation_ids=(oid,))
    subject = "modules/sec_company_identity_resolver.py"
    case.write(subject, "# TEST ONLY original subject\n")
    case.satisfy(oid)
    receipt = case.evidence["evidence"][-1]
    receipt["subject_hashes"] = {subject: digest("# TEST ONLY original subject\n")}
    case.station["change_scope_paths"] = [subject]
    case.request.update(action="LOCAL_DIAGNOSIS", paths=[subject], observed_changes=[])
    # Three distinct approvals: authorized change, proof audit, and GREEN.
    for approved_action, action_id in (
        ("RED", "approved-red"),
        ("LOCAL_DIAGNOSIS", "test-action-1"),
        (action, "approved-green"),
    ):
        case.approve(approved_action)
        case.evidence["approvals"][-1].update(
            action_id=action_id, change_scope_paths=[subject],
            provenance="TEST ONLY separate PO authorization for " + approved_action)
    assert {o["obligation_id"] for o in case.obligations["obligations"]} == {oid}
    assert case.run()["diagnostics"] == [], "Historical proof must initially validate"
    original_receipt = deepcopy(receipt)
    preserved_paths = [case.baseline, case.root / BASELINE,
                       case.root / receipt["path"],
                       case.root / case.binding("B-" + oid)["authority"]["path"]]
    preserved = {p: p.read_bytes() for p in preserved_paths}
    case.write(subject, "# TEST ONLY PO-authorized RED subject change\n")
    case.request["observed_changes"] = [subject]
    audit = case.run()
    assert audit["diagnostics"] == [{"code": "RENEWAL_REQUIRED", "subject": oid}]
    assert audit["status"] == "UNRESOLVED", "Stale evidence must remain invalid"
    # Even a separately approved acceptance action cannot use stale proof.
    case.transition("PRE_CANARY")
    case.evidence["approvals"][-1]["change_scope_paths"] = [subject]
    transition = case.run()
    assert transition["status"] == "TRANSITION_BLOCKED"
    assert {d["code"] for d in transition["diagnostics"]} == {
        "RENEWAL_REQUIRED", "OBLIGATION_DUE"}
    case.request.update(mode="resolve", action=action, action_id="approved-green")
    green_approval = next(a for a in case.evidence["approvals"] if a["action"] == action)
    assert green_approval["id"] in case.station["approval_refs"]
    assert green_approval["issuer"] == "PRODUCT_OWNER" and green_approval["provenance"]
    for key in ("action", "action_id", "scope", "candidate_sha"):
        assert green_approval[key] == case.request[key]
    assert green_approval["change_scope_paths"] == [subject]
    report = case.run()
    assert receipt == original_receipt
    assert all(p.read_bytes() == raw for p, raw in preserved.items())
    assert {d["subject"] for d in report["diagnostics"]} <= {oid, action}
    assert {d["code"] for d in report["diagnostics"]} <= {
        "EVIDENCE_INVALID", "RENEWAL_REQUIRED", "SCOPE_UNRESOLVED"}
    assert any(d["subject"] == oid and d["code"] in
               {"EVIDENCE_INVALID", "RENEWAL_REQUIRED"} for d in report["diagnostics"])
    record_property("intermediate_report", json.dumps(report, sort_keys=True))
    record_property("acceptance_report", json.dumps(transition, sort_keys=True))
    assert not any(d == {"code": "SCOPE_UNRESOLVED", "subject": action}
                   for d in report["diagnostics"]), (
        "PO-authorized BOUNDED_INTERMEDIATE_GREEN must be recognized before "
        "its bounded permission can be evaluated independently of stale proof; "
        + json.dumps({"status": report["status"], "diagnostics": report["diagnostics"]}))
    # The current documented downstream meaning of UNRESOLVED prohibits
    # progression. Separate matching PO authorization was checked above;
    # this assertion does not equate context resolution with authorization.
    assert report["status"] not in {"UNRESOLVED", "TRANSITION_BLOCKED"}, (
        "Eligible stale proof must not prohibit the separately authorized implementation")
    assert report["status"] != "TRANSITION_ALLOWED"
    assert "closure_pass" not in report
    assert report["intermediate_execution"] == {
        "action": action, "action_id": "approved-green",
        "permission": "PERMITTED", "approval_ref": green_approval["id"],
    }
    assert report["diagnostics"] == [{"code": "RENEWAL_REQUIRED", "subject": oid}]
    assert report["station"]["alignment"] == "NOT VERIFIED"
    assert "intermediate_execution" not in audit
    assert "intermediate_execution" not in transition


@pytest.mark.parametrize("fault", [
    "red_only", "missing_approval", "action_id", "issuer", "provenance",
    "candidate", "approval_scope", "station_scope", "unmapped", "unbound",
    "authority", "continuity", "artifact", "baseline", "inactive",
    "station_reference", "transition_mode", "empty_scope", "forbidden",
])
def test_intermediate_green_denials(tmp_path, fault):
    action = "BOUNDED_INTERMEDIATE_GREEN"
    case = RepositoryCase(tmp_path, obligation_ids=("SYNTHETIC-DEV",))
    subject = "modules/sec_company_identity_resolver.py"
    extra = "modules/extra_implementation.py"
    case.write(subject, "# before\n")
    case.satisfy("SYNTHETIC-DEV")
    receipt = case.evidence["evidence"][-1]
    receipt["subject_hashes"] = {subject: digest("# before\n")}
    case.station["change_scope_paths"] = [subject]
    case.request.update(action="LOCAL_DIAGNOSIS", paths=[subject])
    assert case.run()["diagnostics"] == []
    case.approve(action)
    approval = case.evidence["approvals"][-1]
    approval["change_scope_paths"] = [subject]
    case.request["action"] = action
    case.write(subject, "# approved change\n")
    before_receipt = deepcopy(receipt)
    if fault == "red_only":
        approval["action"] = "RED"
    elif fault == "missing_approval":
        case.evidence["approvals"] = []
    elif fault in {"action_id", "issuer", "candidate"}:
        approval["candidate_sha" if fault == "candidate" else fault] = "wrong"
    elif fault == "provenance":
        approval["provenance"] = ""
    elif fault in {"approval_scope", "station_scope", "unmapped", "unbound"}:
        case.write(extra, "# requested extra subject\n")
        case.request["paths"].append(extra)
        if fault != "unmapped":
            component = "orphan" if fault == "unbound" else "opening"
            if component == "orphan":
                case.bindings["components"][component] = {"paths": [], "consumers": []}
            case.bindings["components"][component]["paths"].append(extra)
        if fault != "approval_scope":
            approval["change_scope_paths"].append(extra)
        if fault != "station_scope":
            case.station["change_scope_paths"].append(extra)
    elif fault == "authority":
        case.write(case.binding("B-SYNTHETIC-DEV")["authority"]["path"], "# corrupted\n")
    elif fault == "continuity":
        case.station["unit_id"] = "MISSING-UNIT"
        # A conflicting existing register is an independent continuity blocker.
        case.write(case.request["register_ref"], "R&D 002 | NEXT\nMISSING-UNIT | NEXT\n")
    elif fault == "artifact":
        case.write(receipt["path"], "corrupted proof")
    elif fault == "baseline":
        case.baseline.write_text("{}", encoding="utf-8")
    elif fault == "inactive":
        case.station["unit_status"] = "CLOSED"
    elif fault == "station_reference":
        case.station["approval_refs"] = []
    elif fault == "transition_mode":
        case.request["mode"] = "transition"
    elif fault == "empty_scope":
        case.request["paths"] = []
    elif fault == "forbidden":
        case.station["forbidden_actions"] = [action]
    report = case.run()
    assert report["status"] == "UNRESOLVED"
    assert report["intermediate_execution"]["permission"] == "BLOCKED"
    assert report["intermediate_execution"]["action"] == action
    assert report["diagnostics"]
    assert receipt == before_receipt
    assert "closure_pass" not in report


def expected_recovery_evidence_diagnostics(action=None):
    """Audit real historical proof; never repair it or accept arbitrary failures.

    Subject names grant no renewal authority. Independently check the existing
    binding, explicit approval and current station scope. A passing test proves
    honest rejection/reconstruction, not fresh evidence or station readiness.
    """
    assert sha256((ROOT / BASELINE).read_bytes()).hexdigest() == PIN
    blocks = re.findall(r"```json evidence\s*\n(.*?)\n```",
                        (ROOT / TRACE).read_text(encoding="utf-8-sig"), re.S)
    assert len(blocks) == 1
    records = json.loads(blocks[0])
    evidence = records["evidence"]
    station_blocks = re.findall(r"```json station-state\s*\n(.*?)\n```",
                               (ROOT / STATION).read_text(encoding="utf-8-sig"), re.S)
    assert len(station_blocks) == 1
    station = json.loads(station_blocks[0])
    request = station["resolver_request"]
    action = action or request["action"]
    registry = json.loads((ROOT / BINDINGS).read_text(encoding="utf-8"))
    obligations = json.loads((ROOT / BASELINE).with_name("open-obligations.json")
                            .read_text(encoding="utf-8"))["obligations"]

    def eligible(subjects, oid):
        obligation = next(o for o in obligations if o["obligation_id"] == oid)
        binding = next(b for b in registry["bindings"] if b["id"] == obligation["binding_ref"])
        authority = binding["authority"]
        text = (ROOT / authority["path"]).read_text(encoding="utf-8-sig")
        if (authority["anchor"] not in text.splitlines()
                or sha256(text.encode("utf-8")).hexdigest() != authority["digest"]
                or station["unit_status"] != "ACTIVE"):
            return False
        if obligation["scope"] != request["scope"] or station["scope"] != request["scope"]:
            return False
        if not subjects.issubset(station.get("change_scope_paths", [])):
            return False
        if not all(any(fnmatch(subject, pattern)
                       for component in binding["applies_to"]["components"]
                       for pattern in registry["components"][component]["paths"])
                   for subject in subjects):
            return False
        return any(
            approval["id"] in station.get("approval_refs", [])
            and approval.get("issuer") == "PRODUCT_OWNER"
            and approval.get("action") == action
            and all(approval.get(key) == request.get(key)
                    for key in ("scope", "candidate_sha", "action_id"))
            and bool(approval.get("provenance"))
            and isinstance(approval.get("change_scope_paths"), list)
            and subjects.issubset(approval["change_scope_paths"])
            for approval in records.get("approvals", [])
        )
    # Follow the current obligation receipt; historical receipts remain immutable.
    expected_ids = {}
    for oid, minimum in (("DC-FOUNDATION", 84), ("DC-CONTINUITY", 84),
                         ("DC-REGRESSION", 964)):
        obligation = next(o for o in obligations if o["obligation_id"] == oid)
        assert len(obligation["evidence_refs"]) == 1
        expected_ids[obligation["evidence_refs"][0]] = (oid, minimum)
    selected = [e for e in evidence if e["id"] in expected_ids]
    assert len(selected) == len(expected_ids)
    assert {e["id"] for e in selected} == set(expected_ids)
    diagnostics = []
    for entry in selected:
        obligation, minimum = expected_ids[entry["id"]]
        receipt = entry["validation"]
        raw = (ROOT / entry["path"]).read_bytes()
        assert sha256(raw).hexdigest() == entry["sha256"] == receipt["evidence_sha256"]
        assert receipt["status"] == "VERIFIED"
        assert receipt["kind"] == "pytest-junit"
        assert receipt["validator_ref"]
        assert entry["obligation_id"] == obligation
        assert entry["scope"] == "R&D 002"
        assert entry["proof_class"] == "LEVEL_1"
        suite = ET.fromstring(raw)
        assert receipt["minimum_tests"] >= minimum
        assert len(list(suite.iter("testcase"))) >= receipt["minimum_tests"]
        for rejected_tag in ("failure", "error", "skipped"):
            assert not list(suite.iter(rejected_tag))
        subjects = entry["subject_hashes"]
        assert subjects, "Proof must retain its subject fingerprints"
        changed = {path for path, digest in subjects.items()
                   if sha256((ROOT / path).read_bytes()).hexdigest() != digest}
        if changed:
            code = "RENEWAL_REQUIRED" if eligible(changed, obligation) else "EVIDENCE_INVALID"
            diagnostics.append({"code": code, "subject": obligation})
    return diagnostics


def assert_evidence_sensitive_status(report, *, transition=False, action=None):
    expected = expected_recovery_evidence_diagnostics(action)
    assert sorted(report["diagnostics"], key=lambda d: (d["code"], d["subject"])) == sorted(
        expected, key=lambda d: (d["code"], d["subject"]))
    if expected:
        assert report["status"] == ("TRANSITION_BLOCKED" if transition else "UNRESOLVED")
        assert report["station"]["alignment"] == "NOT VERIFIED"
    else:
        assert report["status"] == ("TRANSITION_ALLOWED" if transition else "RESOLVED_CONTEXT")
        assert report["station"]["alignment"] == "VERIFIED"


def native(action=None):
    command = [sys.executable, "-B", str(ROOT / "tools/resolve_authority.py"),
        "--root", str(ROOT), "--request", str(ROOT / STATION),
        "--baseline", str(ROOT / BASELINE), "--baseline-sha256", PIN]
    if action:
        command.extend(["--mode", "transition", "--action", action])
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", timeout=30, check=False)
    assert result.returncode in (0, 2)
    return json.loads(result.stdout)


def test_native_context_reconstructs_current_station_with_honest_evidence_status():
    report = native()
    assert_evidence_sensitive_status(report)
    assert report["station"]["unit_id"] == "R&D 002"
    assert report["station"]["unit_status"] == "ACTIVE"
    assert report["station"]["station"] == "GREEN"
    assert report["station"]["station_status"] == "LOCAL PASS"
    assert report["station"]["next_action"] == (
        "Complete authorized Component Evolution local verification through PRE_COMMIT only. "
        "X2 remains OPEN for separately authorized release proof. "
        "No Stage, Commit, Push, external action or R&D003."
    )
    assert report["station"]["resolver_request"]["action"] == "PRE_COMMIT"
    assert "tests/test_design_c_hardening.py" in report["station"]["resolver_request"]["paths"]
    assert "PO-WDS-RECOVERY-2026-09-08" in report["station"]["approval_refs"]
    assert {"WDS-RECOVERY-PRINCIPLE", "WDS-RECOVERY-APPROVAL",
            "WDS-RECOVERY-DIAGNOSIS", "WDS-RECOVERY-REVALIDATION-PENDING"}.issubset(
        {outcome["id"] for outcome in report["material_outcomes"]})
    assert "D06" in {control["id"] for control in report["controls"]}


@pytest.mark.parametrize("action,required", [
    ("PRE_CANARY", {"X2"}),
    ("PRE_PRODUCTION", {"X2"}),
    ("PRE_PUSH_OR_PROMOTION", {"X2"}),
    ("PRE_CLOSURE", {"X2"}),
])
def test_native_carried_obligations_block_their_boundaries(action, required):
    report = native(action)
    assert report["status"] == "TRANSITION_BLOCKED"
    due = {d["subject"] for d in report["diagnostics"] if d["code"] == "OBLIGATION_DUE"}
    assert required.issubset(due), report["diagnostics"]
    assert not {"C2", "X1", "X3", "C2-REUSABLE", "X1-REUSABLE", "X3-REUSABLE"} & due
    assert "closure_pass" not in report


def test_native_completed_wds_diagnosis_does_not_restore_superseded_prohibition():
    report = native("WDS_DIAGNOSIS")
    assert report["status"] == "TRANSITION_ALLOWED"
    assert report["diagnostics"] == []
    assert report["station"]["alignment"] == "VERIFIED"
    assert "WDS_DIAGNOSIS" not in report["station"]["forbidden_actions"]
    assert report["station"]["station_status"] == "LOCAL PASS"
    assert report["station"]["next_action"] == (
        "Complete authorized Component Evolution local verification through PRE_COMMIT only. "
        "X2 remains OPEN for separately authorized release proof. "
        "No Stage, Commit, Push, external action or R&D003."
    )


def test_native_station_completion_never_promotes_stale_receipts_to_pass():
    report = native("STATION_COMPLETE")
    assert report["status"] == "TRANSITION_ALLOWED"
    assert report["diagnostics"] == []
    assert report["station"]["alignment"] == "VERIFIED"
    assert "closure_pass" not in report


def test_repository_governance_mapping_covers_native_test_without_unknown_scope_escape():
    from fnmatch import fnmatch

    components = json.loads((ROOT / BINDINGS).read_text(encoding="utf-8"))["components"]
    for path, expected in (
        ("tests/test_design_c_repository.py", {"governance"}),
        ("tests/test_unmapped_recovery_scope_probe.py", set()),
    ):
        actual = {
            name for name, component in components.items()
            if any(fnmatch(path, pattern) for pattern in component.get("paths", []))
        }
        assert actual == expected, (path, actual)


@pytest.fixture
def controlled_renewal_case(tmp_path):
    """TEST ONLY bootstrap, then stale subjects; never renew real evidence.

    PO Controlled Renewal RED: explicit subject scope lives on the existing
    approval record as change_scope_paths, linked by current station approval_refs.
    RENEWAL_REQUIRED uses the existing diagnostic channel, never a PASS status.
    These paths are scenario inputs, not a classifier or historical whitelist.
    """
    case = RepositoryCase(tmp_path)
    subjects = ["tools/resolve_authority.py", "tests/test_authority_continuity.py",
                "tests/test_support/design_c_fixture.py"]
    registry = json.loads((ROOT / BINDINGS).read_text(encoding="utf-8"))
    case.bindings["components"]["governance"] = registry["components"]["governance"]
    for binding in registry["bindings"]:
        if not binding["id"].startswith("B-DC-"):
            continue
        authority = binding["authority"]["path"]
        case.write(authority, (ROOT / authority).read_text(encoding="utf-8-sig"))
        case.bindings["bindings"].append(binding)
        oid = binding["id"][2:]
        requirement = binding["obligations"][0]
        case.obligations["obligations"].append({
            "obligation_id": oid, "binding_ref": binding["id"],
            "scope": "R&D 002", "status": "OPEN",
            "required_before": requirement["required_before"], "evidence_refs": [],
        })
        case.satisfy(oid)
        receipt = case.evidence["evidence"][-1]
        receipt["assertions"] = requirement["required_assertions"]
        receipt["subject_hashes"] = {path: digest("TEST ONLY before change\n")
                                     for path in subjects}
    for path in subjects:
        case.write(path, "TEST ONLY before change\n")
    # Initial synthetic bootstrap only; the real approved baseline is untouched.
    case.pin_baseline()
    case.request.update(action="LOCAL_DIAGNOSIS", paths=subjects.copy(),
                        observed_changes=subjects.copy())
    case.station["change_scope_paths"] = subjects.copy()
    case.approve("LOCAL_DIAGNOSIS")
    case.evidence["approvals"][-1]["change_scope_paths"] = subjects.copy()
    # Prove valid input before introducing the sole stale-evidence condition.
    assert case.run()["diagnostics"] == []
    for path in subjects:
        case.write(path, "TEST ONLY approved change\n")
    return case


def test_controlled_renewal_approved_bound_subjects_require_renewal(controlled_renewal_case):
    report = controlled_renewal_case.run()
    assert report["status"] == "UNRESOLVED"
    assert report["station"]["alignment"] == "NOT VERIFIED"
    assert { (d["code"], d["subject"]) for d in report["diagnostics"] } == {
        ("RENEWAL_REQUIRED", oid)
        for oid in ("DC-FOUNDATION", "DC-CONTINUITY", "DC-REGRESSION")
    }, report["diagnostics"]


@pytest.mark.parametrize("missing_condition", [
    "unknown_subject", "out_of_scope", "no_explicit_scope",
    "no_station_approval", "outside_station_scope", "unresolved_authority",
])
def test_controlled_renewal_ineligible_change_fails_closed(
    controlled_renewal_case, missing_condition,
):
    case = controlled_renewal_case
    if missing_condition == "unknown_subject":
        path = "tests/test_unmapped_recovery_scope_probe.py"
        case.write(path, "TEST ONLY unexpected change\n")
        case.request["observed_changes"].append(path)
        case.station["change_scope_paths"].append(path)
        case.evidence["approvals"][-1]["change_scope_paths"].append(path)
        for receipt in case.evidence["evidence"]:
            receipt["subject_hashes"][path] = digest("TEST ONLY before change\n")
    elif missing_condition == "out_of_scope":
        case.evidence["approvals"][-1]["change_scope_paths"].pop()
    elif missing_condition == "no_explicit_scope":
        del case.evidence["approvals"][-1]["change_scope_paths"]
    elif missing_condition == "no_station_approval":
        case.station["approval_refs"] = []
    elif missing_condition == "outside_station_scope":
        case.station["change_scope_paths"].pop()
    else:
        authority = case.binding("B-DC-FOUNDATION")["authority"]["path"]
        case.write(authority, "# TEST ONLY unresolved authority\n")
    report = case.run()
    assert report["status"] == "UNRESOLVED"
    assert report["station"]["alignment"] == "NOT VERIFIED"
    assert not any(d["code"] == "RENEWAL_REQUIRED" for d in report["diagnostics"])
    assert {d["subject"] for d in report["diagnostics"]
            if d["code"] == "EVIDENCE_INVALID"} == {
        "DC-FOUNDATION", "DC-CONTINUITY", "DC-REGRESSION"}


def test_controlled_renewal_required_never_satisfies_foundation_green(controlled_renewal_case):
    case = controlled_renewal_case
    # Approval remains for local diagnosis; checking a later boundary cannot
    # turn eligibility into fresh focused/full proof or action permission.
    case.request.update(mode="transition", action="FOUNDATION_GREEN")
    report = case.run()
    assert report["status"] == "TRANSITION_BLOCKED"
    assert report["station"]["alignment"] == "NOT VERIFIED"
    assert "closure_pass" not in report
    assert {d["subject"] for d in report["diagnostics"]
            if d["code"] == "OBLIGATION_DUE"} == {
        "DC-FOUNDATION", "DC-CONTINUITY", "DC-REGRESSION"}
