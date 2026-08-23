# Stock Sentinel — Engineering Entry Point

This file is an operational entry point for contributors and engineering tools.

The authoritative product documentation is maintained under `docs/`.

## Authoritative Sources

- Constitution:
  `docs/01-יסודות-המוצר/01.01-חוקת-stock-sentinel/`

- Product and Architecture:
  `docs/02-ספר-המוצר/`

- Engineering Governance:
  `docs/03-ניהול-הפיתוח-ההנדסי/`

- Authoritative End-to-End Change and Delivery Protocol:
  `docs/03-ניהול-הפיתוח-ההנדסי/פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`

- Operations:
  `docs/04-תפעול-המערכת/`

- Quality Assurance, Verification and Validation:
  `docs/05-אבטחת-איכות-אימות-ותיקוף/`

- Documentation, Knowledge Continuity and Access Governance:
  `docs/06-ניהול-הידע-ורציפות-התיעוד/`

## Mandatory Working Rule

Before making a material architectural, domain-contract, engineering-governance, access-governance, documentation-structure, runtime, deployment, or delivery decision:

1. Follow the authoritative end-to-end protocol.
2. Determine purpose and essence.
3. Map the existing system or process end-to-end.
4. Test the normal scenario and relevant failure/abuse scenario.
5. Benchmark professional analogues when materially useful.
6. Present a reasoned proposal.
7. Obtain product-owner approval where required.
8. Implement only after the applicable approval and protocol requirements are satisfied.

## Sprint / Stage Completion

A sprint or formal stage is closed only when every applicable requirement of the authoritative protocol has passed.

Documentation Checkpoint is a mandatory subordinate control when applicable:

Current Truth
→ Chronicle
→ Traceability
→ Repository History.

It is not an independent closure authority.

Do not treat this file as a second constitution or independent source of product truth.

## Codex Controlled Autonomy

Codex is an engineering execution agent.

Within an already approved task, Codex may autonomously:

- inspect repository files and documentation;
- inspect read-only Git state;
- search and trace dependencies;
- identify producers, consumers, assemblers/orchestrators, runtime integration points, fallbacks, tests, and parallel/legacy implementations;
- prepare required Impact Maps;
- edit implementation and test files that are within the approved scope;
- create RED tests for approved behavior changes;
- implement GREEN;
- perform justified local REFACTOR that preserves the approved design/contracts;
- run focused tests;
- run relevant full regression;
- run safe static/diagnostic checks;
- inspect diffs and validation evidence;
- correct implementation mistakes without asking for approval when the correction remains fully inside the approved design and scope.

Codex should not stop for routine low-risk engineering actions already authorized by the approved task.

The purpose is to eliminate unnecessary human copy/paste execution while preserving human authority at material decision boundaries.

### Decision Boundaries

Codex must stop and request Product Owner approval before independently making or implementing a new material decision concerning:

- product scope or behavior;
- architecture;
- domain contracts;
- engineering governance;
- access governance;
- documentation hierarchy or authoritative ownership;
- runtime architecture or material runtime behavior;
- deployment strategy/configuration;
- delivery architecture or material delivery behavior;
- security policy;
- production configuration;
- external-service permissions.

Codex may analyze these matters and present evidence, alternatives, risks, and a reasoned recommendation.

It may not silently decide them.

### Scope Discipline

Remain within the approved task.

Do not expand scope merely because another cleanup, redesign, optimization, feature, or improvement is discovered.

Record unrelated findings.

Interrupt the approved task only when the discovered issue is a material blocker such as:

- crash;
- correctness defect preventing safe continuation;
- security problem;
- data-loss risk;
- material architectural contradiction;
- violation/escape path in the authoritative protocol.

Otherwise preserve the finding for later consideration and continue the approved work.

### Evidence Rule

Never invent or assume:

- repository state;
- test results;
- Git state;
- CI state;
- deployment state;
- runtime identity;
- production health;
- configuration;
- external evidence.

Distinguish clearly:

- `VERIFIED`;
- `INFERRED`;
- `NOT VERIFIED`;
- `BLOCKED`.

No required evidence means no PASS.

### Git Safety

Read-only Git inspection is allowed autonomously.

Working-tree edits inside an approved implementation task are allowed.

Unless explicitly authorized for the specific action, Codex must not:

- commit;
- push;
- merge;
- force-push;
- rewrite history;
- create, delete, or switch branches as a workaround for unexpected state;
- perform destructive reset or clean;
- discard uncommitted user work;
- change the default branch;
- change branch protection;
- modify repository permissions/settings.

Unexpected Git/repository-state mismatches must be reported rather than silently repaired.

### Production / External System Boundary

Unless explicitly approved for the specific action, Codex must not:

- deploy or redeploy Production;
- restart or stop Production;
- modify Railway configuration;
- modify production environment variables;
- modify secrets or credentials;
- modify production volumes or runtime commands;
- change monitoring destinations;
- change external-service permissions;
- make consequential GitHub repository/security configuration changes.

Production-impacting actions require explicit approval.

Repository/CI success must never be represented as proof of Production success.

### Secret Safety

Never expose, print, copy into output, commit, document, or intentionally retrieve secret values.

This includes API keys, tokens, passwords, credentials, private webhook/topic values, authentication material, and production secrets.

When checking configuration, report only states such as:

- `PRESENT`;
- `MISSING`;
- `NOT VERIFIED`;

unless the value itself is explicitly required and separately authorized.

### Architecture / Governance Containment

Do not create:

- a competing architecture without approval;
- a duplicate Source of Truth;
- a second constitution;
- a parallel closure protocol;
- another top-level Gate;
- an independent Documentation closure authority.

Stock Sentinel has one authoritative top-level End-to-End protocol.

If a new control is required and logically belongs to that governing rule, propose strengthening that existing protocol internally.

`AGENTS.md` governs Codex execution behavior only.

### Engineering Execution

For approved behavior-changing implementation, follow the applicable authoritative protocol and use the engineering sequence:

Impact Map
→ required approval
→ RED
→ GREEN
→ REFACTOR where justified
→ focused tests
→ relevant full regression
→ diff review
→ integration/closure evidence
→ applicable Documentation Checkpoint
→ authoritative protocol closure.

A passing test suite is evidence, not by itself proof of complete closure.

Do not weaken or alter a valid test merely to make implementation pass unless the approved contract itself changed.

### Technical Containment Assumption

Do not assume that behavioral instructions are the only protection.

Operate within the effective Codex sandbox and approval boundaries.

Do not attempt to bypass, weaken, escalate around, or disable sandbox, approval, filesystem, Git, or network restrictions.

If an action requires escalation beyond the current technical boundary, request approval rather than finding a workaround.

### Conservative Merge Rule

This file is a semantic superset:

HEAD governance
+ Controlled Autonomy
= one consolidated `AGENTS.md`.

When wording overlaps, consolidation is allowed only when the resulting requirement is demonstrably equal or stronger.

When uncertain, preserve both requirements rather than weaken one.

Do not introduce a new governance concept or authority.
