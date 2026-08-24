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

## Live Runtime Identity — Approved Contract, Not Implemented

כדי להוכיח מה ה־Production process הפעיל אומר על זהותו, אושר חוזה עתידי של Minimal Read-Only HTTPS Challenge-Response שאינו נשען על Railway או GitHub control-plane evidence בלבד.

ה־public response המחייב יכלול רק:

- `schema_version`;
- full `git_commit_sha`;
- `service`, הנקרא ישירות מתוך `RAILWAY_SERVICE_NAME` של ה־process המבצע;
- `environment`, הנקרא ישירות מתוך `RAILWAY_ENVIRONMENT_NAME` של ה־process המבצע;
- `observed_at`;
- challenge בלתי צפוי שמספק ה־caller ומוחזר במדויק;
- `process_instance_nonce` אקראי, non-secret, שנוצר פעם אחת בתחילת process ונשאר יציב רק למשך חייו.

`process_instance_nonce` לא יקודד host, ‏replica, ‏PID, ‏deployment ID או infrastructure data אחר.

Railway deployment ID, ‏replica ID, ‏project ID, ‏branch, ‏PID, ‏host/container identifiers, ‏Secrets, ‏configuration ו־arbitrary environment variables אינם חלק מחייב מה־public contract הנוכחי.

ה־Gate ידרוש שתי תצפיות fresh עם challenges שונים מאותו pinned canonical Production HTTPS host, אותו SHA, אותם runtime-side service/environment ואותו `process_instance_nonce`, כאשר Healthchecks נשאר מקור נפרד ל־fresh work / liveness.

Deployment-side environment evidence ו־Runtime-side service/environment evidence הם source-specific representations. חוזה ה־Deployment-side המאומת אינו כולל טענת service אמפירית:

- ה־Railway-originated GitHub contract שאומת בפועל מחזיר `deployment.environment == "authentic-mercy / production"` וגם `deployment_status.environment == "authentic-mercy / production"`;
- ה־runtime response יקרא `environment` ישירות מתוך `RAILWAY_ENVIRONMENT_NAME` ו־`service` ישירות מתוך `RAILWAY_SERVICE_NAME`;
- `production` ו־`stock-alerts` הם ערכי ה־runtime הצפויים כעת, אך אינם empirically verified live-runtime contract values עד לקבלת התצפית האמיתית הראשונה מתוך ה־Production process;
- לאחר התצפית הראשונה, הערכים שנצפו חייבים לעבור Validation ולהיות מוקפאים ב־runtime-side contract לפני ש־PASS יכול להתאפשר.

אין לדרוש literal equality בין GitHub `deployment.environment` לבין runtime `RAILWAY_ENVIRONMENT_NAME`. אין לבצע normalization שרירותי, substring matching, fuzzy matching או inferred equivalence. כל representation נבדק מול החוזה של המקור שלו, וה־full Git SHA המדויק נשאר מפתח ה־correlation הבלתי משתנה בין שני הגבולות.

החוזה מניח replica פעיל יחיד. Multi-replica scaling הוא Trigger לפתיחה מחדש של החוזה ולהגדרת authoritative replica inventory וכיסוי מלא.

מצב מימוש נוכחי:

- החוזה אושר ברמת Documentation / Governance;
- לא קיים ולא נחשף runtime identity HTTP endpoint;
- לא הופעל Public Networking לצורך היכולת;
- לא שונו Railway, ‏GitHub Actions, ‏Healthchecks או external settings;
- מימוש ו־RED טרם החלו.

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
→ verified Railway-originated GitHub deployment_status for exact SHA
→ first fresh nonce-bound Production runtime identity observation
→ independent external evidence reads
→ second fresh nonce-bound observation from the same process instance
→ post-deployment Healthchecks Work / Liveness Evidence
→ Gate verification.

המערכת אינה מסתפקת ב־Deployment successful או ב־Health status כללי.

PASS מחייב exact full SHA equality בין CI, ‏Railway-originated deployment evidence ו־Production runtime identity; התאמת Deployment-side environment לחוזה Railway/GitHub המאומת; התאמת Runtime-side environment/service לחוזה משתני ה־runtime שאושר ולאחר תצפית ראשונה גם אומת והוקפא; שתי תצפיות runtime טריות מאותו process instance; ו־Healthchecks evidence נפרד שניתן לקשר לפריסה הרלוונטית.

מצב חסר, לא ידוע או בלתי ניתן לאימות נשאר `NOT_VERIFIED` ואינו הופך ל־PASS.

Source diagnostics נשמרים לצורכי חקירה ואינם משמשים תחליף לראיה המחייבת.

Validation מ־2026-08-23 בוצע מול commit:

`05aecca429e2dbad7f2e65240d0675dc3b86d7e3`
