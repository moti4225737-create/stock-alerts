# Chronicle — Branch, CI, Deployment and Governance Alignment

## Objective

ליישר את קו הקוד, CI, Production Deployment, Runtime validation ו־Governance כך של־Stock Sentinel יהיה מסלול סמכותי אחד מקצה לקצה ללא Escape Paths בין Local repository, GitHub, CI, Railway, Production והארכיון.

## Entry State

בתחילת השלב:

- העבודה הפעילה התבצעה על `v0.5`.
- GitHub default branch היה `main`, אך `main` הישן לא הכיל את קו הפיתוח העדכני.
- Railway Production היה מחובר ל־`v0.5`.
- CI היה מכוון ל־`v0.5`.
- Wait for CI ב־Railway לא היה חלק מוכח ממסלול ה־Production.
- Local `main` נשאר reference ישן.
- בקרות הסגירה היו מפוזרות בין Engineering, QA, Operations ו־Documentation ללא Closure Authority יחיד.

## Material Changes

### 1 — Legacy Main Forensic Review

ה־commit הייחודי של `main` הישן נבדק:

`670f0b0 — Update requirements.txt`

הוכח שהתוכן שהוסיף כבר קיים בקו `v0.5`.

### 2 — CI Alignment

CI הועבר מ־`v0.5` ל־`main`.

נוסף contract שמוודא:

- CI על `main`;
- Python `3.13.14`;
- Full Regression;
- שימוש ב־Telegram test configuration לא־סודי;
- אי־תלות ב־Production secrets שאינם נדרשים;
- `SEC_USER_AGENT` test configuration לא־סודי.

### 3 — Main History Migration

נוצר merge מבוקר ששמר את tree המאומת של קו הפיתוח החדש, תוך הכנסת היסטוריית `main` הישן כ־ancestry.

Migration commit:

`9673a67 — Unify legacy main history with authoritative code line`

נשמרו rollback tags:

- `pre-main-migration-v05`
- `legacy-main-before-migration`

המעבר ל־remote `main` בוצע ללא force-push.

### 4 — CI Production Configuration Fix

הרצת GitHub Actions על `main` חשפה פער אמיתי:

`SEC_USER_AGENT` היה נדרש ב־CI environment.

נוסף ערך test לא־סודי:

`SEC_USER_AGENT: stock-sentinel-ci-test`

Commit:

`1e063c7 — Provide deterministic SEC configuration for CI`

לאחר מכן GitHub Actions עבר בהצלחה.

### 5 — Railway Source Alignment

Railway Production הועבר מ־`v0.5` ל־`main`.

Production Deployment החדש עבר בהצלחה.

### 6 — Persistence Validation

אומת:

`NOTIFICATION_HISTORY_PATH=/data/notification_history.txt`

ה־persistent history נשמר לאורך הפריסה.

בבדיקות שנערכו:

- 107 event IDs נשמרו;
- hash של קובץ ההיסטוריה נשמר ללא שינוי לאורך המעבר.

### 7 — Least Privilege

Railway GitHub App נבדק.

הגישה מוגבלת ל־repository יחיד:

`moti4225737-create/stock-alerts`

לא ניתנה גישה ל־All repositories.

### 8 — Wait for CI Enforcement

Wait for CI הופעל ב־Railway.

בוצע verification commit ללא שינוי ב־repository tree:

`6078e39 — Verify Railway waits for CI before deployment`

נצפתה בפועל השרשרת:

Push
→ Railway `Waiting for CI`
→ GitHub Actions PASS
→ Railway Deployment
→ ACTIVE.

### 9 — Exact Production Commit Verification

מתוך Production runtime אומת:

`RAILWAY_GIT_COMMIT_SHA=6078e390b84be79cf18f5bb093ee915077f4d514`

`RAILWAY_GIT_BRANCH=main`

`RAILWAY_SERVICE_NAME=stock-alerts`

`RAILWAY_ENVIRONMENT_NAME=production`

### 10 — Runtime Validation

לאחר ה־Deployment אומתו:

- Python `3.13.14`;
- PID 1 = `python main.py`;
- deployed code markers;
- required configuration presence ללא חשיפת Secret values;
- persistent notification history;
- persistent path;
- state continuity.

### 11 — External Lifeguard

Healthchecks הציג Production Life ירוק ו־Last Ping טרי לאחר ה־Deployment.

כך הוכח:

Production work
→ Work Evidence
→ External Lifeguard.

### 12 — Local Main Escape Path

לאחר שה־remote ו־Production כבר היו מיושרים התגלה ש־local `main` עדיין מצביע ל־commit ישן:

`91a26c9`

קו העבודה המאומת נקרא עדיין:

`main-migration`

בוצע תיקון:

- local `main` הישן נשמר כ־`legacy-local-main-pre-migration`;
- `main-migration` שונה ל־`main`;
- upstream חובר ל־`origin/main`;
- SHA parity אומת;
- repository נשאר clean.

הממצא חשף פער בפרוטוקול: Remote truth לבדו אינו מספיק ללא Local authoritative branch verification.

### 13 — Governance Consolidation

הוחלט לקבע עיקרון חוקתי:

ל־Stock Sentinel יש פרוטוקול End-to-End סמכותי יחיד לשינוי, אימות, מסירה וסגירה.

המימוש המלא נמצא בענף 03 — ניהול הפיתוח ההנדסי.

Quality Gates, Documentation Checkpoints, Maturity Gates ובקרות אחרות נשארות בבתי הסמכות המקצועיים שלהן, אך אינן Closure Authorities עצמאיים.

כל בקרה חדשה השייכת לכלל חייבת להיכנס לתוך הפרוטוקול במקום להפוך למסלול סמכות מקביל.

## Decisions and Rationale

### Main as Authoritative Branch

`main` נבחר כקו הקוד הסמכותי כדי ליישר:

Local development
→ GitHub default branch
→ CI
→ Railway Production.

### Preserve Legacy History

היסטוריית `main` הישנה לא נמחקה ולא נדרסה ב־force-push.

היא נשמרה כחלק מה־ancestry של קו הקוד החדש.

### Wait for CI

הפעלת Toggle בלבד לא נחשבה הוכחה.

נדרשה הוכחת enforcement אמיתית באמצעות commit מבוקר.

### Exact Commit Verification

Deployment successful אינו מספיק.

נדרשה הוכחה של deployed SHA מתוך Production.

### Gate Consolidation

התהליך חשף שכבות רבות שהיו נכונות כל אחת בפני עצמה, אך ללא Closure Authority יחיד.

הוחלט לאחד את הסמכות בלי לרכז בכוח את כל הפרטים:

- העיקרון בחוקה;
- ה־orchestration ההנדסי בענף 03;
- פרטי הבקרות בבתים הטבעיים שלהן.

## Validation / Results

לאורך השלב אומתו בין היתר:

- Full Regression עד 486 tests לפני verification commit;
- GitHub Actions PASS על `main`;
- remote SHA alignment;
- Railway source alignment;
- Wait for CI enforcement;
- Production deployment;
- exact deployed SHA;
- Python runtime;
- process identity;
- environment presence;
- persistent volume continuity;
- Healthchecks Work Evidence;
- local / remote branch alignment.

## Exit State

לאחר השלב:

- `main` הוא authoritative local and remote branch.
- GitHub default branch הוא `main`.
- CI פועל על `main`.
- Railway Production מחובר ל־`main`.
- Wait for CI מופעל ומאומת.
- Railway GitHub App נשאר Least Privilege.
- Production runtime ניתן לקישור ל־commit מדויק.
- Persistence אומתה.
- External Lifeguard אומת לאחר Deployment.
- Governance מאוחד תחת פרוטוקול End-to-End סמכותי יחיד.

## Follow-ups

הפרוטוקול החדש חייב לעבור את תהליך הסגירה שהוא עצמו מגדיר לפני שנכריז עליו כ־Current Governing Standard.

כל Escape Path חדש שיתגלה בעתיד ייבחן גם ברמת הפרוטוקול, ולא רק כתיקון נקודתי.