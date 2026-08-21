# Quality Gates

Quality Gate הוא מנגנון בקרת איכות פנימי שמונע משינוי להתקדם לנקודה הבאה לפני שהוכח שהוא עומד בתנאים שהוגדרו.

המונח Gate במסמך זה אינו מייצג Closure Authority עצמאי.

כל Quality Gate הוא בקרה פנימית של הפרוטוקול הסמכותי:

`../03-ניהול-הפיתוח-ההנדסי/פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`

## לפני Commit

- Targeted Tests passed.
- Full Regression passed.
- Git status reviewed.
- Relevant code reviewed.
- No unrelated modifications.
- השינוי Cohesive.
- אין Temporary Production Code.
- ה־diff מובן ותואם את ה־Scope.

## לפני Push

- Commit approved.
- Branch confirmed.
- Destination confirmed.

## לפני מעבר לסגירת ספרינט

- הערך שהוגדר לספרינט סופק.
- Scope נשמר.
- Verification עבר.
- Validation בוצע כאשר נדרש.
- Repository נמצא במצב ידוע ונקי.
- Documentation Checkpoint הושלם כאשר הוא רלוונטי.
- יתר דרישות הפרוטוקול הסמכותי ממשיכות לחול.

## עיקרון

Quality Gate אינו טקס ואינו נקודת סגירה עליונה.

מטרתו לספק הוכחת איכות בנקודה מוגדרת בתוך ה־End-to-End governing protocol.

Closure נקבע רק על ידי הפרוטוקול הסמכותי לאחר שכל הבקרות הרלוונטיות עברו.