# Chronicle — עצירת ספרינט Opening Picture ונקודת שימור חריגה

## מטרת הרשומה

רשומה זו משמרת את מלוא ההקשר שהוביל לעצירת ספרינט Opening Picture.

נקודת השימור אינה סגירת ספרינט ואינה אישור ארכיטקטורה.
מטרתה למנוע אובדן של עבודה, החלטות, סיבות לעצירה ופערים פתוחים,
עד להשלמת בחינה מחודשת של מבנה Stock Sentinel.

## נקודת הכניסה

לפני Opening Picture הושלם מהלך Portfolio Truth שהעביר את המערכת
לשימוש במצב תיק השקעות סמכותי ומתמשך.

שרשרת היישום המתועדת במאגר:

9b7ff99 — Add portfolio truth foundation
ed64130 — Add durable portfolio source and state
ae8030e — Add portfolio truth orchestration
2c20d19 — Migrate runtime to authoritative portfolio truth

## האירוע שהוביל לפתיחת עבודת ההגנה

לאחר חיבור תיק ההשקעות המעודכן לזרימת העבודה התפעולית אירעה
הצפת הודעות Telegram.

אירוע ההצפה עצמו מתועד בהיסטוריית העבודה התפעולית והשיחות;
המאגר לבדו אינו מוכיח את עצם האירוע, היקפו או משכו.

בעקבות האירוע נעצרו/נותקו באופן מכוון מסלולים חיצוניים רלוונטיים
כדי למנוע המשך הפצה בלתי מבוקרת בזמן הבדיקה.

Production/Railway ומעגלי ההתראה החיצוניים לא הוחזרו לפעילות
כחלק מספרינט זה.

גם עובדת הניתוק התפעולי אינה ניתנת להוכחה מתוך Git בלבד,
ולכן נשמרת כאן במפורש כחלק מההיסטוריה התפעולית.

## מטרת Opening Picture

Opening Picture נפתח כמנגנון הגנת אתחול.

המטרה הייתה למנוע מצב שבו מידע היסטורי שנקלט בעת עליית Sentinel
מזוהה בטעות כאירוע חדש ונשלח למשתמש.

המנגנון מבוסס על נקודת זמן יציבה לכל אחזקה ועל הפרדה בין:

- מידע שקדם לנקודת ההתחלה;
- מידע חדש שנקלט בזמן הלמידה;
- מעבר למצב READY;
- מסירה רגילה לאחר שהמערכת מוכנה.

Opening Picture לא נועד להפוך למוצר, שירות או מערכת עצמאית.

## התפתחות הספרינט

6294f62 — Checkpoint Opening Picture through corrective GREEN 2

נקודה זו יצרה את בסיס מחזור החיים, מצב LEARNING/READY,
סיווג מידע היסטורי/חדש, שמירת מידע חדש בזמן הלמידה
ושחזור מצב מתמשך.

2b1bcd2 — Strengthen comparative system analysis protocol

שינוי ממשל הנדסי שבוצע בין נקודות העבודה ואינו נקודת
מימוש של Opening Picture.

a03f6f4 — Checkpoint Opening Picture control through GREEN 3E

נוספו בין היתר זכאות למסירה לאחר READY, אישורי מסירה,
מעברי pending/ACK, שמירת ACK, תמונת בקרה ודרישות שלמות מצב.

## סיבת עצירת הפיתוח

במהלך חיזוק מנגנון ההגנה עלתה שאלה מהותית:

האם אנחנו עדיין בונים את מנגנון ההגנה הפשוט שנדרש,
או שאנחנו מפתחים מנגנון גדול ומורכב משום שמבנה המוצר
עצמו דורש בחינה מחודשת?

העבודה החלה לצבור מנגנוני מצב, pending, ACK, persistence,
בקרות התקדמות ומקרי התאוששות.

למרות שלחלקם קיימת הצדקה הנדסית, הצטברותם עוררה חשש
שאנחנו פותרים באופן מקומי סימפטומים במקום לבדוק את מבנה
Sentinel כמכלול.

בהתאם לעיקרון המחייב של התאמה מינימלית לבשלות הנוכחית,
הוחלט לא להמשיך אוטומטית בפיתוח.

הספרינט נעצר לצורך בחינה מוצרית ומבנית רחבה.

## שרשרת התקלה הטכנית לאחר העצירה

לאחר עצירת העבודה התרחשה שרשרת תקלות סביב סביבת העבודה המקומית,
המחשב, סביבת הפיתוח ויכולת Codex לגשת למאגר.

נדרשו שחזור ואימות מחדש של:

- המאגר המקומי;
- הענף הפעיל;
- Python;
- סביבת Codex;
- מצב הקבצים;
- נקודת HEAD;
- הקשר לענף המרוחק.

אין להסיק מהמאגר לבדו את פרטי שרשרת התקלה הזאת.
היא נשמרת ברשומה על בסיס רצף העבודה התפעולי.

לאחר השחזור אומת שהעבודה המקומית שנותרה היא מקשה אחת
הקשורה ל־Opening Picture ולא ערבוב מקרי של עבודות אחרות.

## נקודת השימור החריגה

fa95156 — Preserve interrupted Opening Picture work for architecture review

נקודה זו משמרת את העבודה שהייתה קיימת בעת עצירת הספרינט.

היא כוללת בדיוק שמונה קבצים.

השינוי מרכז את האחריות על pending observations ועל ACK
ב־OpeningPictureLifecycle / OpeningPictureState,
והופך את OpeningPictureObservationGuard למסווג חסר מצב.

נוספו גם ראיות להתקדמות משמעותית בזמן LEARNING,
בדיקת חוסר התקדמות ובדיקת גיל pending לאחר READY.

בדיקות השימור הממוקדות:

37 passed
0 failed
0 skipped

git diff --check עבר ללא שגיאות.

## פערים שנשמרו בכוונה

נקודת השימור אינה פותרת את הפערים הבאים:

1. LEARNING שמעולם לא חווה התקדמות משמעותית אינו מזוהה
   כיום על ידי evaluate_no_progress.

2. שילוב Opening Picture ב-runtime אינו מוכח.

3. persistence אוטומטי לאחר כל שינוי lifecycle אינו מוכח.

4. עקביות crash בין delivery לבין ACK אינה מוכחת.

5. regression מלא לא הורץ עבור נקודת השימור.

6. CI לא אומת עבור נקודת השימור.

7. Production לא אומת ולא הוחזר במסגרת נקודה זו.

## משמעות נקודת השימור

הנקודה:

- משמרת עבודה;
- משמרת ראיות;
- משמרת פערים;
- מאפשרת לחזור למצב המדויק אם יוחלט להמשיך ממנו.

היא אינה:

- סגירת הספרינט;
- אישור הארכיטקטורה;
- אישור Production;
- אישור שהמנגנון כולו נחוץ;
- החלטה שכל הקוד שנשמר יישאר במבנה הסופי.

## החלטת ההמשך

לפני חידוש המימוש הוחלט לחזור לרמת המוצר.

נבנתה מפת 28 נקודות לבחינת Stock Sentinel כמכלול.

לאחר סגירת החריגה הנוכחית יבוצע מעבר אופקי שני על כל 28 הנקודות,
תוך שימוש עקבי במבחני:

- מטרת Sentinel;
- מצב קיים מול מצב רצוי;
- מבצע העבודה המתאים;
- השוואה מקצועית חיצונית;
- אמינות ובטיחות תפעולית;
- התאמה ל-Alpha ועלות.

רק לאחר הקפאת החלטות ה-Alpha יבוצע Impact Map הנדסי
לפני חידוש implementation.

## עקרון הסגירה החריגה

נקודת השימור החריגה סוגרת את אי-הוודאות לגבי מה נשמר ומדוע.

היא אינה סוגרת את הספרינט.

## אירוע תפעולי לאחר נקודת השימור — 2026-08-28

לאחר עבודת השימור החריגה נדחף ל־`main` הסמכותי commit תיעוד בלבד.
ה־push הפעיל GitHub Actions CI, ובהתאם לחיבור שהיה מוגדר בין
Railway Production ל־`main`, התרחשה אחריו פריסת Production פעילה.

ה־Production worker שנפרס חזר לעיבוד מקורות אוטונומי. לוגי Railway
הראו עבודת FDA ו־ClinicalTrials.gov אוטונומית וכן אזהרת ספק SEC.
ה־runtime יצר פעילות מסירה חוזרת ל־Telegram, ו־Telegram החזיר
`HTTP 429 Too Many Requests` לצד ניסיונות חוזרים.

הראיות והדיווחים שנאספו במהלך האירוע נבדלים בעוצמתם:

- המשתמש דיווח שצפה בכ־1.7K הודעות bot שלא נקראו; היקף זה לא נספר
  באופן בלתי תלוי מתוך לוגי המערכת.
- ראיית השימוש ב־OpenAI עבור 2026-08-28 הראתה בקירוב `$8.38`,
  ‏`3,250` בקשות ו־`52,019,877` tokens. אין להסיק מכך שכל שימוש
  אוגוסט או כל דולר בתקופה נגרמו מאירוע זה.
- לוגי הבקשות של OpenAI הראו קריאות Sentinel חוזרות מסוג
  analysis/significance עד סביבות 17:20 לפי השעה המקומית.
- המשתמש דיווח ש־OpenAI automatic recharge הועבר ל־OFF; מצב זה
  לא אומת באופן בלתי תלוי במסגרת הראיות שנשמרו כאן.

Railway Production deployment הוסר ידנית. לאחר מכן Railway הראה
`Service offline`, ללא deployment פעיל, ואת ה־deployment כ־removed.
רענונים חוזרים של לוגי הבקשות של OpenAI לאחר הכיבוי לא הראו קריאות
מאוחרות מסביבות 17:20 במהלך חלון האימות שנצפה.

התאמת התזמון בין הסרת ה־Production runtime לבין עצירת זרם הבקשות
המתמשך היא ראיה סיבתית חזקה לכך שה־Railway Production runtime הפעיל
היה מקור הזרם שנצפה. זו אינה הוכחה לסיבת השורש המלאה של אלפי הבקשות,
שנשארת בלתי פתורה.

Production חייב להישאר `OFF` עד להשלמת הבקרות המתקנות של האירוע
ולאימותן המפורש. Telegram bot token שהופיע בראיות לוג תפעוליות
נחשב חשוף/compromised, ומצב החשיפה טופל ללא שמירת ערך Secret ברשומה.

## Telegram credential rotation / containment

ה־token החשוף בוטל ב־BotFather ונוצר token חלופי. `TELEGRAM_TOKEN`
החלופי נשמר ב־Railway, עודכן גם ב־`.env` המקומי וב־GitHub repository
secret. אימות מקומי אישר שהמשתנה קיים ואינו ריק בלי לחשוף את ערכו;
ב־GitHub Environment secrets אין Telegram secret נוסף.

לאחר שינוי המשתנה Railway נשאר ללא deployment פעיל, והשינוי ממתין
להחלה ב־deployment/runtime עתידי שיאושר. בדיקת tracked code מצאה
ש־`main.py` צורך `TELEGRAM_TOKEN` מן ה־environment, ‏CI משתמש במכוון
ב־`ci-test-token`, והבדיקות דורשות במפורש ש־CI לא יצרוך
`secrets.TELEGRAM_TOKEN`. לא נמצא consumer נוסף של Telegram credential
בקוד tracked.

`Telegram credential rotation / containment = COMPLETE`.

`Telegram runtime / Production validation = PENDING FUTURE APPROVED PRODUCTION RESTART`.

אין בכך אימות של Telegram delivery או שימוש ב־token החלופי ב־Production,
פתרון לסיבת השורש של alert storm, או אישור להפעלת Production מחדש.
Production נשאר `OFF` במכוון.

## ממצא התהליך ושרשרת ההשלכות

שינוי שסווג כתיעוד בלבד אינו בהכרח inert מבחינה תפעולית.

תהליך הסגירה העריך את סיכון הקוד/התוכן, אך לא עקב במידה מספקת אחר
שרשרת ההשלכות קדימה של push ל־`main`:

Documentation change
→ push to `main`
→ CI
→ Railway deployment
→ Production runtime activation
→ autonomous acquisition
→ OpenAI API activity/cost
→ Telegram delivery
→ message flood / retries.

זהו Escape Path בהערכת השלכות תפעוליות, ולא Closure Gate עצמאי חדש.

עקרון החיזוק המאושר הוא בקרה פנימית של פרוטוקול ה־End-to-End
הסמכותי הקיים: לפני פעולה שמשנה מצב, יש לעקוב אחר השלכות downstream
מהותיות רחוק מספיק כדי לזהות השפעות על Product, המשתמש, Production,
שירותים חיצוניים, עלות, אבטחה והאמת הסמכותית. לכל הפחות יש לחשוב שני
צעדים קדימה, ולהמשיך מעבר לכך כל עוד נותרות השלכות מהותיות.

עיקרון זה מחזק את הפרוטוקול הקיים ואינו יוצר Gate עליון חדש.

## בקרות אכיפה מינימליות שאושרו

1. Git pre-push hook מקומי מינימלי מומש ב־`.git/hooks/pre-push`.
   הוא מופעל רק עבור push ל־`main` ודורש אישור מפורש שנבדקו תופעות
   לוואי של Production, deployment, שירותים חיצוניים, עלות API
   והתראות. ללא push ל־`main` הוא לא יפריע. זהו Defense in Depth
   ואכיפה פנימית, לא Closure Authority ולא Gate חדש. הוא מקומי
   ובכוונה אינו tracked. מצבו `IMPLEMENTED / VERIFIED`.

   באימות עצמאי, סימולציית push לענף שאינו `main` הסתיימה בהצלחה
   ללא prompt; סימולציית push ל־`refs/heads/main` ללא האישור המדויק
   נחסמה, ועם `CONFIRM MAIN PUSH` הסתיימה בהצלחה. ללא terminal
   אינטראקטיבי push ל־`main` נכשל באופן fail-closed. בדיקת PowerShell
   עצמאית אישרה את תוכן ה־hook הפעיל: אין בו קריאות רשת, deployment,
   שאילתת שירותים חיצוניים, שינוי Secrets או שינוי מצב המאגר.
   `git diff --check` עבר, ו־`git status` הראה רק את שני מסמכי הסגירה
   כשינויים tracked; הנתיבים הבלתי־tracked המוגנים הקיימים לא שונו.

2. מילת ההפעלה האנושית `הפסקה` היא כלל תפעולי מאושר. במהלך עבודה
   פעילה היא מחייבת גידור מחדש מיידי מול הפרוטוקול/מקור האמת
   הסמכותי, יעד ומצב הספרינט הנוכחי, אישורים, פעולות אסורות,
   חיבורים/תופעות לוואי חיצוניים והתאמת הפעולה הבאה. תוצאת התגובה
   תהיה תמציתית: `גידור מחדש — PASS` או `גידור מחדש — STOP`.
   זו בקרת interaction/enforcement מעשית, לא Gate ולא רכיב ארכיטקטורה.

## פערי המשך פתוחים — לא נפתרו בצעד התיעוד

- סיבת השורש של אלפי בקשות OpenAI;
- התנהגות acquisition/reprocessing/dedup/cache;
- יצירת alert storm;
- התנהגות Telegram retry ו־delivery ACK;
- auto-deploy לא רצוי של Production מ־`main`;
- Alpha API cost guard / הגנת הוצאה נאכפת;
- Telegram runtime / Production validation בהפעלה עתידית מאושרת;
- סמנטיקת expected state עבור monitoring כאשר Production כבוי במכוון.

פערים אלה הם פריטי follow-up בלתי פתורים. הם אינם מימוש במסגרת
צעד תיעוד זה ואינם משנים את מצב Opening Picture:
`INTERRUPTED / PRESERVED`.

## Exit State — סגירת התחנה החריגה

- Opening Picture נשאר `INTERRUPTED / PRESERVED`; נקודת השימור
  `fa95156a0b6c8633bf5cc0a9e14057cafaeb24d1` קיימת ונשארת עוגן
  השימור הסמכותי.
- האירוע התפעולי של 2026-08-28 מתועד ברשומה זו.
- Railway Production הוא `OFF` במכוון, אין deployment פעיל,
  והפעלת Production מחדש אינה מאושרת.
- Forward Consequence Check נוסף לפרוטוקול ה־End-to-End הסמכותי
  היחיד כבקרה פנימית קיימת־סמכות, לא כ־Gate חדש.
- local main pre-push confirmation hook הוא `IMPLEMENTED / VERIFIED`
  כ־Defense in Depth.
- `Telegram credential rotation / containment = COMPLETE`.
- `Telegram runtime / Production validation = PENDING FUTURE APPROVED PRODUCTION RESTART`.
- סיבת השורש של alert storm / ריבוי בקשות OpenAI היא `NOT SOLVED`
  ונשארת follow-up.
- אין חידוש של מימוש Opening Picture בתחנה זו.

רצף המוצר הבא לאחר סגירת התחנה החריגה נשאר:

second horizontal review of all 28 product sections
→ Alpha decision freeze
→ approved implementation Impact Map
→ only then implementation.

סיווג הסגירה מדויק: סגירה זו סוגרת את תחנת השימור / ההתאוששות
החריגה ואת ה־operational containment המתועד שלה. היא אינה מכריזה
על ספרינט Opening Picture שנקטע כ־`COMPLETE`, אינה מאשרת הפעלת
Production מחדש ואינה סוגרת את עבודת סיבת השורש הבלתי פתורה.

## Documentation Checkpoint Self-Check

שני מסמכי התחנה מכסים כעת:

- Objective — מטרת השימור והסגירה החריגה;
- Entry State — מצב Portfolio Truth, ‏Opening Picture והעצירה;
- Material Changes — נקודת השימור, תיעוד האירוע ובקרות ה־containment;
- Decisions / Rationale — סיבת העצירה וחיזוק הבקרות בתוך הפרוטוקול היחיד;
- Validation / Evidence — ראיות השימור, האירוע, ה־hook וסבב ה־credential;
- Exit State — מצב התחנה, Production, ‏Telegram ו־Opening Picture;
- Follow-ups — סיבת השורש, runtime validation ושאר הפערים הפתוחים;
- Current Truth alignment — המצב התקף מיושר ב־`current-truth.md`.

Self-check זה משלים את Documentation Checkpoint של התחנה החריגה
לפני Git anchoring; הוא אינו מחליף את סמכות הסגירה של הפרוטוקול.
