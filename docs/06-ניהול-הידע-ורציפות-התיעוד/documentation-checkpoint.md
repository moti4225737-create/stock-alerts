# Documentation Checkpoint

Documentation Checkpoint הוא בקרה פנימית מחייבת בתוך הפרוטוקול הסמכותי של Stock Sentinel.

הוא אינו Completion Authority עצמאי.

ספרינט או שלב רשמי אינם יכולים לעבור Closure ללא Documentation Checkpoint כאשר הוא רלוונטי, אך השלמת ה־Checkpoint לבדה אינה מספיקה לסגירת השינוי.

הפרוטוקול הסמכותי נמצא ב־:

`../03-ניהול-הפיתוח-ההנדסי/פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`

## 0 — Documentation Impact Map

לפני עדכון הארכיון:

- מזהים אילו בתי סמכות השתנו;
- מזהים מסמכים שהמציאות החדשה הפכה ללא מדויקים;
- מזהים כפילויות או סתירות אפשריות;
- מזהים שינוי Constitutional / Product / Architecture / Engineering / Operations / QA / Knowledge Governance;
- מזהים האם נדרש Chronicle חדש או עדכון Chronicle קיים.

אין לעדכן מסמך אקראי רק משום שקל להגיע אליו.

## 1 — Current Truth

- מעדכנים את המצב התקף בביתו הטבעי והסמכותי.
- מעדכנים מסמכים שהשינוי הפך ללא מדויקים.
- נמנעים משכפול Authoritative Content.
- אין להפוך Current Truth ליומן היסטורי.

## 2 — Chronicle

נרשמים לפחות:

- מטרת הספרינט או השלב;
- Entry State;
- שינויים מהותיים;
- החלטות ונימוקים;
- Validation ותוצאות;
- Exit State;
- Follow-ups.

## 3 — Traceability

נשמר הקשר בין:

- דרישות והחלטות;
- מסמכים;
- קוד ובדיקות;
- Commits / Tags / PRs כאשר רלוונטי;
- ראיות Validation;
- Production evidence כאשר רלוונטי.

## 4 — Evolution

יכולת שמקובלת כיום אך דורשת שדרוג עתידי אינה נשכחת.

כאשר רלוונטי היא נרשמת ב־Evolution Register עם:

- Current Acceptable State;
- Target Professional State;
- Upgrade Trigger;
- Target Milestone;
- Validation Criteria.

## 5 — Access and Disclosure

כאשר שינוי משפיע על מידע רגיש, IP, הרשאות, Secrets או חשיפה חיצונית, נבדק שהשינוי משתקף גם בממשל הגישה.

## 6 — Final Documentation Review

לפני PASS של ה־Checkpoint בודקים:

- חוסרים;
- כפילויות;
- מיקום סמכותי שגוי;
- סתירות בין בתי סמכות;
- קישורים שבורים;
- Placeholder / TODO / TEMPORARY;
- קצוות פתוחים שלא נרשמו;
- התאמה בין מצב המוצר לתיעוד;
- התאמה בין Current Truth, Chronicle והיסטוריית Repository.

## 7 — Archive Update Rule

שינוי משמעותי אינו נחשב מתועד רק משום שנוסף Chronicle.

יש לעדכן את כל בתי הסמכות שהפכו ללא מדויקים.

לעומת זאת, אין לשכפל את אותו Authoritative Content בכמה בתים.

ה־Chronicle שומר את ההיסטוריה והנימוק.

המסמך התחומי שומר את האמת המקצועית הנוכחית.

Current Truth מצביע על המצב התקף.

## Status

Documentation Checkpoint הוא חלק מהגדרת הסיום של הפרוטוקול הסמכותי.

הוא אינו Gate עליון נוסף.