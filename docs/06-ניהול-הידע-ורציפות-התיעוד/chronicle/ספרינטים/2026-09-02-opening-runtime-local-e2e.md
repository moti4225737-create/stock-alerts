# Chronicle — R&D 001 — Opening Runtime Local E2E

## R&D Registration

- R&D ID: `R&D 001`.
- Unit / conversation status: `CLOSED — HANDED OFF`.
- Authoritative Closure Gate: `OPEN`.
- Predecessor: none registered under the permanent R&D numbering convention.
- Successor: `R&D 002 — Alpha Portfolio Initial Integration`.
- Successor status: `NEXT — NOT OPEN`.

## Objective

להחליף את חוזה Source Bootstrap העשיר והמורשתי ב־Opening מינימלי בבעלות
Sentinel, להשלים lifecycle עצמאי לכל holding חדש, ולחבר את זכאות Opening
לגבול ה־runtime הקיים בלי לשנות את Portfolio Truth או צרכני ה־runtime.

## Entry State

- Portfolio Truth היה סמכותי ומחובר ל־runtime.
- מימוש Opening קודם היה interrupted/preserved וכלל חוזה provider עשיר מדי.
- לא היה מסלול נקי ומוכח מקצה לקצה מ־authoritative introduction עד runtime
  eligibility.
- Railway Production היה ונשאר `OFF`; חיבור חיצוני מחדש לא היה מאושר.

## Material Changes

- החוזה המורשתי נוטרל והוסר מן המסלול הפעיל, מן persistence ומן הבדיקות
  הפעילות, בלי למחוק מודלים משותפים בעלי צרכנים אחרים.
- נוצר חוזה Opening נקי: `OpeningResearchResult`, ‏`0..10`
  `OpeningFactCandidate`, ו־`OpeningFactDecision` עם disposition מפורש.
- Verified Opening ID כולל `ticker`, ‏`company_name`, ‏`CIK` ו־`exchange`
  מאותה רשומת `company_tickers_exchange.json` סמכותית של SEC.
- Perplexity מקבל זהות מאומתת כהקשר בלבד ואינו מוסמך לייצר או להעשיר
  זהות, materiality, disposition או READY.
- מנגנון SEC הקיים הותאם להוכחת מועמד Opening באמצעות discovery,
  reconstruction, finding discovery ו־evidence validation עצמאיים.
- persistence עבר לקבצים עצמאיים לכל holding באמצעות filename דטרמיניסטי
  המבוסס על SHA-256 של symbol מנורמל, ושומר `LEARNING` ו־`READY` באופן
  fail-closed.
- Portfolio Truth עוקב אחר introductions סמכותיים ומחזורי חיים פעילים.
- `main.py` מריץ Opening לכל introduction באופן עצמאי לפני יצירת ה־runtime
  ומספק view זכאי דרך `SourceRuntimeFactory.portfolio_provider` הקיים.
- downstream runtime consumers לא שונו.

## Decisions and Rationale

- Portfolio Truth נשאר סמכות החברות היחידה; runtime view הוא נגזרת ואינו
  משנה את האמת הסמכותית.
- holding חדש נכלל ב־runtime רק לאחר `READY`; כשל או `LEARNING` של holding
  אחד אינם חוסמים holding אחר.
- holdings שהיו נוכחים ברציפות נשארים זכאים ואינם עוברים Opening חדש.
- הסרה והצגה מחדש יוצרות lifecycle ו־`time_zero` חדשים; שינוי רציף בכמות או
  average cost אינו עושה זאת.
- `READY` דורש זהות מלאה, מחקר שהושלם בהצלחה, לפחות עובדה אחת `VERIFIED`,
  והחלטה מפורשת לכל מועמד. materiality אינה תנאי READY.
- ערכי composition שאושרו: `max_output_tokens=2000`,
  `max_document_characters=20000`, ‏`timeout_seconds=60`, ‏store root
  `data/opening_state/`, credential source ‏`PERPLEXITY_API_KEY`, ו־SEC
  verification budget default ‏`None`.
- לא נוספו registry, manager/coordinator, database, runtime filter class,
  Portfolio authority נוסף או orchestration framework חדש.

## Validation / Results

- Opening Runtime Integration focused: `3 passed`.
- Runtime neighborhood: `71 passed`.
- Full regression before Local E2E: `801 passed`, ללא failures או collection
  errors.
- Controlled Local E2E: `1 passed, 3 deselected`.
- Post-E2E neighborhood: `72 passed`.
- Legacy test-contract cleanup: `25 passed` focused ו־`72 passed`
  neighborhood.
- Legacy Opening reference scan: `PASS`; ההתאמות שנותרו הן הגנות שליליות
  מכוונות או מושגים משותפים ליכולות אחרות.
- Final post-cleanup full regression: `802 passed in 15.41s`.
- לא בוצעה פעילות Perplexity, SEC, OpenAI, Telegram, autonomous runtime,
  Railway או Production אמיתית.

ה־Local E2E הוכיח באמצעות doubles דטרמיניסטיים:

Accepted Portfolio Truth
→ authoritative introduction
→ Verified Opening ID
→ bounded research
→ Sentinel dispositions
→ `READY` / `LEARNING`
→ runtime eligibility.

הוא אינו מהווה הוכחה להתנהגות provider אמיתי או Production.

## Exit State / Current Truth

- Opening Runtime Integration הוא `LOCAL IMPLEMENTED / VERIFIED` בגבול
  המאושר.
- holding חדש `READY` נעשה runtime eligible.
- holding חדש `LEARNING` או failed נשאר ב־Portfolio Truth אך אינו מגיע
  ל־runtime.
- existing continuously-present holdings נשארים eligible.
- multiple introductions מבודדים זה מזה.
- `LEARNING` ו־`time_zero` המקורי שורדים restart.
- Portfolio Truth נשאר מקור החברות היחיד וצרכני ה־runtime downstream לא
  שונו.
- Production נשאר `OFF`; restart, deployment וחיבור חיצוני אינם מאושרים.
- continuous Sentinel handoff הוכח מקומית בלבד, לא ב־live operation.
- flood prevention לא הוכח בפעולה אמיתית.

## Known Limitations / Unproven External Behavior

לא הושלמו או הוכחו בספרינט זה:

- real Perplexity/SEC Opening E2E;
- initial real portfolio onboarding/configuration;
- source configuration/coverage לכל holding;
- הרחבת רשת המקורות;
- correlation/summary/presentation integration נוספת;
- Telegram Production validation;
- Railway restart או deployment;
- complete real-world Alpha proof.

## Next Phase

`Alpha Portfolio Initial Integration`.

האסטרטגיה היא activation הדרגתי בסגנון canary וב־blast radius מוגבל. כל
כשל holding-specific אמיתי יעבור diagnosis → bounded correction → regression
case, בלי redesign אוטומטי של הארכיטקטורה.

## Next-Conversation Handoff

### Repository state and change scope

- branch: `main`;
- local HEAD: `dc9d8914cda1a31f877cd25c4ff2fe953c16f88a`;
- upstream: `origin/main`;
- commit מקומי: `dc9d8914cda1a31f877cd25c4ff2fe953c16f88a — feat: integrate
  per-holding opening lifecycle into runtime`;
- continuity-protocol commit:
  `d6546e9869c79589b97e2904112868fc24341abf — docs: anchor R&D continuity protocol`;
- open-gate Handoff commit:
  `61ba9da11336a6623c4eaf68a2f55899685afaad — docs: finalize R&D 001 open-gate handoff`;
- current Pre-Commit Local HEAD:
  `61ba9da11336a6623c4eaf68a2f55899685afaad`;
- post-closure governance hardening:
  `FINAL / HANDOFF COMMIT: PENDING`;
- authoritative pushed SHA for these local commits: `NOT VERIFIED`;
- deployed SHA: not applicable while Production remains `OFF` and deployment
  is not approved;
- ה־implementation snapshot עוגן ב־commit המקומי; push ו־CI עבור commit זה
  לא בוצעו.
- היקף הייצור כולל את Portfolio Truth lifecycle, מודלי/יישומי Opening,
  Perplexity ו־SEC boundaries, per-holding store ו־composition ב־`main.py`.
- היקף הבדיקות כולל חוזי Opening/SEC/Perplexity, restart/persistence,
  lifecycle, runtime integration ו־controlled Local E2E.

### Completed architecture and contracts

- Sentinel-owned Verified Opening ID;
- bounded candidates-only research;
- explicit Sentinel dispositions;
- `LEARNING → READY` עם `time_zero` יציב;
- per-holding persistence ו־ownership fail-closed;
- authoritative introduction tracking;
- runtime eligibility דרך ה־dynamic provider הקיים בלבד.

### Safety and Production state

- לא נשמרו secrets בתיעוד או בקוד המועמד;
- Railway Production `OFF`;
- מצב `OFF` הוא ה־Current Truth המתועד; מצב Railway control plane החיצוני
  הנוכחי, Auto Deploy ו־Wait for CI הם `NOT VERIFIED` כעת;
- external reconnect, runtime start, CI, deployment ו־Production validation
  לא בוצעו ולא אושרו;
- אין להסיק מ־Local E2E על התנהגות provider אמיתי.

### Protected files and Git restrictions

אין לבצע stage של `.tools/`, ‏`.env`, ‏`.pytest_cache/`, ‏`__pycache__/`,
`*.pyc`, ‏`notification_history.production.txt`, ‏`portfolio_source.json`,
`portfolio_state.production.json`, secrets, credentials או local runtime
artifacts. אין להשתמש ב־`git add .`. stage/commit/push/CI דורשים פעולה
ואישור מפורשים לפי הפרוטוקול הסמכותי.

### Exact next action recommended

ב־`R&D 002 — Alpha Portfolio Initial Integration`: לבצע תחילה read-only
Impact Map עבור onboarding של holding אמיתי ראשון כ־canary, כולל prerequisites
של configuration והרשאות חיצוניות, failure containment ונקודת ההוכחה, בלי
להפעיל Production או שירות חיצוני. רק לאחר החלטת Product Owner מפורשת יש
לבצע חיבור אמיתי bounded.

R&D 002 מקבל בעלות מפורשת על:

- controlled initial real portfolio onboarding;
- bounded canary activation;
- real Perplexity/SEC Opening proof;
- live proof של Opening → continuous Sentinel operation;
- real-world validation של flood prevention;
- holding/company-specific onboarding problems;
- bounded corrections שהופכים ל־regression cases;
- per-holding source configuration/coverage;
- subsequent approved Alpha integration work.

אף אחד מפריטים אלה אינו נחשב מושלם או מוכח על־ידי R&D 001.

### Carried authoritative Gate controls

R&D 002 הוא ה־successor היחיד המקבל בעלות רציפות על ה־controls הבאים. הבעלות
אינה מוותרת, סוגרת, מחליפה או מסווגת אותם מחדש ואינה מעבירה הרשאה לפעולה
חיצונית כלשהי.

1. **External GitHub/Railway safety verification**
   - Gate identity: Repository and Branch Truth / Forward Consequence safety.
   - Status: `BLOCKED`.
   - Evidence earned: repository-only pre-push audit completed.
   - Reason: current Railway control-plane state is not externally verified.
   - Prerequisite: authorized external verification of GitHub/Railway state.
   - Approval/safety: PO approval required before external access or state change.

2. **Forward Consequence Check before Push**
   - Gate identity: Forward Consequence Check.
   - Status: `BLOCKED`; previous result: `STOP`.
   - Evidence earned: local chain from push through CI to possible Railway
     deployment was mapped.
   - Reason: the external safety premise remains unverified.
   - Prerequisite: complete control 1, then rerun the same check.
   - Approval/safety: no Push authority is inherited; PO approval remains required.

3. **Push of the approved local commits**
   - Gate identity: Commit and Push.
   - Status: `BLOCKED`.
   - Evidence earned: local commits
     `dc9d8914cda1a31f877cd25c4ff2fe953c16f88a` and
     `d6546e9869c79589b97e2904112868fc24341abf`, and Handoff commit
     `61ba9da11336a6623c4eaf68a2f55899685afaad` exist; the governance-hardening
     closing commit remains `PENDING`.
   - Reason: Push safety has not passed.
   - Prerequisite: controls 1–2 pass.
   - Approval/safety: explicit PO Push approval is required.

4. **CI on the authoritative pushed SHA**
   - Gate identity: CI.
   - Status: `BLOCKED`.
   - Evidence earned: local final regression is `802 passed in 15.41s`.
   - Reason: local regression is not CI evidence and no authoritative SHA was pushed.
   - Prerequisite: safe approved Push.
   - Approval/safety: CI may be triggered only through the approved safe path.

5. **Local/remote authoritative SHA parity**
   - Gate identity: Repository and Branch Truth / Final Repository Closure.
   - Status: `BLOCKED`.
   - Evidence earned: local branch and commits are known; cached remote evidence
     showed local `main` ahead before this Handoff update.
   - Reason: remote authoritative SHA and CI result are absent.
   - Prerequisite: Push, CI evidence and read-only remote parity verification.
   - Approval/safety: external access and Push require their applicable approvals.

6. **Final authoritative Closure Gate PASS for R&D 001**
   - Gate identity: Final Repository Closure under the single authoritative
     End-to-End Closure protocol.
   - Status: `OPEN`.
   - Evidence earned: R&D 001 implementation outcome and local validation passed;
     repository-cleanliness control passed with protected artifacts contained.
   - Reason: controls 1–5 remain incomplete.
   - Prerequisite: all applicable carried controls pass and final evidence is
     written back to this R&D 001 record, the Register, Current Truth and
     Traceability.
   - Approval/safety: only the authoritative Closure protocol may grant PASS.

7. **POST-CLOSURE GOVERNANCE HARDENING**
   - Gate identity: the same authoritative End-to-End Closure Gate; this is
     closure-evidence work and does not reopen R&D 001 implementation.
   - Status: `OPEN`.
   - Evidence earned: the bounded closed-loop continuity rules are documented
     locally in their existing Natural Homes and the applicable state/evidence
     records are synchronized; the working-tree change is not yet a commit, and
     presence in an Opening Block is not closure evidence.
   - Reason: its exact local commit and the corresponding Push, CI and
     local/remote SHA-parity evidence do not yet exist.
   - Prerequisite: after the governance hardening is committed locally, R&D 002
     inherits that commit as part of the authoritative local repository state
     and completes its repository/remote evidence together with controls 3–5.
   - Approval/safety: no external permission is inherited; the existing
     approval and Forward Consequence controls remain binding.

ה־Natural Homes ששונו הם נוהל רציפות יחידות R&D, נהלי העבודה המחייבים,
ה־End-to-End Closure protocol היחיד ו־`AGENTS.md` כ־Codex enforcement בלבד.
השינוי מקבע באופן כללי closed-loop continuity, ‏Accumulated Delta Sweep,
Genericity / Instance-Leak validation, re-grounding, causal reconstruction,
pre-commit continuity ו־proof levels. הוא אינו מקודד את פרטי instance זה
ככלל קבוע, אינו יוצר Gate חדש ואינו פותח מחדש את מימוש R&D 001.

Before consequential work, the R&D 002 Opening Block / First-Minute
Re-grounding must acknowledge these seven controls, their unchanged statuses
and their approval boundaries. The official Opening Block generated after
Final Re-grounding must explicitly carry `POST-CLOSURE GOVERNANCE HARDENING`
among its `OPEN`/`BLOCKED` controls and identify the inherited local commit;
including it there does not constitute closure evidence. Late completion writes
evidence back to the authoritative R&D 001 and R&D 002 records, Register,
Current Truth and Traceability under the existing late-evidence/write-back rule,
and must not reopen or expand R&D 001's completed implementation scope.

## Follow-ups

- להשלים את ה־Closure Gate של R&D 001 רק לפי הפרוטוקול הסמכותי היחיד;
  `CLOSED — HANDED OFF` אינו Gate PASS.
- לבצע push ו־CI רק לאחר אימות מצב חיצוני ואישור מפורש.
- לפתוח את `R&D 002` לפי ה־Opening Block המחייב וה־handoff לעיל.
- להשאיר Production ו־external delivery כבויים עד לאישור והוכחה נפרדים.
