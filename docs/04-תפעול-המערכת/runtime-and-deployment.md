# Runtime ו־Deployment

מסמך זה מתאר את העקרונות התפעוליים של הרצת Stock Sentinel בסביבה חיה.

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

כתובת ה־External Lifeguard מוזרקת בזמן Runtime באמצעות משתנה הסביבה:

`LIFEGUARD_PING_URL`

הערך עצמו הוא Secret ואינו נשמר בקוד, ב־Git או בתיעוד.

חסרון של משתנה הסביבה הנדרש מונע בנייה תקינה של ה־Production runtime.

## Deployment

פריסה ל־Production מתבצעת רק לאחר:

- בדיקות ממוקדות;
- Full Regression;
- Review של השינוי;
- אישור Commit / Push בהתאם לנוהל;
- בדיקת Configuration ו־Secrets ללא חשיפת ערכיהם.

## Least Privilege

מערכות Deployment, CI/CD ושירותי Runtime מקבלים רק את ההרשאות הדרושות להם.

גישה למאגר, Environment או Secret אינה נגזרת מעצם היות השירות חלק מ־Stock Sentinel.

## Current Production Direction

Railway משמשת סביבת פריסה רלוונטית במסלול הנוכחי.

External Production Lifeguard מחובר ל־Production runtime באמצעות Work Evidence ו־`LIFEGUARD_PING_URL`.

לפני המשך הרחבת Production יש לוודא שהגישה ל־repository, ל־Environment ולשירותים נשארת מוגבלת לפי Least Privilege.

פרטי התנהגות ה־Lifeguard, ה־Monitoring וה־Validation מתועדים בבית הסמכותי:

`production-reliability.md`
