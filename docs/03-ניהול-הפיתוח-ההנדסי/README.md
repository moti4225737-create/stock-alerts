# 03 — ניהול הפיתוח ההנדסי

ענף זה מגדיר כיצד Stock Sentinel נבנה ומשתנה באופן מבוקר.

המטרה היא לאפשר התקדמות מהירה ככל שניתן בלי לאבד נכונות, יציבות, עקיבות או שליטה בהחלטות.

## הפרוטוקול הסמכותי

הבית הסמכותי היחיד לסגירת שינוי End-to-End הוא:

`פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`

הפרוטוקול הוא ה־Orchestrator של כל מחזור השינוי:

Decision
→ Impact Map
→ Implementation
→ Validation
→ CI
→ Promotion / Deployment
→ Production Verification
→ Documentation
→ Closure.

מסמכי TDD, Change Control, Sprint Management, Quality Gates, Documentation Checkpoints, Maturity Gates ובקרות אחרות הם מנגנונים פנימיים או תחומיים.

אף אחד מהם אינו Closure Authority עצמאי.

## תחומי אחריות

- הפרוטוקול הסמכותי End-to-End.
- תהליך פיתוח מבוקר.
- TDD — RED → GREEN → REFACTOR.
- משמעת Scope ומניעת מורכבות מיותרת.
- קבלת החלטות הנדסיות.
- בקרת שינויים.
- ניהול ספרינטים.
- נוהל רציפות יחידות R&D ושיחות עבודה ו־R&D Register, בתוך
  `ניהול-ספרינטים.md`.
- שמירת יציבות מערכתית במהלך שינוי.
- ניהול התפתחות ובשלות המוצר.
- Evolution Register, Upgrade Triggers ושערי בשלות.

הפיתוח יוצר את השינוי במוצר; הארכיון מתעד ומקבע את מצבו המאומת כחלק מהפרוטוקול הסמכותי.
