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

### Live Runtime Identity — Multi-Replica Upgrade Trigger

מצב נוכחי:
חוזה Live Runtime Identity המאושר מניח Railway Production replica פעיל יחיד ושתי תצפיות nonce-bound מאותו process instance.

מצב יעד:
אם Production יפעל עם כמה replicas, חוזה הזהות יכלול authoritative replica inventory וראיית זהות חיובית עבור כל replica נדרש בלי להציג כיסוי חלקי כ־PASS.

Trigger:
לפני שמעבר ליותר מ־Production replica פעיל אחד הופך להגדרת Runtime סטנדרטית.

Validation:
החלטת Product / Architecture מאושרת, inventory סמכותי, כיסוי דטרמיניסטי של כל ה־replicas, בדיקות disagreement / partial coverage ו־Gate integration fail-closed.

סטטוס:
Evolution / Upgrade Trigger בלבד; אינו Scope של שלב המימוש הנוכחי.

### User Control Surface Technology Selection

מצב נוכחי:
User Control Surface הוא Product Capability נדרש אך טרם מומש במלואו. ה־Production runtime הוא Headless Worker ו־Telegram הוא Delivery Surface.

מצב יעד:
משטח שליטה מאושר שבאמצעותו המשתמש מתחזק Portfolio, ‏Watchlist, ‏Preferences ו־user-owned state בהתאם ל־authoritative contract.

Trigger:
לפני פתיחת Sprint למימוש User Control Surface או לבחירת Web UI, ‏Mobile App, ‏Telegram commands, ‏Broker synchronization או שילוב ביניהם.

Validation:
החלטת Product / Architecture מאושרת המכסה ownership, authentication, authorization, persistence, correction semantics, security, end-to-end interaction ו־migration של state קיים.

סטטוס:
Capability נדרש; concrete technology טרם נבחרה.

### Portfolio State Ingestion — Broker Synchronization

מצב נוכחי:
מצב ה־Portfolio אינו מחובר ל־Broker synchronization סמכותי ואינו יכול להיחשב static indefinitely.

מצב יעד:
Broker synchronization יכול להבשיל למסלול ingestion מאושר, תוך שמירת יכולת המשתמש להבין, לתקן ולשלוט במצב שבבעלותו.

Trigger:
לפני החלטה להפוך Broker data למקור Portfolio state פעיל או סמכותי.

Validation:
Contract מאושר עבור ownership, reconciliation, corrections, stale/conflicting data, access permissions, failure behavior ו־auditability.

סטטוס:
Future maturation path; אינו מבטל את דרישת User Control Surface.

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
