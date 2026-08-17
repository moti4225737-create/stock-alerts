# Production Reliability

Production Reliability מגדירה את היכולת של Stock Sentinel להמשיך לספק את פעולתו הצפויה בעולם האמיתי ולזהות כאשר הוא אינו עושה זאת.

## מצב נוכחי

נדרש לחזק את ה־Production Liveness באמצעות מנגנון בקרה חיצוני שאינו תלוי ב־Sentinel או ב־Scheduler שעליו הוא מפקח.

## External Watchdog / Heartbeat

היעד המאושר:

Runtime / Scheduled Cycle
→ Successful Cycle Completion
→ Heartbeat
→ External Watchdog.

כאשר heartbeat צפוי אינו מתקבל בזמן:

External Watchdog
→ Alert
→ Investigation.

## דרישות

- המנטר החיצוני אינו תלוי במסלול הכשל של Sentinel.
- Success heartbeat נשלח רק לאחר נקודת runtime שמייצגת מחזור אמיתי ומוצלח.
- Failure signal ייתמך כאשר הדבר מתאים.
- Credential של המנטר מנוהל כ־Secret ואינו נכתב בקוד או בארכיון.
- הכשל צריך להיות ניתן לזיהוי גם אם Sentinel עצמו אינו עולה.

## סטטוס

Required — Not Yet Implemented.

## סדר מימוש

יכולת זו היא משימת ה־R&D הראשונה לאחר סיום ספרינט הארכיון ולפני Feature חדש.

המימוש ייפתח לפי:

Impact Map
→ Proposal
→ Owner Approval
→ RED
→ Implementation
→ Validation
→ Documentation Checkpoint.
