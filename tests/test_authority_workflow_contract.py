"""Small bootstrap/fixture contracts; these do not prove host interception."""

from hashlib import sha256
import json
from tests.test_support.design_c_fixture import (
    BASELINE, BINDINGS, OBLIGATIONS, OBLIGATION_IDS, ROOT, case,
)


def test_fixture_baseline_is_independent_of_mutable_obligation_status(case):
    baseline_bytes = case.baseline.read_bytes()
    baseline = json.loads(baseline_bytes)
    assert sha256(baseline_bytes).hexdigest() == case.baseline_digest
    assert {o["obligation_id"] for o in baseline["obligations"]} == set(OBLIGATION_IDS)
    assert all(o["status"] == "OPEN" for o in baseline["obligations"])
    case.obligation("O21")["status"] = "CLOSED"
    case.flush()
    assert case.baseline.read_bytes() == baseline_bytes
    assert json.loads((case.root / OBLIGATIONS).read_text(encoding="utf-8"))["obligations"][0]["status"] == "CLOSED"


def test_fixture_references_resolve_without_live_services(case):
    for binding in case.bindings["bindings"]:
        authority = binding["authority"]
        text = (case.root / authority["path"]).read_text(encoding="utf-8")
        assert authority["anchor"] in text
        assert sha256(text.encode("utf-8")).hexdigest() == authority["digest"]
    for path in (BINDINGS, OBLIGATIONS, BASELINE):
        assert json.loads((case.root / path).read_text(encoding="utf-8"))["schema_version"] == 1


def test_fixture_proof_artifacts_and_receipts_are_consistent(case):
    case.satisfy_all()
    for evidence in case.evidence["evidence"]:
        actual = sha256((case.root / evidence["path"]).read_bytes()).hexdigest()
        assert actual == evidence["sha256"] == evidence["validation"]["evidence_sha256"]
        assert "TEST ONLY" in (case.root / evidence["path"]).read_text(encoding="utf-8")
        assert evidence["id"] in case.obligation(evidence["obligation_id"])["evidence_refs"]


def test_agents_bootstrap_points_to_shared_resolver_and_durable_obligations():
    instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "tools/resolve_authority.py" in instructions, "Design C bootstrap invocation is missing"
    assert "open-obligations.json" in instructions
    assert "הפסקה" in instructions


def test_current_ci_collects_the_foundation_contracts_without_production_calls():
    workflow = (ROOT / ".github/workflows/stock-sentinel.yml").read_text(encoding="utf-8")
    assert "python -m pytest" in workflow
    assert "TELEGRAM_TOKEN: ci-test-token" in workflow
    # Test discovery, not a claim that an external CI run passed.
    for name in ("test_authority_resolution.py", "test_transition_guard.py",
                 "test_authority_continuity.py", "test_authority_workflow_contract.py"):
        assert (ROOT / "tests" / name).is_file()
