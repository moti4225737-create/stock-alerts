# Chronicle — Opening Runtime Integration and Controlled Local E2E

## Objective

להחליף את חוזה Source Bootstrap העשיר והמורשתי ב־Opening מינימלי בבעלות
Sentinel, להשלים lifecycle עצמאי לכל holding חדש, ולחבר את זכאות Opening
לגבול ה־runtime הקיים בלי לשנות את Portfolio Truth או צרכני ה־runtime.

## Entry State

- Portfolio Truth היה סמכותי ומחובר ל־runtime.
- מימוש Opening קודם היה interrupted/preserved וכלל חוזה provider עשיר מדי.
- לא היה מסלול נקי ומוכח מקצה לקצה מ־authoritative introduction עד runtime
  eligibility.
- Railway Production היה ונשאר `OFF`; חיבור חיצוני מחדש לא היה מאושר.

## Material Changes

- החוזה המורשתי נוטרל והוסר מן המסלול הפעיל, מן persistence ומן הבדיקות
  הפעילות, בלי למחוק מודלים משותפים בעלי צרכנים אחרים.
- נוצר חוזה Opening נקי: `OpeningResearchResult`, ‏`0..10`
  `OpeningFactCandidate`, ו־`OpeningFactDecision` עם disposition מפורש.
- Verified Opening ID כולל `ticker`, ‏`company_name`, ‏`CIK` ו־`exchange`
  מאותה רשומת `company_tickers_exchange.json` סמכותית של SEC.
- Perplexity מקבל זהות מאומתת כהקשר בלבד ואינו מוסמך לייצר או להעשיר
  זהות, materiality, disposition או READY.
- מנגנון SEC הקיים הותאם להוכחת מועמד Opening באמצעות discovery,
  reconstruction, finding discovery ו־evidence validation עצמאיים.
- persistence עבר לקבצים עצמאיים לכל holding באמצעות filename דטרמיניסטי
  המבוסס על SHA-256 של symbol מנורמל, ושומר `LEARNING` ו־`READY` באופן
  fail-closed.
- Portfolio Truth עוקב אחר introductions סמכותיים ומחזורי חיים פעילים.
- `main.py` מריץ Opening לכל introduction באופן עצמאי לפני יצירת ה־runtime
  ומספק view זכאי דרך `SourceRuntimeFactory.portfolio_provider` הקיים.
- downstream runtime consumers לא שונו.

## Decisions and Rationale

- Portfolio Truth נשאר סמכות החברות היחידה; runtime view הוא נגזרת ואינו
  משנה את האמת הסמכותית.
- holding חדש נכלל ב־runtime רק לאחר `READY`; כשל או `LEARNING` של holding
  אחד אינם חוסמים holding אחר.
- holdings שהיו נוכחים ברציפות נשארים זכאים ואינם עוברים Opening חדש.
- הסרה והצגה מחדש יוצרות lifecycle ו־`time_zero` חדשים; שינוי רציף בכמות או
  average cost אינו עושה זאת.
- `READY` דורש זהות מלאה, מחקר שהושלם בהצלחה, לפחות עובדה אחת `VERIFIED`,
  והחלטה מפורשת לכל מועמד. materiality אינה תנאי READY.
- ערכי composition שאושרו: `max_output_tokens=2000`,
  `max_document_characters=20000`, ‏`timeout_seconds=60`, ‏store root
  `data/opening_state/`, credential source ‏`PERPLEXITY_API_KEY`, ו־SEC
  verification budget default ‏`None`.
- לא נוספו registry, manager/coordinator, database, runtime filter class,
  Portfolio authority נוסף או orchestration framework חדש.

## Validation / Results

- Opening Runtime Integration focused: `3 passed`.
- Runtime neighborhood: `71 passed`.
- Full regression before Local E2E: `801 passed`, ללא failures או collection
  errors.
- Controlled Local E2E: `1 passed, 3 deselected`.
- Post-E2E neighborhood: `72 passed`.
- Legacy test-contract cleanup: `25 passed` focused ו־`72 passed`
  neighborhood.
- Legacy Opening reference scan: `PASS`; ההתאמות שנותרו הן הגנות שליליות
  מכוונות או מושגים משותפים ליכולות אחרות.
- Final post-cleanup full regression: `802 passed in 15.41s`.
- לא בוצעה פעילות Perplexity, SEC, OpenAI, Telegram, autonomous runtime,
  Railway או Production אמיתית.

ה־Local E2E הוכיח באמצעות doubles דטרמיניסטיים:

Accepted Portfolio Truth
→ authoritative introduction
→ Verified Opening ID
→ bounded research
→ Sentinel dispositions
→ `READY` / `LEARNING`
→ runtime eligibility.

הוא אינו מהווה הוכחה להתנהגות provider אמיתי או Production.

## Exit State / Current Truth

- Opening Runtime Integration הוא `LOCAL IMPLEMENTED / VERIFIED` בגבול
  המאושר.
- holding חדש `READY` נעשה runtime eligible.
- holding חדש `LEARNING` או failed נשאר ב־Portfolio Truth אך אינו מגיע
  ל־runtime.
- existing continuously-present holdings נשארים eligible.
- multiple introductions מבודדים זה מזה.
- `LEARNING` ו־`time_zero` המקורי שורדים restart.
- Portfolio Truth נשאר מקור החברות היחיד וצרכני ה־runtime downstream לא
  שונו.
- Production נשאר `OFF`; restart, deployment וחיבור חיצוני אינם מאושרים.

## Known Limitations / Unproven External Behavior

לא הושלמו או הוכחו בספרינט זה:

- real Perplexity/SEC Opening E2E;
- initial real portfolio onboarding/configuration;
- source configuration/coverage לכל holding;
- הרחבת רשת המקורות;
- correlation/summary/presentation integration נוספת;
- Telegram Production validation;
- Railway restart או deployment;
- complete real-world Alpha proof.

## Next Phase

`Alpha Portfolio Initial Integration`.

האסטרטגיה היא activation הדרגתי בסגנון canary וב־blast radius מוגבל. כל
כשל holding-specific אמיתי יעבור diagnosis → bounded correction → regression
case, בלי redesign אוטומטי של הארכיטקטורה.

## Next-Conversation Handoff

### Repository state and change scope

- branch: `main`;
- base HEAD בעת ה־audit: `8e7164f29b62e2006e19abf8edb0e968e0684266`;
- upstream: `origin/main`;
- מימוש, בדיקות ותיעוד נמצאים ב־working tree מקומי ולא עברו stage, commit,
  push או CI.
- היקף הייצור כולל את Portfolio Truth lifecycle, מודלי/יישומי Opening,
  Perplexity ו־SEC boundaries, per-holding store ו־composition ב־`main.py`.
- היקף הבדיקות כולל חוזי Opening/SEC/Perplexity, restart/persistence,
  lifecycle, runtime integration ו־controlled Local E2E.

### Completed architecture and contracts

- Sentinel-owned Verified Opening ID;
- bounded candidates-only research;
- explicit Sentinel dispositions;
- `LEARNING → READY` עם `time_zero` יציב;
- per-holding persistence ו־ownership fail-closed;
- authoritative introduction tracking;
- runtime eligibility דרך ה־dynamic provider הקיים בלבד.

### Safety and Production state

- לא נשמרו secrets בתיעוד או בקוד המועמד;
- Railway Production `OFF`;
- external reconnect, runtime start, CI, deployment ו־Production validation
  לא בוצעו ולא אושרו;
- אין להסיק מ־Local E2E על התנהגות provider אמיתי.

### Protected files and Git restrictions

אין לבצע stage של `.tools/`, ‏`.env`, ‏`.pytest_cache/`, ‏`__pycache__/`,
`*.pyc`, ‏`notification_history.production.txt`, ‏`portfolio_source.json`,
`portfolio_state.production.json`, secrets, credentials או local runtime
artifacts. אין להשתמש ב־`git add .`. stage/commit/push/CI דורשים פעולה
ואישור מפורשים לפי הפרוטוקול הסמכותי.

### Exact next action recommended

בConversation הבא: לבצע read-only Impact Map עבור onboarding של holding
אמיתי ראשון כ־canary, כולל prerequisites של configuration והרשאות חיצוניות,
failure containment ונקודת ההוכחה, בלי להפעיל Production או שירות חיצוני.
רק לאחר החלטת Product Owner מפורשת יש לבצע חיבור אמיתי bounded.

## Follow-ups

- לעגן את השינוי ב־Repository History רק לאחר diff review ואישור Git מפורש.
- לבצע CI רק לאחר commit/push מאושרים.
- לפתוח את Alpha Portfolio Initial Integration לפי ה־handoff לעיל.
- להשאיר Production ו־external delivery כבויים עד לאישור והוכחה נפרדים.
