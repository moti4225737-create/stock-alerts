# Chronicle — Archive Foundation Sprint

## Objective

להקים ל־Stock Sentinel ארכיון מוצר רשמי, מבוקר, ניתן לעקיבה וניתן לתחזוקה, שישמש Controlled Source of Truth במקביל לעבודת ה־R&D.

המטרה הייתה להפוך ידע, החלטות, חוקה, ארכיטקטורה, נהלי עבודה, תפעול, אימות והרשאות שהיו מפוזרים בין קוד, מסמכי Legacy ושיחות עבודה — למבנה סמכותי אחד שניתן להבין ולהמשיך ממנו ללא תלות בזיכרון השיחות.

## Entry State

בתחילת הספרינט:

- `docs/` הכיל מסמך Legacy יחיד:
  `docs/policies/intelligence_sources.md`.
- `AGENTS.md` שימש מסמך Constitution/Engineering מעורב שהכיל יחד עקרונות חוקתיים, ארכיטקטוניים, הנדסיים, QA, Security ו־Reliability.
- לא היה Master Archive Tree מלא.
- לא היה Chronicle מסודר.
- לא היה Documentation Checkpoint מחייב.
- נהלי עבודה משמעותיים רבים נשמרו בעיקר במסגרת תהליך העבודה והשיחות.
- לא היה Access Governance מלא לפי Roles, Disclosure Lifecycle והגנת IP.

## Material Changes

### 1 — נקבע מעמד הארכיון

ארכיון המוצר הוגדר כענף־אב מקביל ל־R&D.

R&D יוצר ומשנה את המוצר בפועל.

הארכיון מתעד, משמר, מסביר ומאפשר עקיבות של מצב המוצר המאומת.

הארכיון אינו מנהל את R&D ואינו משנה את המוצר רק כדי להתאים למסמך ישן.

### 2 — נקבע Master Tree

הארכיון חולק לשישה ענפי־על:

1. יסודות המוצר.
2. ספר המוצר.
3. ניהול הפיתוח ההנדסי.
4. תפעול המערכת.
5. אבטחת איכות, אימות ותיקוף.
6. ניהול הידע ורציפות התיעוד.

הענף המוצע "התפתחות ושיפור מתמשך" נופה כענף־על ותוכנו חולק לבתים המהותיים המתאימים.

### 3 — החוקה נוקתה והופרדה מהמימוש

החוקה צומצמה לגרעין יציב של ארבע משפחות:

- תכלית המוצר.
- הצגה נאמנה של המידע.
- ביסוס אמינות המידע.
- התפתחות תוך שמירת עקרונות היסוד.

עקרונות Architecture, Engineering, QA, Security ו־Operations שהיו בתוך `AGENTS.md` הועברו לבתים הסמכותיים המתאימים.

### 4 — נקבעה שיטת מיון והכרעה

במקרה של התלבטות פועלים לפי:

מהות ומטרה
→ תהליך מעשי
→ תרחיש תקין
→ תרחיש כשל / שימוש לרעה
→ Benchmark מקצועי כאשר הוא מועיל מהותית
→ הצעה
→ החלטת בעל המוצר
→ קיבוע Current Truth והנימוק ההיסטורי.

נשמר גם מבחן:

פרט + פרט + ... = כלל.

עומק חדש בעץ נוצר רק כאשר קיימת משפחה טבעית אמיתית.

### 5 — נקבע Engineering Governance

נבנו נהלים סמכותיים עבור:

- TDD: RED → GREEN → REFACTOR.
- Impact Map לפני שינוי משמעותי.
- בקרת שינויים הנדסיים.
- משמעת Scope.
- קבלת החלטות הנדסיות.
- ניהול ספרינטים.
- Definition of Done.
- Evolution Register.
- שערי בשלות ושיפור.

### 6 — נקבע Documentation Governance

Documentation Checkpoint הפך ל־Completion Gate מחייב בסיום כל Sprint או Stage רשמי.

ה־Checkpoint כולל:

1. Current Truth.
2. Chronicle.
3. Traceability / Repository History.

נוספה גם חובה לבדוק בסיום:

- חוסרים;
- כפילויות;
- Authoritative Ownership שגוי;
- Legacy;
- Placeholder / Temporary / TODO;
- קצוות פתוחים;
- התאמה בין מצב המוצר לתיעוד.

### 7 — נקבע Access Governance

נבנה מודל הרשאות מלא עבור תשעה Roles:

1. בעל המוצר.
2. הארכיטקט הראשי.
3. הצוות הטכני.
4. יועצים מקצועיים.
5. מבקר חיצוני.
6. משקיע או שותף פוטנציאלי.
7. רוכש פוטנציאלי.
8. שירותים ומערכות אוטומטיות.
9. ציבור או גורם חיצוני לא מורשה.

נקבעו בין היתר:

- Default Deny.
- Least Privilege.
- Need-to-Know.
- Separation of Duties.
- No Self-Escalation.
- Access Lifecycle.
- Expiry / Review / Revocation.
- Disclosure Packages.
- Disclosure Records.
- Aggregation Risk.
- Reconstructability Risk.
- Buyer Capability Risk.
- Public Release Gate.
- Secret Handling.
- Machine Identities.
- Break-Glass כדרישת תכנון עתידית.

### 8 — נקבעה הגנת IP בתהליכי ביקורת, השקעה ורכישה

ההרשאה אינה נגזרת רק מה־Role אלא גם מהשלב בתהליך.

למשקיע ולרוכש נקבע Disclosure Lifecycle מדורג.

ברכישה הוגדרו שני מסלולי כניסה:

- מכירה יזומה.
- פנייה נכנסת של רוכש אסטרטגי.

שני המסלולים מתכנסים ל:

Confidentiality
→ Controlled Demonstration
→ Economic Interest
→ LOI
→ Due Diligence
→ Protected Technical DD
→ Definitive Agreement
→ Signing
→ Closing.

הוגדר עיקרון של הוכחת Capability בלי לחשוף אוטומטית את המוצר ברמת שחזור.

### 9 — Legacy Migration

תוכן `AGENTS.md` מופה לבתים הסמכותיים החדשים.

לאחר Coverage Check:

`AGENTS.md` הוסב ל־Engineering Entry Point בלבד ואינו עוד Constitution מקביל.

תוכן:

`docs/policies/intelligence_sources.md`

הוטמע ב־Product Requirements, כולל:

- Primary Sources.
- Secondary Sources.
- Source Priority.
- Original / Discovery Source.
- Publication / First Seen Time.
- Verification Status.
- Confidence.
- Freshness.

לאחר אימות שאין Consumers או References חיים, מסמך ה־Legacy הוסר מהעץ הפעיל.

ההיסטוריה שלו נשמרת ב־Git וב־Chronicle.

## Significant Decisions and Rationale

### Authoritative Home אחד

לכל נושא יש בית סמכותי יחיד.

אין לשמור מסמך Legacy, כפילות חלקית או גרסה Superseded פעילה רק לצורך "ביטחון".

לאחר שה־Current Truth החדש אומת באופן מוחלט ונבדק שאין אובדן מידע או Consumer חי, יש להסיר את הישן מהעץ הפעיל.

ההיסטוריה נשמרת ב־Git וב־Chronicle.

### עברית כשפת ניווט

עברית היא שפת הארגון והניווט הראשית בארכיון.

אנגלית נשמרת רק כאשר מונח מקצועי, שם רכיב או תקן מוסיפים דיוק.

### README כשער ענף

כלל שמכיל ילדים מיוצג כתיקייה עם `README.md`.

פרט סופי מיוצג כמסמך Markdown.

README של ענף מסביר בקצרה את מטרת הענף, גבולותיו וילדיו בלי לסרבל את העץ.

## Validation and Results

- Branch בעת ההקמה: `v0.5`.
- Repository היה נקי בתחילת העבודה.
- נוצר Master Archive Tree מלא.
- כל Placeholder פיזי הוחלף בתוכן.
- `TEMPORARY STRUCTURE` הגיע ל־0.
- בדיקת Coverage מול `AGENTS.md` זיהתה פערים והם הושלמו.
- בדיקת Coverage עצמאית מול `intelligence_sources.md` בוצעה ללא הסתמכות על קובץ ה־Legacy עצמו.
- כל פריטי Source Policy שנבדקו עברו Coverage.
- לא נמצאו References חיים ל־`AGENTS.md` או ל־`intelligence_sources.md`.
- `docs/policies` הוסר לאחר שהפך מיותר.

## Exit State

Stock Sentinel מחזיק כעת בארכיון מוצר מסודר בעל:

- Constitution סמכותית.
- Product Book.
- Architecture documentation.
- Engineering Governance.
- Operations documentation.
- QA / Verification / Validation documentation.
- Documentation Governance.
- Chronicle.
- Access and Disclosure Governance.
- Evolution Register.
- Traceability model.
- Engineering Entry Point ב־root.

הארכיון בנוי כך שיוכל להתעדכן כחלק מסיום כל Sprint או Stage בלי להפריע למסלול ה־R&D הפעיל.

## Follow-ups

### Production Reliability — External Watchdog / Heartbeat

פער Production Reliability שזוהה במהלך הספרינט.

סטטוס:
Required — Not Yet Implemented.

הוא משימת ה־R&D הראשונה לאחר סיום ספרינט הארכיון ולפני Feature חדש.

תהליך פתיחה:

Impact Map
→ Proposal
→ Owner Approval
→ RED
→ Implementation
→ Validation
→ Documentation Checkpoint.

### Hard Regulatory Gate

לפני הרחבה עתידית מ־Investment Intelligence לעבר Personalized Recommendation, Order Proposal או Broker Execution, נדרשת בדיקה משפטית ורגולטורית מקצועית ואישור מוצרי נפרד.

### Alpha Value Validation

לאחר Alpha יציבה עם מקורות ו־Source-Grounded Summary מחוברים, יש למדוד ערך אמיתי באמצעות מדדים כגון:

- Recall;
- Latency;
- Precision;
- Grounding;
- Correlation;
- Personal Relevance;
- Human Effort;
- Decision Usefulness;
- Time-to-Awareness.

## Repository Traceability

Baseline before archive work:

`e9ded34 — Make static macro calendar tests deterministic`

Commit יסוד הארכיון נושא את ההודעה: Establish governed product documentation archive. מזהה ה-commit הסופי נשמר ב-Git Repository History ואינו נכתב בתוך אותו commit כדי למנוע self-reference בלתי יציב.
