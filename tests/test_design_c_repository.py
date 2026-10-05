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


def test_intermediate_green_approval_covers_request_not_preexisting_observed_path(tmp_path):
    """Observed scope remains checked without expanding current mutation approval."""
    action = "BOUNDED_INTERMEDIATE_GREEN"
    requested = "modules/sec_company_identity_resolver.py"
    observed = "modules/preexisting_observed_dependency.py"
    case = RepositoryCase(tmp_path, obligation_ids=())
    case.bindings["components"]["opening"]["paths"].append(observed)
    case.write(requested, "# TEST ONLY current action target\n")
    case.write(observed, "# TEST ONLY pre-existing authorized delta\n")
    case.station["change_scope_paths"] = [requested, observed]
    case.pin_baseline()
    case.request.update(action="LOCAL_DIAGNOSIS", paths=[requested],
                        observed_changes=[observed])
    assert case.run()["diagnostics"] == [], "Observed scope must be valid independently"
    case.approve(action)
    approval = case.evidence["approvals"][-1]
    approval["change_scope_paths"] = [requested]
    case.request["action"] = action
    assert approval["id"] in case.station["approval_refs"]
    assert approval["issuer"] == "PRODUCT_OWNER" and approval["provenance"]
    for key in ("action", "action_id", "scope", "candidate_sha"):
        assert approval[key] == case.request[key]
    assert observed not in approval["change_scope_paths"]
    observed_bytes = (case.root / observed).read_bytes()
    report = case.run()
    assert case.request["paths"] == [requested]
    assert case.request["observed_changes"] == [observed]
    assert observed in report["station"]["change_scope_paths"]
    assert (case.root / observed).read_bytes() == observed_bytes
    assert all(d == {"code": "APPROVAL_INVALID", "subject": action}
               for d in report["diagnostics"]), report
    assert report["intermediate_execution"]["permission"] == "PERMITTED", (
        "Current approval must cover explicit request.paths, while the pre-existing "
        "observed path remains present and subject to existing checks", report)
    assert report["intermediate_execution"]["approval_ref"] == approval["id"]
    assert report["status"] == "RESOLVED_CONTEXT"
    assert report["diagnostics"] == []


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


def test_expectation_model_declared_dependency_not_component_ownership(tmp_path, monkeypatch):
    """Exercise the expectation producer, not a replacement Resolver."""
    ids = ("DC-FOUNDATION", "DC-CONTINUITY", "DC-REGRESSION")
    case = RepositoryCase(tmp_path, obligation_ids=ids)
    dependency = "shared/acceptance-input.txt"
    case.bindings["components"]["shared-input"] = {
        "paths": [dependency], "consumers": ["synthetic-consumer"],
    }
    case.write(dependency, "original\n")
    for oid in ids:
        case.satisfy(oid)
        receipt = case.evidence["evidence"][-1]
        xml = '<testsuite>' + '<testcase name="synthetic" />' * 964 + '</testsuite>'
        case.write(receipt["path"], xml)
        receipt["sha256"] = digest(xml)
        receipt["validation"].update(kind="pytest-junit", minimum_tests=964,
                                      evidence_sha256=digest(xml))
        receipt["subject_hashes"] = {dependency: digest("original\n")}
    case.request.update(action="LOCAL_DIAGNOSIS")
    case.station["resolver_request"] = deepcopy(case.request)
    case.station["change_scope_paths"] = [dependency]
    case.approve("LOCAL_DIAGNOSIS")
    case.evidence["approvals"][-1]["change_scope_paths"] = [dependency]
    case.pin_baseline()
    case.flush()
    monkeypatch.setattr(sys.modules[__name__], "ROOT", case.root)
    monkeypatch.setattr(sys.modules[__name__], "PIN",
                        sha256((case.root / BASELINE).read_bytes()).hexdigest())
    from tests.test_support.design_c_fixture import CHRONICLE
    monkeypatch.setattr(sys.modules[__name__], "STATION", CHRONICLE)
    assert expected_recovery_evidence_diagnostics() == []
    case.write(dependency, "approved change\n")
    assert expected_recovery_evidence_diagnostics() == [
        {"code": "RENEWAL_REQUIRED", "subject": oid} for oid in ids
    ]


@pytest.mark.parametrize("surface", ["context", "wds", "station"])
def test_native_expectations_preserve_current_unreconciled_state(monkeypatch, tmp_path, surface):
    """Historical rejection against isolated authority/proof, never live state."""
    blocks = re.findall(r"```json station-state\s*\n(.*?)\n```",
                        (ROOT / STATION).read_text(encoding="utf-8-sig"), re.S)
    station = json.loads(blocks[0])
    station["alignment"] = "NOT VERIFIED"
    ids = ("O28", "C2-REUSABLE", "X1-REUSABLE", "X3-REUSABLE",
           "DC-FOUNDATION", "DC-CONTINUITY", "DC-REGRESSION")
    stale_proofs = {"O28", "DC-FOUNDATION", "DC-CONTINUITY", "DC-REGRESSION"}
    case = RepositoryCase(tmp_path, obligation_ids=ids)
    subject = "modules/sec_company_identity_resolver.py"
    case.write(subject, "TEST ONLY historical subject\n")
    for oid in ids:
        case.binding("B-" + oid)["applies_to"]["always"] = True
        case.satisfy(oid)
        if oid in stale_proofs:
            case.evidence["evidence"][-1]["subject_hashes"] = {
                subject: digest("TEST ONLY historical subject\n")}
    case.station = deepcopy(station)
    case.station["resolver_request"] = deepcopy(case.request)
    case.station["resolver_request"].update(
        action="BOUNDED_INTERMEDIATE_GREEN", paths=[])
    case.pin_baseline()  # Independent TEST ONLY snapshot, before historical drift.
    for oid in ids[:-1]:
        authority = case.binding("B-" + oid)["authority"]
        original_text = (case.root / authority["path"]).read_text(encoding="utf-8")
        case.write(authority["path"], original_text + "\nTEST ONLY later authority edit\n")
    case.write(subject, "TEST ONLY later subject edit\n")
    case.flush()
    from tests.test_support.design_c_fixture import CHRONICLE
    monkeypatch.setattr(sys.modules[__name__], "ROOT", case.root)
    monkeypatch.setattr(sys.modules[__name__], "STATION", CHRONICLE)
    monkeypatch.setattr(sys.modules[__name__], "PIN",
                        sha256((case.root / BASELINE).read_bytes()).hexdigest())
    expected = [
        {"code": "AUTHORITY_STALE", "subject": bid}
        for bid in ("B-O28", "B-C2-REUSABLE", "B-X1-REUSABLE",
                    "B-X3-REUSABLE", "B-DC-FOUNDATION", "B-DC-CONTINUITY")
    ] + [
        {"code": "EVIDENCE_INVALID", "subject": oid}
        for oid in ("O28", "DC-FOUNDATION", "DC-CONTINUITY", "DC-REGRESSION")
    ]
    report = {"status": "UNRESOLVED" if surface == "context" else "TRANSITION_BLOCKED",
              "diagnostics": deepcopy(expected), "station": station,
              "material_outcomes": station["material_outcomes"],
              "controls": [{"id": "D06"}]}
    report["station"] = deepcopy(case.station)
    if surface == "context":
        report["intermediate_execution"] = {
            "action": "BOUNDED_INTERMEDIATE_GREEN",
            "action_id": case.request["action_id"],
            "permission": "BLOCKED", "approval_ref": None}
    # These transition actions consume no proof boundary; authority checks
    # still run. Evidence invalidity is inspected by the resolve-mode case.
    if surface != "context":
        expected = [d for d in expected if d["code"] == "AUTHORITY_STALE"]
        report["diagnostics"] = deepcopy(expected)
    original = deepcopy(report)
    monkeypatch.setattr(sys.modules[__name__], "native", lambda action=None: report)
    action = {"context": None, "wds": "WDS_DIAGNOSIS",
              "station": "STATION_COMPLETE"}[surface]
    # Exercise the shared independent oracle, not current-station assertions.
    assert_evidence_sensitive_status(native(action), transition=surface != "context",
                                     action=action)
    assert report == original
    assert report["diagnostics"] == expected
    assert report["station"]["alignment"] == "NOT VERIFIED"


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
    mode = "transition" if action is not None else request["mode"]
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
    # Independently reconstruct authority failures, never copy Resolver output.
    diagnostics = []
    bindings = {b["id"]: b for b in registry["bindings"]}
    for binding in bindings.values():
        if binding.get("supersession_ref"):
            # Sealed predecessor contracts retain historical authority. Invalid
            # supersession diagnostics are not whitelisted by this model.
            continue
        authority = binding["authority"]
        text = (ROOT / authority["path"]).read_text(encoding="utf-8-sig")
        assert authority["anchor"] in text.splitlines()
        if digest(text) != authority["digest"]:
            diagnostics.append({"code": "AUTHORITY_STALE", "subject": binding["id"]})
    authority_invalid = bool(diagnostics)
    # No new boundary policy: use the existing public boundary definitions.
    from tools.resolve_authority import BOUNDARIES, INTERMEDIATE_GREEN
    reached = set() if action == INTERMEDIATE_GREEN else BOUNDARIES[action]
    paths = request.get("paths", []) + request.get("observed_changes", [])
    components = {name for name, component in registry["components"].items()
                  if any(fnmatch(path, pattern) for path in paths
                         for pattern in component.get("paths", []))}
    # Follow all applicable active receipt references, not a fixed diagnostic list.
    expected_ids = {}
    for obligation in obligations:
        if obligation["status"] != "CLOSED":
            continue
        applies = bindings[obligation["binding_ref"]]["applies_to"]
        relevant = (bool(reached.intersection(obligation["required_before"]))
                    if mode == "transition" else
                    not paths or applies.get("always") or
                    bool(components.intersection(applies.get("components", []))))
        if not relevant:
            continue
        oid = obligation["obligation_id"]
        assert len(obligation["evidence_refs"]) == 1
        expected_ids[obligation["evidence_refs"][0]] = oid
    selected = [e for e in evidence if e["id"] in expected_ids]
    assert len(selected) == len(expected_ids)
    assert {e["id"] for e in selected} == set(expected_ids)
    for entry in selected:
        obligation = expected_ids[entry["id"]]
        receipt = entry["validation"]
        raw = (ROOT / entry["path"]).read_bytes()
        assert sha256(raw).hexdigest() == entry["sha256"] == receipt["evidence_sha256"]
        assert receipt["status"] == "VERIFIED"
        assert receipt["validator_ref"]
        assert entry["scope"] == "R&D 002"
        record = next(o for o in obligations if o["obligation_id"] == obligation)
        requirement = bindings[record["binding_ref"]]["obligations"][0]
        assert entry["proof_class"] == requirement["proof_class"]
        assert set(requirement["required_assertions"]).issubset(entry["assertions"])
        if receipt.get("kind") == "pytest-junit":
            suite = ET.fromstring(raw)
            assert len(list(suite.iter("testcase"))) >= receipt["minimum_tests"]
            for rejected_tag in ("failure", "error", "skipped"):
                assert not list(suite.iter(rejected_tag))
        subjects = entry.get("subject_hashes", {})
        changed = {path for path, digest in subjects.items()
                   if sha256((ROOT / path).read_bytes()).hexdigest() != digest}
        if changed:
            code = ("RENEWAL_REQUIRED" if not authority_invalid and
                    eligible(changed, obligation) else "EVIDENCE_INVALID")
            diagnostics.append({"code": code, "subject": obligation})
    return diagnostics


def assert_evidence_sensitive_status(report, *, transition=False, action=None):
    expected = expected_recovery_evidence_diagnostics(action)
    assert sorted(report["diagnostics"], key=lambda d: (d["code"], d["subject"])) == sorted(
        expected, key=lambda d: (d["code"], d["subject"]))
    from tools.resolve_authority import INTERMEDIATE_GREEN
    request = report["station"]["resolver_request"]
    intermediate = not transition and request["action"] == INTERMEDIATE_GREEN
    if intermediate:
        permission = report["intermediate_execution"]
        assert permission["action"] == INTERMEDIATE_GREEN
        assert permission["action_id"] == request["action_id"]
        records = json.loads(re.findall(
            r"```json evidence\s*\n(.*?)\n```",
            (ROOT / TRACE).read_text(encoding="utf-8-sig"), re.S)[0])
        matching = [a for a in records["approvals"]
                    if a["id"] in report["station"]["approval_refs"]
                    and a.get("issuer") == "PRODUCT_OWNER" and a.get("provenance")
                    and all(a.get(key) == request.get(key)
                            for key in ("action", "action_id", "scope", "candidate_sha"))
                    and isinstance(a.get("change_scope_paths"), list)
                    and bool(request["paths"])
                    and set(request["paths"]).issubset(a["change_scope_paths"])]
        permitted = permission["permission"] == "PERMITTED"
        assert permission["permission"] in {"PERMITTED", "BLOCKED"}
        assert permitted == (bool(matching) and
                             all(d["code"] == "RENEWAL_REQUIRED" for d in expected))
        if permitted:
            assert permission["approval_ref"] in report["station"]["approval_refs"]
            assert all(d["code"] == "RENEWAL_REQUIRED" for d in expected)
            approval = next(a for a in matching
                            if a["id"] == permission["approval_ref"])
            assert approval["issuer"] == "PRODUCT_OWNER" and approval["provenance"]
            assert all(approval.get(key) == request.get(key)
                       for key in ("action", "action_id", "scope", "candidate_sha"))
            assert set(request["paths"]).issubset(approval["change_scope_paths"])
        if any(d["code"] != "RENEWAL_REQUIRED" for d in expected):
            assert not permitted
        assert report["status"] == ("RESOLVED_CONTEXT" if permitted else "UNRESOLVED")
        assert report["station"]["alignment"] == ("NOT VERIFIED" if expected else "VERIFIED")
        assert "closure_pass" not in report
    elif expected:
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


def test_native_x2_approved_supersession_preserves_history_and_release_contract():
    registry = json.loads((ROOT / BINDINGS).read_text(encoding="utf-8"))
    obligations = json.loads((ROOT / BASELINE).with_name("open-obligations.json").read_text(encoding="utf-8"))["obligations"]
    by_binding = {b["id"]: b for b in registry["bindings"]}
    by_obligation = {o["obligation_id"]: o for o in obligations}
    old, new = by_binding["B-X2"], by_binding["B-X2-POST-PUSH"]
    assert old["supersession_ref"] == by_obligation["X2"]["disposition_ref"]
    assert old["obligations"][0]["required_before"] == ["PRE_PUSH_OR_PROMOTION"]
    assert by_obligation["X2"]["status"] == "SUPERSEDED"
    assert by_obligation["X2"]["required_before"] == ["PRE_PUSH_OR_PROMOTION"]
    assert new["authority"]["path"] == "docs/03-ניהול-הפיתוח-ההנדסי/החלטות-הנדסיות.md"
    assert new["authority"]["anchor"] == "## Required-before transitions"
    requirement = new["obligations"][0]
    assert requirement["candidate_match_required"] is True
    assert requirement["required_assertions"] == [
        "Authorized Push of Release Subject R",
        "Authoritative remote SHA equals Release Subject R",
        "Required CI runs on exact Release Subject R",
        "Required CI completes with PASS on exact Release Subject R",
        "Validated POST_PUSH release-delivery evidence for Release Subject R",
    ]
    assert requirement["required_before"] == ["POST_PUSH"]
    assert by_obligation["X2-POST-PUSH"]["status"] == "OPEN"
    assert by_obligation["X2-POST-PUSH"]["evidence_refs"] == []
    report = native("POST_PUSH")
    assert report["x2"]["obligation_id"] == "X2-POST-PUSH"
    assert {"code": "OBLIGATION_DUE", "subject": "X2-POST-PUSH"} in report["diagnostics"]
    assert not any(d["code"] in {"BASELINE_COVERAGE", "EVOLUTION_INVALID"} for d in report["diagnostics"])


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
    request = report["station"]["resolver_request"]
    assert request["mode"] == "resolve"
    assert request["action"] == "BOUNDED_INTERMEDIATE_GREEN"
    assert request["action_id"] == "rnd002-x2-po1-green-20261003"
    assert request["paths"] == [
        "docs/03-ניהול-הפיתוח-ההנדסי/החלטות-הנדסיות.md",
        "docs/03-ניהול-הפיתוח-ההנדסי/decision-bindings.json",
        "docs/03-ניהול-הפיתוח-ההנדסי/open-obligations.json",
    ]
    assert "PO-WDS-RECOVERY-2026-09-08" in report["station"]["approval_refs"]
    assert {"WDS-RECOVERY-PRINCIPLE", "WDS-RECOVERY-APPROVAL",
            "WDS-RECOVERY-DIAGNOSIS", "WDS-RECOVERY-REVALIDATION-PENDING"}.issubset(
        {outcome["id"] for outcome in report["material_outcomes"]})
    assert {control["id"] for control in report["controls"]} == {
        "B-DC-FOUNDATION", "B-DC-CONTINUITY", "B-DC-REGRESSION"}


@pytest.mark.parametrize("action,x2_required", [
    ("PRE_PUSH_OR_PROMOTION", False),
    ("PRE_CANARY", False),
    ("PRE_PRODUCTION", False),
    ("POST_PUSH", True),
    ("PRE_CLOSURE", True),
], ids=["PRE_PUSH_OR_PROMOTION", "PRE_CANARY", "PRE_PRODUCTION", "POST_PUSH", "PRE_CLOSURE"])
def test_native_carried_obligations_block_their_boundaries(action, x2_required):
    report = native(action)
    assert report["status"] == "TRANSITION_BLOCKED"
    due = {d["subject"] for d in report["diagnostics"] if d["code"] == "OBLIGATION_DUE"}
    active_x2 = report["x2"]
    assert active_x2 is not None
    assert active_x2["status"] == "OPEN"
    assert active_x2["required_before"] == ["POST_PUSH"]
    if x2_required:
        assert active_x2["obligation_id"] in due, report["diagnostics"]
    else:
        assert not {"X2", active_x2["obligation_id"]} & due, report["diagnostics"]
    assert not {"C2", "X1", "X3", "C2-REUSABLE", "X1-REUSABLE", "X3-REUSABLE"} & due
    assert "closure_pass" not in report


def test_native_completed_wds_diagnosis_does_not_restore_superseded_prohibition():
    report = native("WDS_DIAGNOSIS")
    assert_evidence_sensitive_status(report, transition=True, action="WDS_DIAGNOSIS")
    assert "WDS_DIAGNOSIS" not in report["station"]["forbidden_actions"]
    assert report["station"]["station_status"] == "LOCAL PASS"
    assert report["station"]["next_action"] == (
        "Complete authorized Component Evolution local verification through PRE_COMMIT only. "
        "X2 remains OPEN for separately authorized release proof. "
        "No Stage, Commit, Push, external action or R&D003."
    )


def test_native_station_completion_never_promotes_stale_receipts_to_pass():
    report = native("STATION_COMPLETE")
    assert_evidence_sensitive_status(report, transition=True, action="STATION_COMPLETE")
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
        binding = deepcopy(binding)
        authority = binding["authority"]["path"]
        authority_text = (ROOT / authority).read_text(encoding="utf-8-sig")
        case.write(authority, authority_text)
        # Bind the synthetic copy to its actual text, not the real registry pin.
        binding["authority"]["digest"] = digest(authority_text)
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


@pytest.mark.parametrize("dependency", ["shared/rules.json", "adapters/reference.txt"])
def test_declared_cross_component_dependency_enters_controlled_renewal(tmp_path, dependency):
    """R-CR1/R-CR8: entry eligibility never consumes stale synthetic proof."""
    oid = "SYNTHETIC-CLAIM"
    case = RepositoryCase(tmp_path, obligation_ids=(oid,))
    owner_path = "consumer/entry.py"
    case.bindings["components"].update({
        "claim-owner": {"paths": [owner_path], "consumers": ["consumer"]},
        "dependency-owner": {"paths": [dependency], "consumers": ["reference"]},
    })
    binding = case.binding(f"B-{oid}")
    binding["applies_to"]["components"] = ["claim-owner"]
    case.write(owner_path, "# TEST ONLY consumer\n")
    before = "TEST ONLY declared dependency before change\n"
    case.write(dependency, before)
    case.satisfy(oid)
    receipt = case.evidence["evidence"][-1]
    receipt["subject_hashes"] = {dependency: digest(before)}
    original_receipt = deepcopy(receipt)
    artifact_bytes = (case.root / receipt["path"]).read_bytes()
    # Pin only the initial synthetic repository, before any dependency change.
    case.pin_baseline()
    case.request.update(action="LOCAL_DIAGNOSIS", paths=[owner_path, dependency],
                        observed_changes=[])
    case.station["change_scope_paths"] = [dependency]
    for action in ("LOCAL_DIAGNOSIS", "PRE_CANARY"):
        case.approve(action)
        case.evidence["approvals"][-1]["change_scope_paths"] = [dependency]
    initial = case.run()
    assert initial["status"] == "RESOLVED_CONTEXT"
    assert initial["diagnostics"] == []
    assert not any(fnmatch(dependency, pattern)
                   for pattern in case.bindings["components"]["claim-owner"]["paths"])
    assert dependency in receipt["subject_hashes"]
    case.write(dependency, "TEST ONLY approved dependency change\n")
    case.request["observed_changes"] = [dependency]
    stale = case.run()
    assert stale["status"] == "UNRESOLVED"
    assert len(stale["diagnostics"]) == 1, stale["diagnostics"]
    assert stale["diagnostics"][0] in (
        {"code": "EVIDENCE_INVALID", "subject": oid},
        {"code": "RENEWAL_REQUIRED", "subject": oid},
    )
    case.request.update(mode="transition", action="PRE_CANARY")
    blocked = case.run()
    assert blocked["status"] == "TRANSITION_BLOCKED"
    assert {"code": "OBLIGATION_DUE", "subject": oid} in blocked["diagnostics"]
    assert receipt == original_receipt
    assert (case.root / receipt["path"]).read_bytes() == artifact_bytes
    # The sole expected RED: owning-component membership rejects this declared
    # dependency despite valid authority, mapped scope and matched approvals.
    assert stale["diagnostics"] == [{"code": "RENEWAL_REQUIRED", "subject": oid}]


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

def test_r5_release_subject_identity_is_independent_of_governance_revision(tmp_path):
    case = RepositoryCase(tmp_path)
    case.satisfy_all()
    case.transition("PRE_CLOSURE")

    assert "release_subject_sha" not in case.request
    assert "governance_revision_sha" not in case.request

    report = case.run()

    assert report["status"] == "TRANSITION_BLOCKED", (
        "Closure context must fail closed unless immutable Release Subject R "
        "and Governance Revision G have separate explicit identities",
        report,
    )

    release_subject = "a" * 40
    governance_revision = "b" * 40

    case.station["release_subject_sha"] = release_subject
    case.station["governance_revision_sha"] = governance_revision
    case.request["release_subject_sha"] = release_subject
    case.request["governance_revision_sha"] = governance_revision
    case.request["governance_sync_proof"] = {
        "governance_revision_sha": governance_revision,
        "synchronized": True,
    }
    case.request["governance_terminal_observation"] = {
        "governance_revision_sha": governance_revision,
        "terminal": True,
        "creates_governance_revision": False,
    }

    report = case.run()

    assert report["status"] == "TRANSITION_ALLOWED", report["diagnostics"]

    case.request["release_subject_sha"] = governance_revision
    case.station["release_subject_sha"] = governance_revision

    report = case.run()

    assert report["status"] == "TRANSITION_BLOCKED", (
        "Release Subject R and Governance Revision G must remain "
        "separate explicit identities",
        report,
    )
def test_r7_closure_requires_final_governance_synchronization(tmp_path):
    case = RepositoryCase(tmp_path)
    case.satisfy_all()
    case.transition("PRE_CLOSURE")

    release_subject = "a" * 40
    governance_revision = "b" * 40

    case.station["release_subject_sha"] = release_subject
    case.station["governance_revision_sha"] = governance_revision
    case.request["release_subject_sha"] = release_subject
    case.request["governance_revision_sha"] = governance_revision

    assert "governance_sync_proof" not in case.request

    report = case.run()

    assert report["status"] == "TRANSITION_BLOCKED", (
        "Final Closure must fail closed without explicit final Governance "
        "Revision synchronization proof",
        report,
    )

    case.request["governance_sync_proof"] = {
        "governance_revision_sha": governance_revision,
        "synchronized": True,
    }
    case.request["governance_terminal_observation"] = {
        "governance_revision_sha": governance_revision,
        "terminal": True,
        "creates_governance_revision": False,
    }

    report = case.run()

    assert report["status"] == "TRANSITION_ALLOWED", report["diagnostics"]

    case.request["governance_sync_proof"]["governance_revision_sha"] = "c" * 40

    report = case.run()

    assert report["status"] == "TRANSITION_BLOCKED", (
        "Governance synchronization proof must bind the exact "
        "Governance Revision G",
        report,
    )

def test_x2_supersession_returns_open_active_terminal(tmp_path):
    """TEST ONLY accepted evolution must return the active X2 revision."""
    case = RepositoryCase(tmp_path, obligation_ids=("X2",))
    predecessor_binding = case.binding("B-X2")
    predecessor = case.obligation("X2")
    predecessor_binding["obligations"][0]["required_before"] = ["PRE_PUSH_OR_PROMOTION"]
    predecessor["required_before"] = ["PRE_PUSH_OR_PROMOTION"]
    case.pin_baseline()  # TEST ONLY historical snapshot, before evolution.

    successor_binding = deepcopy(predecessor_binding)
    successor_binding["id"] = "B-X2-POST-PUSH"
    successor_binding["obligations"][0]["required_before"] = ["POST_PUSH"]
    successor = deepcopy(predecessor)
    successor.update(obligation_id="X2-POST-PUSH", binding_ref="B-X2-POST-PUSH",
                     required_before=["POST_PUSH"])
    case.bindings["bindings"].append(successor_binding)
    case.obligations["obligations"].append(successor)
    ref = "TEST-EV-X2-POST-PUSH"
    predecessor_binding["supersession_ref"] = ref
    predecessor.update(status="SUPERSEDED", disposition_ref=ref)

    def seal(value):
        return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")).encode("utf-8")).hexdigest()

    def binding_contract(binding):
        contract = deepcopy(binding)
        contract.pop("supersession_ref", None)
        contract["authority"].pop("digest")
        for requirement in contract["obligations"]:
            requirement.setdefault("candidate_match_required", requirement.get("fresh_for_action"))
        return contract

    def obligation_contract(obligation):
        return {k: v for k, v in obligation.items()
                if k not in {"status", "evidence_refs", "disposition_ref"}}

    consumers = sorted(case.bindings["components"]["opening"]["consumers"])
    disposition = {
        "id": ref, "kind": "SUPERSESSION", "from": "B-X2", "to": "B-X2-POST-PUSH",
        "scope": "R&D 002", "authority_ref": predecessor_binding["authority"]["path"] + "#X2",
        "approval_ref": "TEST-PO-ACTION",
        "evolution": {
            "contracts": {b["id"]: seal(binding_contract(b))
                          for b in (predecessor_binding, successor_binding)},
            "consumers": {b["id"]: consumers
                          for b in (predecessor_binding, successor_binding)},
            "obligations": [{
                "from": "X2", "to": "X2-POST-PUSH",
                "contracts": {o["obligation_id"]: seal(obligation_contract(o))
                              for o in (predecessor, successor)},
                "historical_status": "OPEN", "historical_evidence_refs": [],
                "evidence_policy": "RENEWAL_REQUIRED", "reusable_evidence": {},
                "reason": "TEST ONLY approved POST_PUSH revision; no proof exists or is reused.",
            }],
        },
    }
    case.approve("SUPERSESSION")
    case.evidence["approvals"][-1]["disposition_sha256"] = seal(disposition)
    case.evidence["dispositions"].append(disposition)
    report = case.run()
    assert report["diagnostics"] == [], report["diagnostics"]
    assert report["status"] == "RESOLVED_CONTEXT"
    assert report["x2"] is not None
    assert report["x2"]["obligation_id"] == "X2-POST-PUSH", report["x2"]
    assert report["x2"]["status"] == "OPEN"


def test_x2_is_not_due_at_pre_push_after_po1_boundary_separation():
    report = native("PRE_PUSH_OR_PROMOTION")
    active_x2 = report["x2"]
    assert active_x2 is not None

    x2_due = [
        diagnostic
        for diagnostic in report["diagnostics"]
        if diagnostic.get("code") == "OBLIGATION_DUE"
        and diagnostic.get("subject") in {"X2", active_x2["obligation_id"]}
    ]

    assert not x2_due, (
        "PO-1 separates PRE_PUSH authorization from X2 POST_PUSH delivery proof; "
        "X2 must not be due at PRE_PUSH_OR_PROMOTION",
        report,
    )
