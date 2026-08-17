# Evolution Register — מרשם התפתחות ובשלות המוצר

ה־Evolution Register שומר יכולות שמספקות את צורכי המוצר כיום אך דורשות שדרוג כאשר Trigger מוגדר מתקיים.

כל רשומה כוללת לפחות:

- המצב הנוכחי המקובל.
- המצב המקצועי שאליו חותרים.
- Trigger מדיד לשדרוג.
- שלב / Milestone יעד.
- קריטריוני Validation לסגירת השדרוג.
- סטטוס.

## פריטים מאושרים

### External Watchdog / Heartbeat

מצב נוכחי:
Sentinel יכול לפעול ב־Production אך עדיין חסר מנגנון חיצוני עצמאי שמזהה היעדר ריצה מתוכננת כאשר Sentinel או Scheduler אינם יכולים לדווח על הכשל בעצמם.

מצב יעד:
External Watchdog / Heartbeat בלתי תלוי ב־Sentinel, שמזהה היעדר Liveness ומתריע מחוץ למסלול הכשל.

Trigger:
סיום ספרינט הארכיון הנוכחי.

יעד:
משימת ה־R&D הראשונה לאחר סיום ספרינט הארכיון ולפני Feature חדש.

Validation:
יש להוכיח שהיעדר heartbeat או ריצה צפויה מזוהה ומייצר התרעה עצמאית.

### Hard Regulatory Gate — Recommendation / Execution

מצב נוכחי:
Stock Sentinel הוא מערכת Intelligence ו־Decision Support ואינו מיועד כרגע לבצע המלצת קנייה/מכירה או הוראות Broker.

מצב יעד:
כל הרחבה עתידית לכיוון המלצות פעולה אישיות, Order Proposal או Broker Execution תתרחש רק לאחר בדיקה משפטית ורגולטורית מקצועית של השווקים הרלוונטיים.

Trigger:
לפני כל החלטת Product/R&D שמבקשת לחצות מ־Intelligence לעבר Recommendation או Execution.

Validation:
חוות דעת מקצועית מתאימה והחלטה מוצרית מאושרת לפני פתיחת מימוש.

### Alpha Value Validation → Market Validation

מצב נוכחי:
ה־Alpha נועדה להוכיח ערך למשתמש יחיד באמצעות מודיעין מדויק, מהיר, ממוקד ומבוסס מקור.

מצב יעד:
מדידה שיטתית של ערך המוצר מול האלטרנטיבה האמיתית: כלים קיימים + עבודה ידנית + AI כללי.

מדדים אפשריים:
Recall, Latency, Precision, Grounding, Correlation, Personal Relevance, Human Effort, Decision Usefulness ו־Time-to-Awareness.

Trigger:
Alpha יציבה עם מעגלי המקורות וה־Source-Grounded Summary מחוברים לפלט המעשי.

Validation:
הוכחה מצטברת שהמערכת מייצרת ערך חוזר, ולא רק הצלחה אנקדוטלית באירוע יחיד.
