"""Synthetic repository input for the approved Design C RED contracts.

No resolver, guard, proof validator, or production state is implemented here.
The CLI contract under test is:
  python tools/resolve_authority.py --root ROOT --request REQUEST
      --baseline BASELINE --baseline-sha256 DIGEST
All paths other than the SUT are temporary. Evidence/approvals are TEST ONLY.
JSON output: status, diagnostics[{code, subject}], controls[{id, text,
consumers, authority}], obligations[{obligation_id, status}], station,
material_outcomes, snapshot. Exit 0 for resolved/allowed, 2 for blocked/unresolved.
The pinned baseline models an independently supplied approved snapshot, not
an agent-editable authorization source. Live approval provenance is not proved.
"""

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SUT = ROOT / "tools" / "resolve_authority.py"
ENGINEERING = "docs/03-ניהול-הפיתוח-ההנדסי"
KNOWLEDGE = "docs/06-ניהול-הידע-ורציפות-התיעוד"
BINDINGS = f"{ENGINEERING}/decision-bindings.json"
OBLIGATIONS = f"{ENGINEERING}/open-obligations.json"
BASELINE = f"{ENGINEERING}/obligation-coverage-baseline.json"
CHRONICLE = f"{KNOWLEDGE}/chronicle/ספרינטים/fixture-station.md"
TRACE = f"{KNOWLEDGE}/traceability.md"
REGISTER = f"{ENGINEERING}/ניהול-ספרינטים.md"
CURRENT = f"{KNOWLEDGE}/current-truth.md"
ARCHITECTURE = (
    "docs/02-ספר-המוצר/02.05-ארכיטקטורת-המערכת/"
    "02.05.03-תהליכים-ואינטראקציות.md"
)
SHA = "a" * 40  # Synthetic candidate, never a claimed repository SHA.
OBLIGATION_IDS = ("O21", "O22", "O26", "O28", "C2", "X1", "X2", "X3")


def digest(text):
    return sha256(text.encode("utf-8")).hexdigest()


class RepositoryCase:
    def __init__(self, tmp_path, *, obligation_ids=OBLIGATION_IDS):
        self.root = tmp_path / "repo"
        self.root.mkdir()
        self.baseline = tmp_path / "approved-baseline.json"
        self.request_path = tmp_path / "request.json"
        architecture = (ROOT / ARCHITECTURE).read_text(encoding="utf-8")
        self.write(ARCHITECTURE, architecture)
        self.bindings = {"schema_version": 1, "components": {
            "opening": {"paths": ["modules/sec_company_identity_resolver.py"],
                        "consumers": ["opening"]},
            "observation": {"paths": ["models/source_observation.py",
                "modules/clinical_trials_provider.py", "modules/sec_provider.py",
                "modules/fda_provider.py", "modules/provider_manager.py"],
                "consumers": ["SEC", "FDA", "ClinicalTrials.gov"]},
        }, "bindings": []}
        self.bindings["bindings"].append({
            "id": "D06", "authority": {"path": ARCHITECTURE,
                "anchor": "## Opening / Initialization",
                "digest": digest(architecture)},
            "applies_to": {"components": ["opening"], "operations": ["diagnosis"]},
            "obligations": [],
        })
        self.obligations = {"schema_version": 1, "obligations": []}
        self.evidence = {"schema_version": 1, "evidence": [], "approvals": [],
                         "dispositions": []}
        self.station = {
            "schema_version": 1, "unit_id": "R&D 002", "unit_status": "ACTIVE",
            "station": "FOUNDATION_RED", "station_status": "ACTIVE",
            "objective_ref": f"{CHRONICLE}#objective",
            "scope": "R&D 002", "approval_refs": [], "restriction_refs": [],
            "next_action": "REVIEW_RED", "repository_snapshot": SHA,
            "material_outcomes": [], "outcome_classification": "NO_MATERIAL_OUTCOME",
        }
        self.checkpoint_outcomes = []
        for oid in obligation_ids:
            if oid in ("O21", "O22"):
                component, level = "observation", 1
            else:
                component, level = "opening", 1
            if oid in ("C2", "X2"):
                level = 2
            if oid == "X3":
                level = 3
            boundaries = ["PRE_CANARY", "PRE_PRODUCTION"]
            if oid == "O28":
                boundaries = ["PRE_EXTERNAL_WORK"]
            elif oid == "X2":
                boundaries = ["PRE_PUSH_OR_PROMOTION"]
            elif oid == "X3":
                boundaries = ["PRE_CLOSURE"]
            path = f"{ENGINEERING}/fixture-{oid}.md"
            text = f"# {oid}\n\nSynthetic authority for proof-{oid}.\n"
            self.write(path, text)
            self.bindings["bindings"].append({
                "id": f"B-{oid}",
                "authority": {"path": path, "anchor": f"# {oid}",
                              "digest": digest(text)},
                "applies_to": {"components": [component],
                               "operations": ["diagnosis", "transition"]},
                "obligations": [{"id": f"proof-{oid}", "required_follow_up": True,
                    "scope": "R&D 002", "required_before": boundaries,
                    "proof_class": f"LEVEL_{level}", "enforcement": "HARD",
                    "required_assertions": [f"outcome-{oid}"],
                    "fresh_for_action": oid in ("C2", "X1", "X2", "X3")}],
            })
            self.obligations["obligations"].append({
                "obligation_id": oid, "binding_ref": f"B-{oid}",
                "origin_ref": f"{CHRONICLE}#audit", "scope": "R&D 002",
                "status": "OPEN", "required_before": boundaries,
                "evidence_refs": [],
            })
        self.request = {
            "mode": "resolve", "task": "Diagnose WDS identity failure.",
            "action": "WDS_DIAGNOSIS", "scope": "R&D 002", "paths": [],
            "candidate_sha": SHA, "action_id": "test-action-1",
            "station_ref": CHRONICLE, "traceability_ref": TRACE,
            "register_ref": REGISTER, "current_truth_ref": CURRENT,
            "observed_changes": [],
        }
        self.write(REGISTER, "# R&D Register\n\nR&D 002 | ACTIVE\n")
        self.write(CURRENT, f"# Current Truth\n\nR&D 002 | ACTIVE\nStation: {CHRONICLE}\n")
        self.write("modules/provider_manager.py", 'PROVIDERS = ("SEC", "FDA", "ClinicalTrials.gov")\n')
        self.flush()
        self.pin_baseline()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def dump(self, relative, value):
        self.write(relative, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def flush(self):
        self.dump(BINDINGS, self.bindings)
        self.dump(OBLIGATIONS, self.obligations)
        self.write(CHRONICLE, "# TEST ONLY Chronicle\n\n## objective\nFoundation RED.\n"
            "\n## audit\nSynthetic acceptance sample; not execution evidence.\n"
            "\n```json checkpoint-accounting\n"
            + json.dumps({"schema_version": 1, "outcomes": self.checkpoint_outcomes}, ensure_ascii=False)
            + "\n```\n"
            "\n```json station-state\n" + json.dumps(self.station, ensure_ascii=False)
            + "\n```\n")
        self.write(TRACE, "# TEST ONLY Traceability\n\n```json evidence\n"
            + json.dumps(self.evidence, ensure_ascii=False) + "\n```\n")

    def pin_baseline(self):
        baseline = {"schema_version": 1, "approval_ref": "TEST-PO-BASELINE",
            "bindings": deepcopy(self.bindings["bindings"]),
            "components": deepcopy(self.bindings["components"]),
            "obligations": deepcopy(self.obligations["obligations"])}
        self.dump(BASELINE, baseline)
        data = json.dumps(baseline, ensure_ascii=False, sort_keys=True)
        self.baseline.write_text(data, encoding="utf-8")
        self.baseline_digest = digest(data)

    def obligation(self, oid):
        return next(o for o in self.obligations["obligations"] if o["obligation_id"] == oid)

    def binding(self, bid):
        return next(b for b in self.bindings["bindings"] if b["id"] == bid)

    def satisfy(self, oid):
        """Create synthetic proof bytes + validation receipt, never real proof."""
        requirement = self.binding(f"B-{oid}")["obligations"][0]
        path = f"evidence/{oid}.txt"
        body = f"TEST ONLY proof for {oid}: outcome-{oid}\n"
        self.write(path, body)
        ref = f"E-{oid}"
        self.evidence["evidence"].append({
            "id": ref, "obligation_id": oid, "path": path, "sha256": digest(body),
            "proof_class": requirement["proof_class"], "scope": "R&D 002",
            "candidate_sha": SHA, "action_id": "test-action-1",
            "assertions": [f"outcome-{oid}"],
            "validation": {"status": "VERIFIED", "validator_ref": "TEST-VALIDATOR",
                           "evidence_sha256": digest(body)},
        })
        self.obligation(oid).update(status="CLOSED", evidence_refs=[ref])

    def satisfy_all(self):
        for oid in OBLIGATION_IDS:
            self.satisfy(oid)

    def approve(self, action):
        ref = "TEST-PO-ACTION" + (str(len(self.evidence["approvals"]))
                                  if self.evidence["approvals"] else "")
        self.evidence["approvals"].append({"id": ref,
            "issuer": "PRODUCT_OWNER", "action": action, "scope": "R&D 002",
            "candidate_sha": SHA, "action_id": "test-action-1",
            "provenance": "TEST-ONLY-TRUSTED-INPUT"})
        self.station["approval_refs"].append(ref)

    def transition(self, action="PRE_CANARY"):
        self.request.update(mode="transition", action=action)
        self.approve(action)

    def checkpoint_outcome(
        self,
        *,
        outcome_id,
        provenance_ref,
        responsibility_ref,
        status,
    ):
        record = {
            "outcome_id": outcome_id,
            "provenance_ref": provenance_ref,
            "responsibility_ref": responsibility_ref,
            "status": status,
        }
        self.checkpoint_outcomes.append(record)
        return record

    def outcome(self, kind, **kwargs):
        record = {"id": "M1", "kind": kind,
                  "classification": "UNRESOLVED_CLASSIFICATION", **kwargs}
        self.station["material_outcomes"].append(record)
        self.station["outcome_classification"] = record["classification"]
        return record

    def run(self):
        self.flush()
        self.request_path.write_text(json.dumps(self.request), encoding="utf-8")
        # Ordinary test failure, not collection error/skip/xfail or a fake SUT.
        assert SUT.is_file(), "Design C RED: approved resolver/transition guard entry point is absent"
        env = {key: value for key, value in os.environ.items()
               if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP"}}
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        result = subprocess.run([sys.executable, "-B", str(SUT),
            "--root", str(self.root), "--request", str(self.request_path),
            "--baseline", str(self.baseline), "--baseline-sha256", self.baseline_digest],
            cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8",
            timeout=15, check=False)
        assert result.returncode in (0, 2), "CLI must return a structured result, not crash"
        report = json.loads(result.stdout)
        assert report["status"] in {"RESOLVED_CONTEXT", "TRANSITION_ALLOWED",
                                     "TRANSITION_BLOCKED", "UNRESOLVED"}
        assert result.returncode == (2 if report["status"] in {
            "TRANSITION_BLOCKED", "UNRESOLVED"} else 0)
        assert "closure_pass" not in report, "Internal guard cannot grant Closure PASS"
        return report


@pytest.fixture
def case(tmp_path):
    return RepositoryCase(tmp_path)


def rejected(report, code, subject=None):
    assert report["status"] in {"TRANSITION_BLOCKED", "UNRESOLVED"}
    matches = [d for d in report["diagnostics"] if d["code"] == code]
    assert matches, f"Expected specific diagnostic {code}, got {report['diagnostics']}"
    if subject is not None:
        assert any(d["subject"] == subject for d in matches)
