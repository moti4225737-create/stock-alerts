# Traceability — עקיבות

מטרת ה־Traceability היא לאפשר להבין לא רק מה נכון כיום אלא גם מאין הגיע השינוי וכיצד אומת.

## שרשרת עקיבות

כאשר רלוונטי יש לאפשר מעבר בין:

Product Requirement
→ Decision
→ Architecture / Domain Contract
→ Implementation
→ Tests / Validation
→ Documentation
→ Commit / Tag / PR
→ Chronicle.

## Repository History

Git הוא חלק ממנגנון ההיסטוריה ולא תחליף ל־Chronicle.

Commit מתעד שינוי בקבצים.
ה־Chronicle מתעד את ההקשר, המטרה, ההחלטות והמשמעות.

שניהם יחד מאפשרים שחזור מקצועי של התפתחות המוצר.

## עיקרון

אין ליצור Traceability לשם בירוקרטיה.

רמת העקיבות צריכה להספיק כדי שאדם מוסמך שאינו תלוי בזיכרון המייסד או הארכיטקט יוכל להבין את מצב המוצר ואת השינויים המהותיים שעבר.

## Live Runtime Identity and User Control Surface — 2026-08-24

Product Owner Decisions:

- אושר חוזה נתונים מינימלי ל־future Live Runtime Identity HTTPS challenge-response;
- אושרה דרישת שתי תצפיות fresh ו־nonce-bound בתוך ה־Gate הסמכותי היחיד;
- נשמרה הפרדה מחייבת בין Runtime Identity לבין Healthchecks Work / Liveness Evidence;
- אושרה הנחת single-replica עם Evolution Trigger מחייב לפני scaling;
- User Control Surface עוגן כ־Product Capability ללא בחירת טכנולוגיית UI וללא פתיחת Sprint מימוש.

Natural Homes:

- Product identity: `../02-ספר-המוצר/02.02-הגדרת-המוצר.md`;
- Product requirements: `../02-ספר-המוצר/02.03-דרישות-המוצר.md`;
- Runtime contract and current implementation state: `../04-תפעול-המערכת/runtime-and-deployment.md`;
- single Closure Authority and internal Gate requirement: `../03-ניהול-הפיתוח-ההנדסי/פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`;
- future triggers: `../03-ניהול-הפיתוח-ההנדסי/evolution-register.md`;
- current state: `current-truth.md`;
- additive history: `chronicle/ספרינטים/2026-08-24-live-runtime-identity-and-user-control-contracts.md`.

Implementation / Tests / Production Evidence:

- `NOT IMPLEMENTED` — אין runtime identity endpoint;
- `NOT STARTED` — אין User Control Surface implementation;
- `NOT RUN` — RED ו־runtime tests לא החלו בשלב תיעוד זה;
- `NOT CHANGED` — GitHub workflows, Railway, Healthchecks, Production, Secrets ו־external settings.

Repository Commit / PR:

- `NOT YET CREATED`; שלב זה נעצר ל־Product Owner review לפני RED או runtime implementation.
