# 04 — תפעול המערכת

ענף זה מתאר כיצד Stock Sentinel החי מופעל, מנוטר ונשמר במצב תפעולי תקין.

## תחומי אחריות

- Runtime ופריסה.
- הפעלה וניהול שוטף.
- ניטור ובריאות המערכת.
- זמינות, תקינות וטריות.
- טיפול בכשלים.
- התאוששות ושחזור.
- Production Reliability.

## Production Reliability — מצב נוכחי

External Production Lifeguard ממומש, מחובר ל־Production runtime ומאומת End-to-End.

השלמה מוצלחת של עבודת מקור אוטונומית מייצרת Work Evidence למנטר חיצוני בלתי תלוי. היעדר Work Evidence צפוי מאפשר זיהוי DOWN מחוץ למסלול הכשל של Sentinel, וחזרת Work Evidence מאפשרת זיהוי Recovery / UP.

יכולת זו אינה עוד פער Production Reliability פתוח ואינה משימת ה־R&D הבאה.

ה־Current Truth המפורט של היכולת נשמר ב־:

`production-reliability.md`
