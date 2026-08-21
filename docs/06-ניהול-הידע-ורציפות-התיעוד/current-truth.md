# Current Truth

Current Truth הוא המצב המאומת והתקף של Stock Sentinel בנקודת הזמן הנוכחית.

הוא אינו מסמך ענק שמעתיק את כל הארכיון.

ה־Current Truth מפנה אל הבתים הסמכותיים שבהם מתועד המצב התקף של כל תחום.

## היררכיית אמת

### Constitutional Truth

חוקת Stock Sentinel מגדירה את גרעין העקרונות היציבים.

החוקה כוללת עקרון שלפיו כל שינוי מהותי כפוף לפרוטוקול End-to-End סמכותי יחיד.

### Operational Truth

הקוד, הבדיקות, CI וה־runtime קובעים מה ממומש, מאומת ופועל בפועל.

קו הקוד הסמכותי הנוכחי הוא:

`main`

Local `main`, ‏`origin/main` ו־GitHub default branch מיושרים.

Railway Production מחובר ל־`main`.

Wait for CI מופעל ואכיפתו אומתה בפועל.

### Engineering Governance Truth

ה־Closure Authority היחיד למחזור שינוי End-to-End הוא:

`../03-ניהול-הפיתוח-ההנדסי/פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`

Quality Gates, Documentation Checkpoints, Maturity Gates ובקרות אחרות הם מנגנונים פנימיים או תחומיים ואינם Closure Authorities עצמאיים.

### Product and Architecture Truth

ענפים 01–05 מתעדים את הזהות, דרישות המוצר, הארכיטקטורה, ההנדסה, התפעול והאימות המאושרים.

### Documentation Truth

ענף 06 מגדיר כיצד המידע נשמר, מתעדכן, נגיש וניתן לעקיבה.

Documentation Checkpoint הוא בקרה פנימית מחייבת בפרוטוקול הסמכותי.

### Historical Truth

ה־Chronicle מתעד כיצד ומדוע עבר המוצר ממצב אחד לאחר.

## Production Alignment — 2026-08-21

במסלול היישור האחרון אומתו:

- GitHub `main` כקו הסמכותי.
- CI על `main`.
- Railway Production source = `main`.
- Wait for CI enforcement.
- exact deployed commit verification.
- Python `3.13.14`.
- `python main.py` כ־runtime process.
- persistent notification history.
- required runtime configuration presence.
- External Lifeguard Work Evidence לאחר Deployment.
- local authoritative branch alignment.

Commit הבדיקה ששימש להוכחת Wait-for-CI וה־Production alignment:

`6078e390b84be79cf18f5bb093ee915077f4d514`

## כלל עדכון

כאשר R&D משנה את המוצר באופן מהותי, בתי ה־Current Truth הרלוונטיים מתעדכנים כחלק מ־Documentation Checkpoint של הפרוטוקול הסמכותי.

אין לעדכן מסמך רק כדי לגרום למימוש להיראות תואם לתכנון ישן.

כאשר המציאות השתנתה באופן מאושר, התיעוד מתעדכן בהתאם.