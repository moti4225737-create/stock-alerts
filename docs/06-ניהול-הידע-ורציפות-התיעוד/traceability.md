# Traceability — עקיבות

מטרת ה־Traceability היא לאפשר להבין לא רק מה נכון כיום אלא גם מאין הגיע השינוי וכיצד אומת.

## שרשרת עקיבות

כאשר רלוונטי יש לאפשר מעבר בין:

Product Requirement
→ Decision
→ Architecture / Domain Contract
→ Implementation
→ Tests / Validation
→ Documentation
→ Commit / Tag / PR
→ Chronicle.

## Repository History

Git הוא חלק ממנגנון ההיסטוריה ולא תחליף ל־Chronicle.

Commit מתעד שינוי בקבצים.
ה־Chronicle מתעד את ההקשר, המטרה, ההחלטות והמשמעות.

שניהם יחד מאפשרים שחזור מקצועי של התפתחות המוצר.

## עיקרון

אין ליצור Traceability לשם בירוקרטיה.

רמת העקיבות צריכה להספיק כדי שאדם מוסמך שאינו תלוי בזיכרון המייסד או הארכיטקט יוכל להבין את מצב המוצר ואת השינויים המהותיים שעבר.

## Live Runtime Identity and User Control Surface — 2026-08-24

Product Owner Decisions:

- אושר חוזה נתונים מינימלי ל־future Live Runtime Identity HTTPS challenge-response;
- אושרה דרישת שתי תצפיות fresh ו־nonce-bound בתוך ה־Gate הסמכותי היחיד;
- נשמרה הפרדה מחייבת בין Runtime Identity לבין Healthchecks Work / Liveness Evidence;
- אושרה הנחת single-replica עם Evolution Trigger מחייב לפני scaling;
- User Control Surface עוגן כ־Product Capability ללא בחירת טכנולוגיית UI וללא פתיחת Sprint מימוש.

Natural Homes:

- Product identity: `../02-ספר-המוצר/02.02-הגדרת-המוצר.md`;
- Product requirements: `../02-ספר-המוצר/02.03-דרישות-המוצר.md`;
- Runtime contract and current implementation state: `../04-תפעול-המערכת/runtime-and-deployment.md`;
- single Closure Authority and internal Gate requirement: `../03-ניהול-הפיתוח-ההנדסי/פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`;
- future triggers: `../03-ניהול-הפיתוח-ההנדסי/evolution-register.md`;
- current state: `current-truth.md`;
- additive history: `chronicle/ספרינטים/2026-08-24-live-runtime-identity-and-user-control-contracts.md`.

Implementation / Tests / Production Evidence:

- `NOT IMPLEMENTED` — אין runtime identity endpoint;
- `NOT STARTED` — אין User Control Surface implementation;
- `NOT RUN` — RED ו־runtime tests לא החלו בשלב תיעוד זה;
- `NOT CHANGED` — GitHub workflows, Railway, Healthchecks, Production, Secrets ו־external settings.

Repository Commit / PR:

- `NOT YET CREATED`; שלב זה נעצר ל־Product Owner review לפני RED או runtime implementation.

## Opening / Initialization Local Runtime Integration — 2026-09-02

Product Owner decisions and contract:

- Portfolio Truth נשאר מקור הסמכות היחיד לחברות בתיק;
- Opening הוא lifecycle עצמאי לכל holding חדש;
- הזהות המאומתת היא Sentinel-owned ומקדימה מחקר;
- המחקר מחזיר `0..10` מועמדי `fact/category/evidence` בלבד;
- החלטות Sentinel הן `VERIFIED`, ‏`REJECTED` או `UNRESOLVED`;
- runtime eligibility משתמש ב־`SourceRuntimeFactory.portfolio_provider` הקיים;
- composition מאושר: `max_output_tokens=2000`, ‏`max_document_characters=20000`,
  ‏`timeout_seconds=60`, ‏store root ‏`data/opening_state/`, credential source
  ‏`PERPLEXITY_API_KEY`, ו־SEC verification budget default ‏`None`.

Natural homes:

- architecture and active contract:
  `../02-ספר-המוצר/02.05-ארכיטקטורת-המערכת/02.05.03-תהליכים-ואינטראקציות.md`;
- current state: `current-truth.md`;
- decisions, validation and handoff:
  `chronicle/ספרינטים/2026-09-02-opening-runtime-local-e2e.md`;
- historical interrupted design record:
  `chronicle/ספרינטים/2026-08-28-opening-picture-interrupted-preservation.md`.

Implementation and tests:

- domain/application: `models/source_bootstrap_state.py`,
  `application/source_bootstrap_application.py`,
  `application/source_bootstrap_researcher.py`,
  `application/sec_source_bootstrap_acceptance_producer.py`;
- identity/providers/persistence: `modules/sec_company_identity_resolver.py`,
  `modules/perplexity_api_request_client.py`,
  `modules/perplexity_source_bootstrap_transport.py`,
  `modules/file_source_bootstrap_store.py`;
- Portfolio Truth and composition: `application/portfolio_truth_service.py`,
  `main.py`;
- focused lifecycle/runtime/E2E protection:
  `tests/test_opening_lifecycle_integration.py`,
  `tests/test_main_opening_runtime_integration.py`,
  `tests/test_source_bootstrap_restart.py`, and the focused Opening/SEC/
  Perplexity contract test modules.

Validation evidence:

- Opening Runtime Integration focused: `3 passed`;
- runtime neighborhood: `71 passed`;
- full regression before Local E2E: `801 passed`;
- controlled Local E2E: `1 passed, 3 deselected`;
- post-E2E neighborhood: `72 passed`;
- legacy test cleanup: `25 passed` focused and `72 passed` neighborhood;
- legacy Opening reference scan: `PASS`;
- final post-cleanup full regression: `802 passed in 15.41s`;
- real external activity: `NO`.

Repository / Production evidence:

- R&D unit: `R&D 001 — Opening Runtime Local E2E`;
- unit / conversation status: `CLOSED — HANDED OFF`;
- authoritative Closure Gate: `OPEN`, not `PASS`;
- local implementation commit:
  `dc9d8914cda1a31f877cd25c4ff2fe953c16f88a`;
- local continuity-protocol commit:
  `d6546e9869c79589b97e2904112868fc24341abf`;
- Push / PR / CI for this commit: `NOT RUN`;
- Production remains `OFF`; external reconnect, deployment and restart are
  `NOT APPROVED`;
- current external Railway control-plane, Auto Deploy and Wait for CI state:
  `NOT VERIFIED`;
- local evidence does not prove real Perplexity, SEC, Telegram or Production
  behavior.

Continuity:

- permanent protocol and R&D Register:
  `../03-ניהול-הפיתוח-ההנדסי/ניהול-ספרינטים.md`;
- successor: `R&D 002 — Alpha Portfolio Initial Integration`;
- successor status: `NEXT — NOT OPEN`;
- successor must acknowledge all carried R&D 001 Gate controls in its Opening
  Block / First-Minute Re-grounding before consequential work;
- carried controls retain their original Gate identities and statuses:
  external GitHub/Railway safety verification (`BLOCKED`), Forward Consequence
  Check (`BLOCKED`, previous `STOP`), approved Push (`BLOCKED`), CI on the
  authoritative pushed SHA (`BLOCKED`), local/remote SHA parity (`BLOCKED`),
  and final R&D 001 authoritative Closure Gate PASS (`OPEN`);
- late evidence must write back to the R&D 001 Chronicle/closure record,
  Register, Current Truth and Traceability, then reevaluate the same
  authoritative Gate without reopening R&D 001 implementation scope;
- no Push, deployment, Production, runtime or external permission is inherited
  through this Handoff;
- transferred work includes real portfolio onboarding, bounded canary
  activation, real Perplexity/SEC Opening proof, live Opening-to-continuous-
  operation proof, real-world flood-prevention validation and holding/company-
  specific onboarding corrections.
