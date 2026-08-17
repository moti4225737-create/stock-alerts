# 06 — זהויות מכונה ו־Secrets

Secrets הם נתוני גישה ולא תוכן תיעודי.

## כללים

- אין לשמור Secret חי בארכיון.
- אין להציג Secret בצ'אט או בפלט Terminal לצורך בדיקה רגילה.
- אין להכניס Secret ל־Source Code או Git.
- בודקים קיום, שם, Scope או Metadata בטוח במקום ערך מפורש.
- כאשר נדרש ייצוג, משתמשים ב־Masked Value כגון `********`.
- Credentials מוזרקים ממנגנון מוגן.
- יש לאפשר Rotation ו־Revocation.
- Short-Lived / Federated Identity מועדפת כאשר קיימת חלופה מתאימה.

Machine Identity מקבלת רק את היכולת הנדרשת לפעולתה.
