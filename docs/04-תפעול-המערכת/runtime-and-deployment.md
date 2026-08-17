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

לפני המשך הרחבת Production יש לוודא שהגישה ל־repository ולשירותים נשארת מוגבלת לפי Least Privilege.
