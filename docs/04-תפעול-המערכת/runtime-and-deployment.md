# Runtime ו־Deployment

מסמך זה מתאר את המצב והעקרונות התפעוליים של הרצת Stock Sentinel בסביבה חיה.

## Runtime

ה־runtime אחראי להפעיל את תהליכי Stock Sentinel לפי ה־orchestration והמדיניות שנקבעו במערכת.

הוא צריך:

- להפעיל את תהליכי האיסוף בזמן המתאים;
- לכבד publication-aware scheduling כאשר מוגדר;
- להפעיל את שרשרת העיבוד הרלוונטית;
- לשמור state נדרש;
- לאפשר מסירה לערוצים המאושרים;
- להיכשל בצורה ניתנת לזיהוי ולחקירה.

## Runtime Work Evidence

ב־Production, השלמה מוצלחת של עבודת מקור אוטונומית מחוברת למסלול Work Evidence חיצוני.

ה־runtime בונה `HealthchecksWorkEvidenceReporter` ומעביר אותו דרך שכבת ה־autonomous acquisition אל ה־coordinator.

לאחר Successful Source Execution, ה־coordinator מפעיל את ה־reporter.

כשל בהרצת המקור אינו מייצר Success Evidence.

כשל בדיווח ה־Work Evidence אינו מבטל עבודת מקור שכבר הושלמה בהצלחה; הכשל נשמר כאזהרה תפעולית.

## Configuration

כתובת ה־External Lifeguard מוזרקת בזמן Runtime באמצעות:

`LIFEGUARD_PING_URL`

הערך עצמו הוא Secret ואינו נשמר בקוד, ב־Git או בתיעוד.

חסרון של configuration נדרש מונע בנייה תקינה של Production runtime כאשר הרכיב תלוי בו.

## Persistent State

`NotificationHistory` משתמש ב־Production בנתיב:

`/data/notification_history.txt`

באמצעות:

`NOTIFICATION_HISTORY_PATH`

הנתיב נמצא על Railway persistent volume.

Persistence חייבת להיבדק לאחר Deployment כאשר שינוי עשוי להשפיע על state continuity.

## Authoritative Branch

קו הקוד הסמכותי הנוכחי הוא:

`main`

`main` הוא ה־default branch ב־GitHub ומשמש מקור הקוד של Railway Production.

Branch migration אינו נחשב סגור עד שגם local authoritative branch, upstream, remote SHA ו־repository cleanliness מיושרים.

## CI

GitHub Actions מפעיל Stock Sentinel CI על:

- push ל־`main`;
- pull request ל־`main`;
- workflow dispatch.

CI משתמש ב־Python `3.13.14`.

Configuration בדיקה לא־סודי משמש במקום Production secrets כאשר הבדיקות דורשות import/runtime configuration.

## Railway Production

Railway הוא סביבת ה־Production הפעילה.

Source repository:

`moti4225737-create/stock-alerts`

Production branch:

`main`

Auto Deploy:

Enabled.

Wait for CI:

Enabled.

ההתנהגות אומתה בפועל:

Push to main
→ Railway Waiting for CI
→ GitHub Actions PASS
→ Railway Deployment.

## Exact Deployment Verification

Deployment successful אינו מספיק.

בכל Validation רלוונטי יש להוכיח שה־Production הפעיל מבוסס על ה־commit המאושר.

בבדיקת האכיפה שבוצעה ב־2026-08-21 אומת מתוך Production:

`RAILWAY_GIT_COMMIT_SHA=6078e390b84be79cf18f5bb093ee915077f4d514`

`RAILWAY_GIT_BRANCH=main`

`RAILWAY_SERVICE_NAME=stock-alerts`

`RAILWAY_ENVIRONMENT_NAME=production`

## Runtime Validation Evidence

לאחר Deployment של `6078e39` אומתו בפועל:

- Python `3.13.14`;
- PID 1 מריץ `python main.py`;
- wiring של `SEC_USER_AGENT`;
- wiring של `NOTIFICATION_HISTORY_PATH`;
- כל משתני ה־runtime הנדרשים היו PRESENT ללא חשיפת ערכי secrets;
- `NOTIFICATION_HISTORY_PATH=/data/notification_history.txt`;
- persistent history נשמר עם 107 רשומות;
- hash של קובץ ההיסטוריה נשמר לאורך ה־deployment.

## Least Privilege

Railway GitHub App מוגבל ל־repository:

`moti4225737-create/stock-alerts`

גישה ל־All repositories אינה מאושרת.

מערכות Deployment, CI/CD ושירותי Runtime מקבלים רק את ההרשאות הדרושות להם.

## Governing Protocol

Deployment ו־Runtime Validation הם בקרות פנימיות של:

`../03-ניהול-הפיתוח-ההנדסי/פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`

מסמך זה מתאר את האמת התפעולית של התחום ואינו Closure Authority עצמאי.

פרטי ה־Lifeguard וה־Monitoring מתועדים ב־:

`production-reliability.md`
## Automated Gate Evidence

מסלול האימות כולל שכבת Evidence אוטומטית המחברת בין ה־commit הסמכותי לבין ה־Production הפעיל.

השרשרת המחייבת היא:

Authoritative SHA
→ GitHub CI for exact SHA
→ Railway deployment for exact SHA
→ Production runtime identity
→ post-deployment Health Evidence
→ Gate verification.

המערכת אינה מסתפקת ב־Deployment successful או ב־Health status כללי.

PASS מחייב התאמה בין ה־SHA הסמכותי לבין CI ו־Production, runtime identity תקין, deployment מאומת ו־Health evidence שניתן לקשר לפריסה הרלוונטית.

מצב חסר, לא ידוע או בלתי ניתן לאימות נשאר `NOT_VERIFIED` ואינו הופך ל־PASS.

Source diagnostics נשמרים לצורכי חקירה ואינם משמשים תחליף לראיה המחייבת.

Validation מ־2026-08-23 בוצע מול commit:

`05aecca429e2dbad7f2e65240d0675dc3b86d7e3`
