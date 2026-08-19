# Chronicle — Production Reliability

## Objective

להוסיף ל־Stock Sentinel מנגנון External Production Lifeguard בלתי תלוי, שמסוגל לזהות מבחוץ מצב שבו עבודת Production צפויה אינה מספקת ראיית חיים, ולהתריע גם כאשר Sentinel עצמו אינו מסוגל לדווח על הכשל.

## Entry State

בתחילת השלב:

- ספרינט הארכיון הושלם ונקבע בו ש־External Watchdog / Heartbeat הוא פער Production Reliability פתוח.
- ה־Evolution Register הגדיר את היכולת כמשימת ה־R&D הראשונה לאחר סיום ספרינט הארכיון ולפני Feature חדש.
- `production-reliability.md` הגדיר את היכולת כ־Required — Not Yet Implemented.
- לא היה מנגנון חיצוני עצמאי שמקבל Work Evidence מתוך מסלול העבודה האמיתי של ה־Production runtime.

## Material Changes

### 1 — Work Evidence Reporter

נוסף:

`HealthchecksWorkEvidenceReporter`

ה־reporter מקבל URL מוגן דרך Runtime configuration ושולח Work Evidence למנטר החיצוני.

### 2 — Runtime Wiring

ה־Work Evidence Reporter מחובר דרך:

`main.py`
→ `build_autonomous_loop`
→ `build_autonomous_source_acquisition`
→ `AutonomousAcquisitionCoordinator`.

### 3 — Success Evidence Contract

לאחר Successful Source Execution:

Source Execution
→ Completion
→ Work Evidence Reporter
→ Healthchecks.

כשל בהרצת המקור אינו מייצר Success Evidence.

### 4 — Failure Isolation

כשל בדיווח Work Evidence אינו הופך עבודת מקור שכבר הושלמה בהצלחה לכישלון.

כשל בדיווח החיצוני נשמר כאזהרה תפעולית, כך שמסלול הניטור אינו מפיל את מסלול האיסוף.

### 5 — External Monitoring and Notification

Healthchecks משמש External Watchdog בלתי תלוי.

היעדר Work Evidence צפוי מאפשר זיהוי DOWN.

חזרת Work Evidence מאפשרת זיהוי Recovery / UP.

ההתראות נבדקו בפועל דרך הערוצים החיצוניים שהוגדרו למערכת.

## Decisions and Rationale

### Work Evidence מתוך עבודה אמיתית

הוחלט שה־Lifeguard לא יתבסס רק על Process Liveness.

Work Evidence נוצר לאחר השלמה מוצלחת של עבודת מקור אוטונומית, כדי שהאות החיצוני ישקף עבודה אמיתית של Sentinel.

### External Failure Detection

הוחלט להשתמש במנטר שאינו תלוי במסלול הכשל של Sentinel, משום שמערכת שאינה פועלת אינה יכולה להסתמך רק על עצמה כדי לדווח שהיא אינה פועלת.

### Failure Isolation

הוחלט שכשל בשירות הניטור החיצוני לא יבטל Success של עבודת מקור שכבר הושלמה.

### Secret Handling

`LIFEGUARD_PING_URL` מוזרק דרך Environment configuration.

ערך ה־Secret אינו נשמר בקוד, ב־Git או בארכיון.

## Validation / Results

המימוש עוגן ב־commit:

`c864cd9 — Add external lifeguard work evidence`

נוספו בין היתר הבדיקות:

- `test_autonomous_acquisition_life_evidence.py`
- `test_autonomous_source_acquisition_life_evidence.py`
- `test_healthchecks_work_evidence_reporter.py`
- `test_main_lifeguard_loop_wiring.py`
- `test_main_lifeguard_runtime_wiring.py`

הבדיקות הוכיחו:

- Successful Source Execution מייצר Work Evidence.
- Failed Source Execution אינו מייצר Success Evidence.
- כשל בדיווח Work Evidence אינו מפיל עבודת מקור שהושלמה.
- ה־reporter מחובר דרך builder, coordinator ו־runtime.
- `LIFEGUARD_PING_URL` מוזרק בזמן Runtime.

בוצע גם Controlled Production Death / Recovery test:

Production Running
→ Controlled Stop
→ Missing Work Evidence
→ Healthchecks DOWN
→ External Notification

ולאחר מכן:

Production Restart
→ Work Evidence Restored
→ Healthchecks UP
→ Recovery Notification.

ה־DOWN וה־UP אומתו בפועל מחוץ ל־Sentinel.

## Exit State

External Production Lifeguard:

Implemented
→ Production Integrated
→ End-to-End Validated.

Production Reliability אינו עוד חסם פתוח במסלול ה־Alpha.

ה־External Watchdog הוסר מה־Evolution Register הפעיל משום שהיכולת הושלמה ואומתה.

ה־Current Truth עודכן בבתים הסמכותיים של:

- Production Reliability;
- Monitoring / Health;
- Runtime / Deployment;
- Operations branch status.

## Follow-ups

אין Follow-up פתוח ל־Explicit Failure Signal או ל־ntfy manual push test.

בדיקת ה־ntfy הידנית שימשה Validation מוקדם של יכולת ה־push בלבד; ה־Production DOWN / UP test המאוחר יותר סיפק ראיית End-to-End חזקה יותר.

ממצא תהליכי נפרד:

ה־Documentation Checkpoint של שלב זה לא הושלם בזמן המעבר לשיחה הבאה, למרות שהנוהל המחייב כבר היה קיים.

יש לבחון בהמשך Governance Enforcement / Control Plane שיאכוף gates קריטיים במקום להסתמך רק על זיכרון או משמעת שיחה.

ממצא זה אינו פותח Scope חדש במסגרת סגירת Production Reliability הנוכחית.
