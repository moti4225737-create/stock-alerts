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

היישור ההיסטורי של Local `main`, ‏`origin/main` ו־GitHub default branch
אומת במסלולי ה־Production alignment המתועדים להלן. אין ברשומה זו
אימות מחודש של parity לאחר שינויי התיעוד של 2026-08-28.

Railway Production היה מחובר ל־`main`, ו־push תיעוד בלבד ב־2026-08-28
הוביל דרך CI לפריסה פעילה ולהפעלת runtime אוטונומי. בעקבות האירוע
ה־deployment הוסר ידנית. המצב התפעולי הנוכחי שנצפה לאחר ההסרה הוא:

- Railway Production הוא `OFF` במכוון;
- השירות offline;
- אין deployment פעיל;
- ה־deployment שהפעיל את האירוע מסומן removed.

Production אינו מאושר להפעלה מחדש עד להשלמת הבקרות המתקנות של
האירוע ולאימותן המפורש.

ה־Telegram Bot Token שנחשף בוטל ב־BotFather ונוצר token חלופי.
`TELEGRAM_TOKEN` החלופי נשמר ב־Railway, עודכן ב־`.env` המקומי
וב־GitHub repository secret; אין Telegram secret נוסף ב־GitHub
Environment secrets. אימות מקומי אישר שהמשתנה קיים ואינו ריק בלי
לחשוף את ערכו. Railway נשאר ללא deployment פעיל לאחר שינוי המשתנה,
והשינוי ממתין להחלה ב־deployment/runtime עתידי מאושר.

בדיקת tracked code אישרה ש־`main.py` צורך `TELEGRAM_TOKEN` מן
ה־environment, ‏CI משתמש במכוון ב־`ci-test-token`, והבדיקות דורשות
ש־CI לא יצרוך `secrets.TELEGRAM_TOKEN`; לא נמצא consumer tracked נוסף.

`Telegram credential rotation / containment = COMPLETE`.

`Telegram runtime / Production validation = PENDING FUTURE APPROVED PRODUCTION RESTART`.

Telegram delivery והשימוש ב־token החלופי ב־Production לא אומתו.
Production נשאר `OFF` במכוון וההפעלה מחדש אינה מאושרת.

Wait for CI ואכיפתו אומתו היסטורית. אימות זה אינו הופך push ל־`main`
לפעולה inert ואינו סותר את מצב Production הכבוי הנוכחי.

ב־`.git/hooks/pre-push` ממומשת ומאומתת כעת בקרת Defense in Depth
מקומית עבור push ל־`main`. היא דורשת אישור מפורש שנבדקו השלכות
Production/deployment, שירותים חיצוניים, עלות API והתראות לפני
המשך ה־push. ה־hook מקומי ובכוונה אינו tracked; הוא בקרת אכיפה
פנימית ואינו Gate חדש או Closure Authority.

בקרה זו אינה פותרת כשלעצמה את Railway auto-deploy, הגנת עלות API,
Telegram runtime / Production validation או סיבת השורש של alert storm,
ואינה מאשרת הפעלת Production מחדש. Production נשאר `OFF` וההפעלה
מחדש אינה מאושרת.

### Engineering Governance Truth

ה־Closure Authority היחיד למחזור שינוי End-to-End הוא:

`../03-ניהול-הפיתוח-ההנדסי/פרוטוקול-השינוי-האימות-המסירה-והסגירה-הסמכותי.md`

Quality Gates, Documentation Checkpoints, Maturity Gates ובקרות אחרות הם מנגנונים פנימיים או תחומיים ואינם Closure Authorities עצמאיים.

הפרוטוקול הסמכותי מתפתח באופן מצטבר באמצעות עדכון, חיזוק, דיוק והתאמה של הבקרות הפנימיות שלו. אין ליצור לצדו Closure Authority מקביל.

לפני Closure של שינוי שמבטיח Capability, התנהגות או תוצאה בנקודת יעד ממשית, נדרשת End-to-End Product Outcome Validation המוכיחה את התוצאה הנדרשת בנקודת היעד שלה ולא רק את תקינות הרכיבים או ה־wiring.

כאשר קיימים Degraded / Fallback paths מהותיים, ה־Product Outcome Validation חייב להבחין בין Success, Degraded / Fallback ו־Failure visibility כך שמסלול מופחת לא יוצג כהצלחת ה־Capability המלא ללא הגדרה ואישור מפורשים.

כאשר ראיה חדשה לאחר Closure סותרת באופן מהותי `PASS`, `COMPLETE` או `CLOSED`, מופעל Post-Closure Contradiction & Revalidation בתוך אותו פרוטוקול. הקביעה והראיות המקוריות נשמרות, והממצא מסווג לפי הראיות כ־`False Closure`, ‏`Regression after valid Closure` או `Insufficient Historical Evidence`.

### Product and Architecture Truth

ענפים 01–05 מתעדים את הזהות, דרישות המוצר, הארכיטקטורה, ההנדסה, התפעול והאימות המאושרים.

Stock Sentinel מוגדר כ־Personal Autonomous Investment Intelligence System המשלב Autonomous Intelligence Engine עם User Control Surface לתחזוקת המצב האישי הסמכותי של המשתמש.

ה־Railway Production runtime הנוכחי הוא Headless Autonomous Worker המממש את מנוע המודיעין. Telegram הוא כיום Delivery Surface.

User Control Surface הוא Product Capability נדרש עבור Portfolio lifecycle, ‏Watchlist lifecycle, ‏Preferences ו־user-owned corrections, אך טרם מומש במלואו. לא נבחרה טכנולוגיית UI, ולא נפתח Sprint למימושה.

### Documentation Truth

ענף 06 מגדיר כיצד המידע נשמר, מתעדכן, נגיש וניתן לעקיבה.

Documentation Checkpoint הוא בקרה פנימית מחייבת בפרוטוקול הסמכותי.

### Historical Truth

ה־Chronicle מתעד כיצד ומדוע עבר המוצר ממצב אחד לאחר.

## Production Alignment — 2026-08-21

במסלול היישור שבוצע ב־2026-08-21 אומתו היסטורית:

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
## Gate Evidence Automation — 2026-08-23

מנגנון Gate Evidence ממומש ומאומת עבור מסלול הסגירה הסמכותי.

ה־Gate אוסף ומצליב ראיות עבור:

- authoritative Git SHA;
- GitHub Actions CI על `main` ועל אותו SHA;
- Railway Production runtime identity;
- Railway deployment status;
- post-deployment Healthchecks evidence;
- source diagnostics במצב שבו ראיה אינה ניתנת לאימות.

עקרון האכיפה הוא fail-closed:

חוסר ראיה, ראיה שאינה תואמת ל־SHA הסמכותי, runtime identity שגוי, deployment שאינו מאומת או health שאינו ניתן לקישור לפריסה הרלוונטית אינם מאפשרים PASS.

המימוש עוגן ב־commit:

`05aecca429e2dbad7f2e65240d0675dc3b86d7e3 — Add automated gate evidence verification`

אומת בפועל:

- local `main` = `origin/main` = `05aecca429e2dbad7f2e65240d0675dc3b86d7e3`;
- GitHub Actions run `32622602473` — `Stock Sentinel CI` — completed / success;
- Railway Production runtime SHA = `05aecca429e2dbad7f2e65240d0675dc3b86d7e3`;
- Railway branch = `main`;
- Railway service = `stock-alerts`;
- Railway environment = `production`;
- Railway deployment ID = `0a05ad62-1d98-423b-9168-71ecbf519258`;
- Healthchecks Production Life = `up`;
- Healthchecks last ping = `2026-08-23T06:21:48+00:00`;
- final full regression = `531 passed`;
- legacy migration branch הוכח כ־ancestor של `main` ונמחק;
- repository clean לאחר היישור.

Gate Evidence הוא מנגנון פנימי של הפרוטוקול הסמכותי ואינו Closure Authority נפרד.

ערכי Railway service/environment ברשומת האימות ההיסטורית לעיל נאספו בבדיקת ה־Production שבוצעה באותו שלב. הם אינם כשלעצמם הקפאת ה־runtime-side contract של משטח Live Runtime Identity העתידי.

## Live Runtime Identity Contract — 2026-08-24

חוזה Live Production Runtime Identity אושר ברמת Product / Architecture וטרם מומש.

המנגנון העתידי המאושר הוא Minimal Read-Only HTTPS Challenge-Response מתוך ה־Production process הפעיל.

ה־public payload המחייב מוגבל ל־:

- `schema_version`;
- full `git_commit_sha`;
- `service`;
- `environment`;
- `observed_at`;
- caller challenge המוחזר במדויק;
- `process_instance_nonce` אקראי, non-secret ויציב רק למשך חיי process יחיד.

שתי תצפיות טריות עם challenges שונים נדרשות סביב קריאת שאר הראיות החיצוניות. שתיהן חייבות להגיע מה־pinned canonical Production HTTPS host, להתאים זו לזו ול־Railway-originated GitHub `deployment_status` exact SHA, ולעמוד ב־freshness / skew contract המאושר.

ה־Railway-originated GitHub deployment evidence שאומת בפועל משתמש ב־source-specific environment representation:

- `deployment.environment == "authentic-mercy / production"`;
- `deployment_status.environment == "authentic-mercy / production"`.

ה־runtime identity response העתידי יקבל `environment` ישירות מ־`RAILWAY_ENVIRONMENT_NAME` ו־`service` ישירות מ־`RAILWAY_SERVICE_NAME` של ה־Production process המבצע.

`production` הוא ה־runtime environment הצפוי כעת ו־`stock-alerts` הוא ה־runtime service הצפוי כעת. הם `NOT VERIFIED` כערכי Live Runtime Identity contract אמפיריים עד לתצפית הראשונה מן המשטח האמיתי. לאחר קבלתה, הערכים שנצפו חייבים לעבור Validation ולהיות מוקפאים ב־runtime-side contract לפני ש־PASS יכול להתאפשר.

אין לדרוש literal equality בין GitHub `deployment.environment` לבין runtime `RAILWAY_ENVIRONMENT_NAME`, ואין להשתמש ב־normalization שרירותי, substring matching, fuzzy matching או inferred equivalence. כל צד נבדק מול החוזה הספציפי למקורו; exact full SHA equality היא מפתח ה־correlation הבלתי משתנה בין Deployment-side ל־Runtime-side evidence.

Healthchecks נשאר מקור עצמאי ונפרד ל־fresh work / liveness evidence.

נכון לעכשיו:

- לא מומש או נחשף public runtime identity endpoint;
- לא שונו Railway networking או domain settings;
- לא שונה GitHub workflow לצורך היכולת;
- לא נוצרו Credentials או Secrets חדשים;
- החוזה מניח Production replica פעיל יחיד.

מעבר ל־multi-replica Production חייב לפתוח מחדש את החוזה לפני הפיכתו לסטנדרט.

## Opening / Initialization — Local Runtime Integration Proven — 2026-09-02

ה־Opening הנוכחי ממומש כמחזור חיים עצמאי לכל holding חדש לאחר קבלת
Portfolio Truth סמכותי ולפני צריכת התיק ב־runtime. הוא כולל זהות מאומתת
בבעלות Sentinel, מחקר bounded, החלטות אימות מפורשות, מצבי `LEARNING` /
`READY`, persistence לכל holding, וסינון זכאות דרך גבול
`SourceRuntimeFactory.portfolio_provider` הקיים.

Portfolio Truth נשאר מקור הסמכות היחיד לחברות בתיק ואינו משתנה לצורך יצירת
תצוגת runtime. holding חדש במצב `READY` נעשה זכאי; holding חדש במצב
`LEARNING` או כשל נשאר סמכותי אך אינו נמסר ל־runtime; holdings שהיו נוכחים
ברציפות נשארים זכאים. הסרה והצגה מחדש יוצרות lifecycle ו־`time_zero` חדשים,
בעוד שינוי רציף בכמות או בעלות ממוצעת אינו עושה זאת. `LEARNING` נשמר ונשחזר
עם `time_zero` המקורי.

החוזה והזרימה התקפים מתועדים בבית הארכיטקטורה הטבעי:

`../02-ספר-המוצר/02.05-ארכיטקטורת-המערכת/02.05.03-תהליכים-ואינטראקציות.md`

המסלול הוכח מקומית באמצעות doubles דטרמיניסטיים בגבולות החיצוניים. הראיות
כוללות Runtime Integration focused של `3 passed`, neighborhood של
`71 passed`, full regression מוקדם לפני Local E2E של `801 passed`, Local
E2E של `1 passed` ו־`3 deselected`, ו־post-E2E neighborhood של
`72 passed`. לאחר ניקוי test-contract מורשתי אומתו `25 passed` focused
ו־`72 passed` neighborhood, וסריקת חוזה Opening מורשתי עברה. ראיית הסגירה
הסופית לאחר כלל הניקויים היא: `802 passed in 15.41s`.

ראיות אלה אינן מוכיחות התנהגות אמיתית של Perplexity או SEC, אינן מוכיחות
Telegram או Production, ואינן מהוות אישור ל־Railway restart, deployment או
חיבור חיצוני. Production נשאר `OFF` במכוון והפעלה מחדש אינה מאושרת.

השלב הבא הוא `Alpha Portfolio Initial Integration`: חיבור הדרגתי ומבוקר של
התיק האמיתי, holding אחר holding, עם blast radius מוגבל והפיכת כל כשל ממשי
ל־diagnosis, correction bounded ו־regression case. טרם הושלמו onboarding
אמיתי, source coverage לכל holding, הרחבת רשת המקורות, אינטגרציית
correlation/summary/presentation נוספת, Telegram Production validation או
הוכחת Alpha מלאה בעולם האמיתי.

היסטוריית תחנת השימור הקודמת נשמרת ב־:

`chronicle/ספרינטים/2026-08-28-opening-picture-interrupted-preservation.md`

רשומת הספרינט וה־handoff הנוכחיים:

`chronicle/ספרינטים/2026-09-02-opening-runtime-local-e2e.md`

יחידת העבודה רשומה כ־`R&D 001 — Opening Runtime Local E2E` במצב
`IMPLEMENTATION COMPLETE — CLOSURE IN PROGRESS`; היא אינה `CLOSED`.
ה־implementation snapshot נמצא ב־commit המקומי
`dc9d8914cda1a31f877cd25c4ff2fe953c16f88a`. push ו־CI עבור commit זה לא
בוצעו.

היחידה הבאה הרשומה היא
`R&D 002 — Alpha Portfolio Initial Integration` במצב `NEXT — NOT OPEN`.
היא מחזיקה את העבודה האמיתית של portfolio onboarding, canary activation,
real Perplexity/SEC proof, ‏live Opening-to-continuous-operation proof,
real-world flood-prevention validation ובעיות onboarding תלויות holding או
company. יכולות אלה אינן מוכחות על־ידי ה־Local E2E של R&D 001.

Production נשאר `OFF` לפי ה־Current Truth המתועד, אך מצב Railway control
plane החיצוני הנוכחי, Auto Deploy ו־Wait for CI הם `NOT VERIFIED`. אין אישור
ל־push, reconnect, restart או deployment מכוח תיעוד זה.
