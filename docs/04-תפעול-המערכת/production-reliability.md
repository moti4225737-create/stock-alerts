# Production Reliability

Production Reliability מגדירה את היכולת של Stock Sentinel להמשיך לספק את פעולתו הצפויה בעולם האמיתי ולזהות כאשר הוא אינו עושה זאת.

## מצב נוכחי

External Production Lifeguard ממומש ומאומת.

Stock Sentinel מפיק Work Evidence לאחר השלמה מוצלחת של עבודת מקור אוטונומית ומדווח אותו למנטר חיצוני בלתי תלוי.

המנגנון מאפשר לזהות מבחוץ מצב שבו עבודת Production צפויה אינה מספקת את ראיית החיים הנדרשת.

## External Watchdog / Work Evidence

הזרימה הממומשת:

Successful Source Execution
→ Work Evidence
→ Healthchecks
→ External Liveness Monitoring.

כאשר ראיית העבודה הצפויה אינה מתקבלת במסגרת הזמן שהוגדרה:

External Watchdog
→ DOWN Detection
→ Independent Notification
→ Investigation.

כאשר העבודה חוזרת ומתקבלת שוב ראיית עבודה תקינה:

Work Evidence Restored
→ UP Detection
→ Recovery Notification.

## חוזה Work Evidence

- Work Evidence נשלח רק לאחר השלמה מוצלחת של עבודת מקור.
- כשל בהרצת המקור אינו מייצר Success Evidence.
- המנגנון הנוכחי מבסס זיהוי כשל חיצוני על היעדר Success Evidence צפוי.
- כשל בדיווח ה־Work Evidence אינו הופך עבודת מקור שהושלמה בהצלחה לכישלון.
- כשל בדיווח החיצוני נשמר כאזהרה תפעולית כדי לבודד את מסלול האיסוף ממסלול הניטור.

## Runtime ו־Configuration

HealthchecksWorkEvidenceReporter מחובר למסלול ה־autonomous acquisition דרך ה־coordinator.

כתובת הדיווח מוזרקת בזמן Runtime באמצעות משתנה הסביבה:

`LIFEGUARD_PING_URL`

ערך ה־URL הוא Secret ואינו נשמר בקוד או בתיעוד.

## Validation

המימוש אומת באמצעות:

- בדיקות המוכיחות ש־Successful Source Execution מייצר Work Evidence;
- בדיקה שכשל מקור אינו מייצר Success Evidence;
- בדיקת Failure Isolation כאשר דיווח ה־Lifeguard נכשל;
- בדיקות wiring דרך builder, coordinator ו־runtime;
- בדיקת reporter מול endpoint מוגדר;
- Controlled Production Death / Recovery test;
- זיהוי DOWN אמיתי לאחר היעדר Work Evidence;
- קבלת התראות עצמאיות;
- החזרת Production;
- זיהוי UP וקבלת Recovery notifications.

## סטטוס

Implemented — Production Integrated — End-to-End Validated.

External Production Lifeguard אינו חסם פתוח להמשך מסלול ה־Alpha.

## Traceability

המימוש והבדיקות עוגנו ב־commit:

`c864cd9 — Add external lifeguard work evidence`

ה־Chronicle של שלב Production Reliability ישלים במסגרת Documentation Checkpoint את התיעוד ההיסטורי של ההחלטות, ה־Validation וה־Exit State.
