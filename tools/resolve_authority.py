"""Read-only repository authority resolver and subordinate transition checker.

No network, application imports, mutation, action execution or Closure authority.
The caller must independently pin the approved baseline digest. Recorded proof
receipts are checked for consistency, not magically authenticated by this CLI.
"""
import argparse
import ast
from fnmatch import fnmatch
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


ENGINEERING = "docs/03-ניהול-הפיתוח-ההנדסי"
BINDINGS = f"{ENGINEERING}/decision-bindings.json"
OBLIGATIONS = f"{ENGINEERING}/open-obligations.json"
BASELINE = f"{ENGINEERING}/obligation-coverage-baseline.json"
BOUNDARIES = {
    "WDS_DIAGNOSIS": set(), "LOCAL_DIAGNOSIS": set(),
    "STATION_COMPLETE": set(), "FOUNDATION_GREEN": {"FOUNDATION_GREEN"},
    "PRE_COMMIT": {"PRE_COMMIT"},
    "PRE_PUSH_OR_PROMOTION": {"PRE_COMMIT", "PRE_PUSH_OR_PROMOTION"},
    "PRE_EXTERNAL_WORK": {"PRE_EXTERNAL_WORK"},
    "PRE_CANARY": {"PRE_CANARY", "PRE_PRODUCTION", "PRE_EXTERNAL_WORK", "PRE_PUSH_OR_PROMOTION"},
    "PRE_PRODUCTION": {"PRE_PRODUCTION", "PRE_CANARY", "PRE_EXTERNAL_WORK", "PRE_PUSH_OR_PROMOTION"},
    "PRE_CLOSURE": {"PRE_COMMIT", "PRE_PUSH_OR_PROMOTION", "PRE_CANARY",
                    "PRE_PRODUCTION", "PRE_EXTERNAL_WORK", "PRE_CLOSURE"},
}
PO_ACTIONS = {"PRE_COMMIT", "PRE_PUSH_OR_PROMOTION", "PRE_EXTERNAL_WORK",
              "PRE_CANARY", "PRE_PRODUCTION"}
INTERMEDIATE_GREEN = "BOUNDED_INTERMEDIATE_GREEN"


def hashed(data):
    return sha256(data).hexdigest()


def sealed(value):
    return hashed(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8"))


def effective_requirements(requirements):
    # Only an already-defined legacy default is normalized, not policy changes.
    return [{**r, "candidate_match_required": r.get(
        "candidate_match_required", r.get("fresh_for_action"))} for r in requirements]


def binding_contract(binding):
    return {**{k: v for k, v in binding.items() if k != "supersession_ref"},
            "authority": {k: v for k, v in binding.get("authority", {}).items()
                          if k != "digest"},
            "obligations": effective_requirements(binding.get("obligations", []))}


def obligation_contract(obligation):
    return {k: v for k, v in obligation.items()
            if k not in {"status", "evidence_refs", "disposition_ref"}}


def require(condition):
    if not condition:
        raise ValueError("invalid approved evolution")


class Resolver:
    def __init__(self, root, request, baseline, baseline_digest):
        self.root = Path(root).resolve()
        self.request = request
        self.baseline_path = Path(baseline)
        self.baseline_digest = baseline_digest
        self.diagnostics = []
        self.reads = {}
        self.stale_proofs = {}
        self.evolutions = {}
        self.reusable_evidence = {}

    def validate_evolutions(self, bindings, obligations, components):
        """Validate sealed PO dispositions within the existing approval trust boundary.

        Seals detect changes relative to reviewed approvals; they do not authenticate
        an approval's author. No current-action permission is derived here.
        """
        for ref, d in self.dispositions.items():
            if "evolution" not in d:
                continue
            try:
                evolution = d["evolution"]
                approval = self.approvals[d["approval_ref"]]
                before, after = d["from"], d["to"]
                require(d["kind"] == "SUPERSESSION" and before != after)
                require(sum(other.get("to") == after for other in self.dispositions.values()
                            if "evolution" in other) == 1)
                require(approval.get("issuer") == "PRODUCT_OWNER")
                require(approval.get("action") == "SUPERSESSION")
                require(approval.get("scope") == d["scope"])
                require(approval.get("provenance") and approval.get("action_id"))
                require(approval.get("disposition_sha256") == sealed(d))
                require(self.reference_exists(d["authority_ref"]))
                require(set(evolution["contracts"]) == {before, after})
                require(set(evolution["consumers"]) == {before, after})
                for bid in (before, after):
                    binding = bindings[bid]
                    require(sealed(binding_contract(binding)) == evolution["contracts"][bid])
                    if not binding.get("supersession_ref"):
                        consumers = sorted({c for name in binding["applies_to"]["components"]
                                            for c in components[name]["consumers"]})
                        require(consumers == evolution["consumers"][bid])
                    elif bid == after:
                        following = self.dispositions[binding["supersession_ref"]]
                        require(following["evolution"]["consumers"][bid]
                                == evolution["consumers"][bid])
                require(bindings[before].get("supersession_ref") == ref)
                migrations = evolution["obligations"]
                require(isinstance(migrations, list) and migrations)
                require(len({m["from"] for m in migrations}) == len(migrations))
                require(len({m["to"] for m in migrations}) == len(migrations))
                for side, bid in (("from", before), ("to", after)):
                    require({m[side] for m in migrations} == {
                        oid for oid, o in obligations.items() if o.get("binding_ref") == bid})
                for m in migrations:
                    old, new = m["from"], m["to"]
                    require(old != new and set(m["contracts"]) == {old, new})
                    for oid in (old, new):
                        require(obligations[oid]["scope"] == d["scope"])
                        require(sealed(obligation_contract(obligations[oid])) == m["contracts"][oid])
                    predecessor = obligations[old]
                    require(predecessor.get("status") == "SUPERSEDED")
                    require(predecessor.get("disposition_ref") == ref)
                    require(m["historical_status"] in {"OPEN", "CLOSED"})
                    require(predecessor.get("evidence_refs", []) == m["historical_evidence_refs"])
                    require(m["evidence_policy"] in {"REUSABLE", "RENEWAL_REQUIRED", "NOT_APPLICABLE"})
                    require(isinstance(m["reason"], str) and m["reason"].strip())
                    require(set(m["reusable_evidence"]) == set(m["historical_evidence_refs"]))
                    for eid, digest in m["reusable_evidence"].items():
                        require(sealed(self.evidence[eid]) == digest)
                    if m["evidence_policy"] == "REUSABLE":
                        require(m["reusable_evidence"] and m["historical_status"] == "CLOSED")
                self.evolutions[ref] = d
            except (AssertionError, KeyError, TypeError, ValueError, AttributeError):
                self.problem("EVOLUTION_INVALID", ref)
        # Establish all sealed links before checking receipt ancestry; JSON order
        # cannot determine whether a historical receipt has lawful provenance.
        for ref, d in list(self.evolutions.items()):
            for m in d["evolution"]["obligations"]:
                if not all(self.receipt_belongs_to(eid, m["from"], set())
                           for eid in m["historical_evidence_refs"]):
                    self.problem("EVOLUTION_INVALID", ref)
                    del self.evolutions[ref]
                    break
                if m["evidence_policy"] == "REUSABLE":
                    self.reusable_evidence[m["to"]] = {
                        eid: self.evidence[eid]["obligation_id"]
                        for eid in m["reusable_evidence"]}

    def receipt_belongs_to(self, eid, oid, seen):
        if oid in seen:
            return False
        seen.add(oid)
        if self.evidence.get(eid, {}).get("obligation_id") == oid:
            return True
        incoming = [m for d in self.evolutions.values()
                    for m in d["evolution"]["obligations"]
                    if m["to"] == oid and m["evidence_policy"] == "REUSABLE"
                    and eid in m["reusable_evidence"]]
        return (len(incoming) == 1
                and self.receipt_belongs_to(eid, incoming[0]["from"], seen))

    def problem(self, code, subject="repository"):
        item = {"code": code, "subject": subject}
        if item not in self.diagnostics:
            self.diagnostics.append(item)

    def path(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("reference outside repository")
        if any(p.startswith(".env") or p in {".git", ".tools"} for p in path.relative_to(self.root).parts):
            raise ValueError("protected reference")
        return path

    def read(self, relative):
        raw = self.path(relative).read_bytes()
        self.reads[relative] = hashed(raw)
        return raw.decode("utf-8-sig").replace("\r\n", "\n")

    def document(self, relative, code):
        try:
            data = json.loads(self.read(relative))
            if not isinstance(data, dict) or data.get("schema_version") != 1:
                raise ValueError("schema")
            return data
        except (OSError, ValueError, TypeError):
            self.problem(code, relative)
            return {}

    def block(self, relative, label, code, required=True):
        try:
            text = self.read(relative)
            blocks = re.findall(r"```json " + re.escape(label) + r"\s*\n(.*?)\n```", text, re.S)
            if not blocks and not required:
                return {}
            if len(blocks) != 1:
                raise ValueError("unique structured block required")
            data = json.loads(blocks[0])
            if data.get("schema_version") != 1:
                raise ValueError("schema")
            return data
        except (OSError, ValueError, TypeError):
            self.problem(code, relative)
            return {}

    def reference_exists(self, ref):
        try:
            path, _, anchor = ref.partition("#")
            text = self.read(path)
            return not anchor or anchor in text
        except (OSError, ValueError, AttributeError):
            return False

    def index(self, records, key, code):
        result = {}
        if not isinstance(records, list):
            self.problem("INVALID_SCHEMA")
            return result
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get(key), str):
                self.problem("INVALID_SCHEMA")
                continue
            if record[key] in result:
                self.problem(code, record[key])
            result[record[key]] = record
        return result

    def approved(self, ref, action):
        approval = self.approvals.get(ref, {})
        return (approval.get("issuer") == "PRODUCT_OWNER"
            and approval.get("action") == action
            and approval.get("scope") == self.request.get("scope")
            and approval.get("candidate_sha") == self.request.get("candidate_sha")
            and approval.get("action_id") == self.request.get("action_id")
            and bool(approval.get("provenance"))
            and ref in self.station.get("approval_refs", []))

    def disposition(self, ref, source, records, seen=None):
        seen = set() if seen is None else seen
        if source in seen:
            return False
        seen.add(source)
        d = self.dispositions.get(ref, {})
        kind = d.get("kind")
        if "evolution" in d:
            if ref not in self.evolutions:
                return False
            links = {d["from"]: d["to"]} if records is self.bindings else {
                m["from"]: m["to"] for m in d["evolution"]["obligations"]}
            target = links.get(source)
            if target not in records or target in seen:
                return False
            following = records[target].get("supersession_ref") or records[target].get("disposition_ref")
            return not following or self.disposition(following, target, records, seen)
        if (d.get("from") != source or d.get("scope") != self.request.get("scope")
                or not self.approved(d.get("approval_ref"), kind)):
            return False
        if kind == "SCOPE_CHANGE":
            return self.reference_exists(d.get("authority_ref", ""))
        target = d.get("to")
        if kind != "SUPERSESSION" or target not in records:
            return False
        if not self.reference_exists(d.get("authority_ref", "")):
            return False
        following = records[target].get("supersession_ref") or records[target].get("disposition_ref")
        return not following or self.disposition(following, target, records, seen)

    def proof_valid(self, obligation, requirement):
        oid = obligation["obligation_id"]
        refs = obligation.get("evidence_refs", [])
        if not refs:
            self.problem("EVIDENCE_MISSING", oid)
            return False
        assertions = set()
        valid = True
        changed_subjects = set()
        for ref in refs:
            e = self.evidence.get(ref, {})
            receipt = e.get("validation", {})
            try:
                raw = self.path(e["path"]).read_bytes()
                self.reads[e["path"]] = hashed(raw)
                consistent = (hashed(raw) == e.get("sha256") == receipt.get("evidence_sha256")
                    and receipt.get("status") == "VERIFIED" and bool(receipt.get("validator_ref"))
                    and e.get("obligation_id") in {
                        oid, self.reusable_evidence.get(oid, {}).get(ref, oid)}
                    and e.get("scope") == obligation.get("scope")
                    and e.get("proof_class") == requirement.get("proof_class"))
                candidate_match_required = requirement.get(
                    "candidate_match_required", requirement.get("fresh_for_action"))
                if candidate_match_required:
                    consistent = consistent and (e.get("candidate_sha") == self.request.get("candidate_sha"))
                if requirement.get("fresh_for_action"):
                    consistent = consistent and (e.get("action_id") == self.request.get("action_id"))
                if not consistent:
                    valid = False
                if receipt.get("kind") == "pytest-junit":
                    suites = ET.fromstring(raw)
                    cases = list(suites.iter("testcase"))
                    if (len(cases) < receipt.get("minimum_tests", 1)
                            or list(suites.iter("failure")) or list(suites.iter("error"))
                            or list(suites.iter("skipped"))):
                        valid = False
                for subject, expected in e.get("subject_hashes", {}).items():
                    if hashed(self.path(subject).read_bytes()) != expected:
                        changed_subjects.add(subject)
                assertions.update(e.get("assertions", []))
            except (OSError, ValueError, KeyError, TypeError, ET.ParseError):
                valid = False
        if not set(requirement.get("required_assertions", [])).issubset(assertions):
            valid = False
        if valid and changed_subjects:
            self.stale_proofs[oid] = changed_subjects
        if changed_subjects:
            valid = False
        if not valid:
            self.problem("EVIDENCE_INVALID", oid)
        return valid

    def classify_renewal(self, bindings, obligations, components):
        """Classify eligible staleness only; proof_valid still returns False."""
        if any(d["code"] not in {"EVIDENCE_INVALID", "OBLIGATION_DUE"}
               for d in self.diagnostics):
            return
        station_scope = self.station.get("change_scope_paths", [])
        if (not isinstance(station_scope, list)
                or not all(isinstance(path, str) for path in station_scope)
                or self.station.get("scope") != self.request.get("scope")
                or self.station.get("unit_status") != "ACTIVE"):
            return
        for oid, subjects in self.stale_proofs.items():
            obligation = obligations[oid]
            binding = bindings.get(obligation.get("binding_ref"), {})
            bound_components = binding.get("applies_to", {}).get("components", [])
            if (obligation.get("scope") != self.request.get("scope")
                    or not subjects.issubset(station_scope)
                    or not all(any(fnmatch(subject, pattern)
                        for name in bound_components
                        for pattern in components.get(name, {}).get("paths", []))
                        for subject in subjects)):
                continue
            for ref in self.station.get("approval_refs", []):
                approved_scope = self.approvals.get(ref, {}).get("change_scope_paths")
                if (isinstance(approved_scope, list)
                        and all(isinstance(path, str) for path in approved_scope)
                        and subjects.issubset(approved_scope)
                        and self.approved(ref, self.request.get("action"))):
                    for diagnostic in self.diagnostics:
                        if diagnostic == {"code": "EVIDENCE_INVALID", "subject": oid}:
                            diagnostic["code"] = "RENEWAL_REQUIRED"
                    break

    def intermediate_approval(self, paths, bindings, components):
        """Validate the whole bounded request using existing approval records."""
        action = self.request.get("action")
        if self.request.get("mode") != "resolve":
            self.problem("INVALID_INPUT", "intermediate mode")
        if action in self.station.get("forbidden_actions", []):
            self.problem("ACTION_PROHIBITED", action)
        station_paths = self.station.get("change_scope_paths", [])
        requested = self.request.get("paths", [])
        if (self.station.get("unit_status") != "ACTIVE"
                or self.station.get("scope") != self.request.get("scope")
                or not isinstance(station_paths, list)
                or not all(isinstance(p, str) for p in station_paths)
                or not isinstance(requested, list) or not requested
                or not paths.issubset(station_paths)):
            self.problem("SCOPE_UNRESOLVED", "intermediate scope")
        bound_components = {name for binding in bindings.values()
                            for name in binding.get("applies_to", {}).get("components", [])}
        for path in paths:
            if not any(fnmatch(path, pattern) for name in bound_components
                       for pattern in components.get(name, {}).get("paths", [])):
                self.problem("SCOPE_UNRESOLVED", path)
        for ref in self.station.get("approval_refs", []):
            approved_paths = self.approvals.get(ref, {}).get("change_scope_paths")
            if (self.approved(ref, action)
                    and isinstance(approved_paths, list)
                    and all(isinstance(p, str) for p in approved_paths)
                    and paths.issubset(approved_paths)):
                return ref
        self.problem("APPROVAL_INVALID", action)
        return None

    def resolve(self):
        if self.request.get("mode") not in {"resolve", "transition"}:
            self.problem("INVALID_INPUT", "mode")
        registry = self.document(BINDINGS, "INVALID_SCHEMA")
        obligations_doc = self.document(OBLIGATIONS, "INVALID_SCHEMA")
        baseline_current = self.document(BASELINE, "BASELINE_MISSING")
        try:
            raw = self.baseline_path.read_bytes()
            if hashed(raw) != self.baseline_digest:
                self.problem("BASELINE_INTEGRITY")
            baseline = json.loads(raw)
            if baseline.get("schema_version") != 1 or not baseline.get("approval_ref"):
                raise ValueError("baseline")
        except OSError:
            self.problem("BASELINE_MISSING")
            baseline = {}
        except (ValueError, AttributeError):
            self.problem("BASELINE_INTEGRITY")
            baseline = {}
        self.station = self.block(self.request.get("station_ref", ""), "station-state", "STATION_MISSING")
        self.checkpoint_accounting = self.block(
            self.request.get("station_ref", ""),
            "checkpoint-accounting",
            "CHECKPOINT_ACCOUNTING_INVALID",
            required=False,
        )
        records = self.block(self.request.get("traceability_ref", ""), "evidence", "EVIDENCE_MISSING")
        self.evidence = self.index(records.get("evidence", []), "id", "INVALID_SCHEMA")
        self.approvals = self.index(records.get("approvals", []), "id", "INVALID_SCHEMA")
        self.dispositions = self.index(records.get("dispositions", []), "id", "INVALID_SCHEMA")
        bindings = self.index(registry.get("bindings", []), "id", "DUPLICATE_BINDING")
        obligations = self.index(obligations_doc.get("obligations", []), "obligation_id", "INVALID_SCHEMA")
        components = registry.get("components", {})
        self.bindings = bindings
        self.validate_evolutions(bindings, obligations, components)
        for key, current in (("bindings", bindings), ("obligations", obligations)):
            id_key = "id" if key == "bindings" else "obligation_id"
            current_baseline_ids = {b.get(id_key) for b in baseline_current.get(key, [])}
            for old in baseline.get(key, []):
                old_id = old[id_key]
                if old_id not in current or old_id not in current_baseline_ids:
                    self.problem("BASELINE_COVERAGE", old_id)
                elif (key == "bindings" and current[old_id].get("supersession_ref") in self.evolutions
                      and binding_contract(old) != binding_contract(current[old_id])):
                    self.problem("BASELINE_COVERAGE", old_id)
                elif key == "obligations":
                    if (current[old_id].get("disposition_ref") in self.evolutions
                            and obligation_contract(old) != obligation_contract(current[old_id])):
                        self.problem("BASELINE_COVERAGE", old_id)
                    if (set(old["required_before"]) != set(current[old_id].get("required_before", []))
                            or any(old.get(field) != current[old_id].get(field)
                                   for field in ("scope", "binding_ref", "proof_ref"))):
                        if not self.disposition(current[old_id].get("disposition_ref"), old_id, current):
                            self.problem("BASELINE_COVERAGE", old_id)
                elif effective_requirements(old.get("obligations", [])) != effective_requirements(current[old_id].get("obligations", [])):
                    if not self.disposition(current[old_id].get("supersession_ref"), old_id, current):
                        self.problem("BASELINE_COVERAGE", old_id)
        for name, component in baseline.get("components", {}).items():
            if not set(component.get("consumers", [])).issubset(components.get(name, {}).get("consumers", [])):
                self.problem("CONSUMER_COVERAGE", name)
        paths = set(self.request.get("paths", []) + self.request.get("observed_changes", []))
        # Repository-native observable changes, limited to the approved station
        # paths. Names only: never inspect local runtime artifacts or secrets.
        watch = self.station.get("change_scope_paths", [])
        if watch and (self.root / ".git").exists():
            for command in (["git", "-c", "core.quotepath=false", "diff", "--name-only", "HEAD", "--", *watch],
                            ["git", "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard", "--", *watch]):
                result = subprocess.run(command, cwd=self.root, capture_output=True,
                    text=True, encoding="utf-8", timeout=10, check=False)
                if result.returncode:
                    self.problem("SCOPE_UNRESOLVED", "repository changes")
                else:
                    paths.update(result.stdout.splitlines())
        matched_components = set()
        for path in paths:
            matches = {name for name, c in components.items()
                       if any(fnmatch(path, pattern) for pattern in c.get("paths", []))}
            if not matches and not path.startswith("docs/"):
                self.problem("SCOPE_UNRESOLVED", path)
            matched_components.update(matches)
        # Inspect only a mapped composition surface, without importing runtime.
        manager = "modules/provider_manager.py"
        if manager in paths:
            try:
                tree = ast.parse(self.read(manager))
                providers = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROVIDERS" for t in node.targets):
                        providers.update(ast.literal_eval(node.value))
                    if isinstance(node, ast.FunctionDef) and node.name == "build_named":
                        for child in ast.walk(node):
                            if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                                providers.update(k.value for k in child.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str))
                consumers = {c for component in components.values() for c in component.get("consumers", [])}
                if not providers.issubset(consumers):
                    self.problem("CONSUMER_COVERAGE", manager)
            except (OSError, ValueError, SyntaxError):
                self.problem("CONSUMER_COVERAGE", manager)
        controls = []
        applicable_bindings = set()
        for bid, binding in bindings.items():
            supersession = binding.get("supersession_ref")
            if supersession in self.evolutions and self.disposition(supersession, bid, bindings):
                # Its sealed historical contract is retained, not reinterpreted
                # against the current text of a subsequently evolved authority.
                continue
            authority = binding.get("authority", {})
            try:
                text = self.read(authority["path"])
                if authority.get("anchor") not in text.splitlines():
                    self.problem("ANCHOR_MISSING", bid)
                if hashed(text.encode("utf-8")) != authority.get("digest"):
                    self.problem("AUTHORITY_STALE", bid)
            except (OSError, ValueError, KeyError, TypeError):
                self.problem("AUTHORITY_MISSING", bid)
                text = ""
            supersession = binding.get("supersession_ref")
            if supersession:
                if not self.disposition(supersession, bid, bindings):
                    self.problem("SUPERSESSION_INVALID", bid)
                else:
                    continue
            applies = binding.get("applies_to", {})
            scope_components = set(applies.get("components", []))
            if not paths or applies.get("always") or scope_components & matched_components:
                applicable_bindings.add(bid)
                controls.append({"id": bid, "authority": authority, "text": text,
                    "consumers": sorted({consumer for c in scope_components
                        for consumer in components.get(c, {}).get("consumers", [])}),
                    "why": "baseline context" if not paths else "mapped component / global control"})
            for requirement in binding.get("obligations", []):
                if (requirement.get("proof_class") not in {"LEVEL_1", "LEVEL_2", "LEVEL_3"}
                        or not requirement.get("required_assertions")
                        or not requirement.get("required_before")
                        or not set(requirement["required_before"]).issubset(BOUNDARIES)
                        or ("candidate_match_required" in requirement
                            and type(requirement["candidate_match_required"]) is not bool)):
                    self.problem("INVALID_SCHEMA", bid)
                if requirement.get("required_follow_up") and requirement.get("scope") == self.request.get("scope"):
                    if not any(o.get("binding_ref") == bid and o.get("scope") == requirement["scope"] for o in obligations.values()):
                        self.problem("OBLIGATION_COVERAGE", bid)
        action = self.request.get("action")
        if self.request.get("mode") == "transition" and action in self.station.get("forbidden_actions", []):
            self.problem("ACTION_PROHIBITED", action)
        intermediate = action == INTERMEDIATE_GREEN
        reached = set() if intermediate else BOUNDARIES.get(action)
        if reached is None:
            self.problem("SCOPE_UNRESOLVED", str(action))
            reached = set()
        for oid, obligation in obligations.items():
            binding = bindings.get(obligation.get("binding_ref"))
            if binding is None:
                self.problem("ORPHANED_OBLIGATION", oid)
                continue
            requirements = binding.get("obligations", [])
            requirement = next((r for r in requirements if r.get("id") == obligation.get("proof_ref")), None)
            if requirement is None and len(requirements) == 1:
                requirement = requirements[0]
            if requirement is None:
                self.problem("ORPHANED_OBLIGATION", oid)
                continue
            if set(obligation.get("required_before", [])) != set(requirement.get("required_before", [])):
                self.problem("OBLIGATION_COVERAGE", oid)
            consumed = (self.request.get("mode") == "transition"
                        and obligation.get("scope") == self.request.get("scope")
                        and bool(reached.intersection(obligation.get("required_before", []))))
            proof_relevant = (consumed if self.request.get("mode") == "transition"
                              else obligation.get("binding_ref") in applicable_bindings)
            status = obligation.get("status")
            satisfied = False
            if status == "CLOSED":
                satisfied = (self.proof_valid(obligation, requirement)
                             if proof_relevant else True)
            elif status in {"SUPERSEDED", "NOT_APPLICABLE"}:
                satisfied = self.disposition(obligation.get("disposition_ref"), oid, obligations)
                if not satisfied:
                    self.problem("DISPOSITION_INVALID", oid)
            elif status != "OPEN":
                self.problem("INVALID_SCHEMA", oid)
            if consumed and not satisfied:
                self.problem("OBLIGATION_DUE", oid)
        self.continuity(obligations)
        self.persistence(obligations, paths)
        if self.request.get("mode") == "transition" and action in PO_ACTIONS:
            refs = self.station.get("approval_refs", [])
            if not refs:
                self.problem("APPROVAL_REQUIRED", action)
            elif not any(self.approved(ref, action) for ref in refs):
                self.problem("APPROVAL_INVALID", action)
        approval_ref = (self.intermediate_approval(paths, bindings, components)
                        if intermediate else None)
        snapshot = hashed(json.dumps(self.reads, sort_keys=True).encode())
        if self.request.get("expected_snapshot") not in (None, snapshot):
            self.problem("SNAPSHOT_CHANGED")
        self.classify_renewal(bindings, obligations, components)
        status = "TRANSITION_ALLOWED" if self.request.get("mode") == "transition" else "RESOLVED_CONTEXT"
        if self.diagnostics:
            status = "TRANSITION_BLOCKED" if self.request.get("mode") == "transition" else "UNRESOLVED"
        permission = None
        if intermediate:
            permitted = (approval_ref is not None
                         and self.request.get("mode") == "resolve"
                         and all(d["code"] == "RENEWAL_REQUIRED" for d in self.diagnostics))
            status = "RESOLVED_CONTEXT" if permitted else "UNRESOLVED"
            permission = {"action": action, "action_id": self.request.get("action_id"),
                          "permission": "PERMITTED" if permitted else "BLOCKED",
                          "approval_ref": approval_ref}
        result = {"status": status, "diagnostics": self.diagnostics, "controls": controls,
            "obligations": list(obligations.values()), "station": {**self.station,
                "alignment": "VERIFIED" if not self.diagnostics else "NOT VERIFIED"},
            "material_outcomes": self.station.get("material_outcomes", []),
            "checkpoint_outcomes": self.checkpoint_accounting.get("outcomes", []),
            "snapshot": snapshot,
            "enforcement_limit": "Read-only check; invocation and real approval/proof provenance require trusted caller/review."}
        if intermediate:
            result["intermediate_execution"] = permission
        return result

    def continuity(self, obligations):
        unit = self.station.get("unit_id")
        for key in ("register_ref", "current_truth_ref"):
            try:
                text = self.read(self.request[key])
                rows = [line for line in text.splitlines() if unit and unit in line and "|" in line]
                if not rows or any("NEXT" in row for row in rows):
                    self.problem("CONTINUITY_CONFLICT", key)
            except (OSError, ValueError, KeyError):
                self.problem("CONTINUITY_CONFLICT", key)
        snapshot = self.station.get("obligation_snapshot")
        if snapshot is not None:
            open_ids = sorted(oid for oid, o in obligations.items() if o.get("status") == "OPEN")
            if (sorted(snapshot.get("open_ids", [])) != open_ids
                    or snapshot.get("register_digest") != self.reads.get(OBLIGATIONS)):
                self.problem("STATION_DRIFT")

    def traceability_artifacts(self, reference):
        """Read explicit durable-copy links in one referenced record only."""
        if not isinstance(reference, str):
            return set()
        document, separator, anchor = reference.partition("#")
        if (not separator or not anchor
                or document != self.request.get("traceability_ref")):
            return set()
        try:
            lines = self.read(document).splitlines()
            # Fenced examples are not authoritative record headings or links.
            fence = None
            for index, line in enumerate(lines):
                marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
                if fence:
                    if re.fullmatch(r"\s{0,3}" + re.escape(fence[0])
                                    + "{" + str(len(fence)) + r",}\s*", line):
                        fence = None
                    lines[index] = ""
                elif marker:
                    fence = marker[1]
                    lines[index] = ""
            headings = [(index, match[1]) for index, line in enumerate(lines)
                        if (match := re.fullmatch(r"#{1,6} (.+)", line))]
            starts = [index for index, title in headings if title == anchor]
            if len(starts) != 1:
                return set()
            start = starts[0]
            end = next((index for index, _ in headings if index > start), len(lines))
            artifacts = set()
            index = start + 1
            while index < end:
                if not re.fullmatch(r"Durable copies(?: \([^\n]*\))?:", lines[index]):
                    index += 1
                    continue
                index += 1
                while index + 1 < end:
                    link = re.fullmatch(r"- \[[^\[\]\n]+\]\(([^\s()]+)\);", lines[index])
                    digest = re.fullmatch(r"  SHA256 [0-9a-fA-F]{64}\.", lines[index + 1])
                    if not link or not digest:
                        break
                    target = link[1]
                    if not any(char in target for char in (":", "#", "?", "\\")) and not target.startswith("/"):
                        try:
                            path = self.path(str(Path(document).parent / target))
                            if path.is_file():
                                artifacts.add(path.relative_to(self.root).as_posix())
                        except (OSError, ValueError):
                            pass
                    index += 2
            return artifacts
        except (OSError, ValueError):
            return set()

    def persistence(self, obligations, paths):
        outcomes = self.station.get("material_outcomes", [])
        persisted_paths = set()
        for outcome in outcomes:
            oid = outcome.get("id", "outcome")
            if outcome.get("classification") != "CLASSIFIED_AND_PERSISTED":
                self.problem("UNRESOLVED_CLASSIFICATION", oid)
                continue
            persisted_paths.update(self.traceability_artifacts(outcome.get("traceability_ref")))
            kind = outcome.get("kind")
            if kind == "CARRIED_FOLLOW_UP":
                if outcome.get("obligation_ref") not in obligations:
                    self.problem("OBLIGATION_COVERAGE", oid)
            elif kind == "PROOF_EVIDENCE":
                obligation = obligations.get(outcome.get("obligation_ref"), {})
                if (outcome.get("evidence_ref") not in obligation.get("evidence_refs", [])
                        or outcome.get("evidence_ref") not in self.evidence
                        or not self.reference_exists(outcome.get("traceability_ref", ""))):
                    self.problem("EVIDENCE_NOT_LINKED", oid)
                for key in ("traceability_ref", "artifact_ref"):
                    if outcome.get(key):
                        persisted_paths.add(outcome[key].split("#")[0])
            else:
                reference = outcome.get("authority_ref") or outcome.get("persistence_ref")
                if not reference or not self.reference_exists(reference):
                    self.problem("PERSISTENCE_MISSING", oid)
                else:
                    persisted_paths.add(reference.split("#")[0])
        dispositions = self.station.get("artifact_dispositions", {})
        historical_paths = {
            path for path, disposition in dispositions.items()
            if isinstance(path, str) and path.startswith("docs/")
            and disposition in (
                "HISTORICAL_PROVENANCE_UNRESOLVED",
                "HISTORICAL_PROVENANCE_PROVEN_NOT_ACTIVE_PERSISTENCE",
            )
        } if isinstance(dispositions, dict) else set()
        for path in paths:
            if (path.startswith("docs/") and path not in persisted_paths
                    and path not in historical_paths):
                self.problem("UNCLASSIFIED_CHANGE", path)
        if outcomes and self.station.get("outcome_classification") == "NO_MATERIAL_OUTCOME":
            self.problem("UNRESOLVED_CLASSIFICATION")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--action")
    parser.add_argument("--mode", choices=("resolve", "transition"))
    args = parser.parse_args()
    try:
        request_text = Path(args.request).read_text(encoding="utf-8-sig")
        if Path(args.request).suffix == ".md":
            blocks = re.findall(r"```json station-state\s*\n(.*?)\n```", request_text, re.S)
            if len(blocks) != 1:
                raise ValueError("one station block required")
            request = json.loads(blocks[0])["resolver_request"]
        else:
            request = json.loads(request_text)
        if args.action:
            request["action"] = args.action
        if args.mode:
            request["mode"] = args.mode
        result = Resolver(args.root, request, args.baseline, args.baseline_sha256).resolve()
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        result = {"status": "UNRESOLVED", "diagnostics": [{"code": "INVALID_INPUT", "subject": "request or repository"}]}
    if args.format == "text":
        print(result["status"])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 2 if result["status"] in {"UNRESOLVED", "TRANSITION_BLOCKED"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
