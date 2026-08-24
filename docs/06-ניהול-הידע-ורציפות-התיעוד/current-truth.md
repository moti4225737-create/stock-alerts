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
