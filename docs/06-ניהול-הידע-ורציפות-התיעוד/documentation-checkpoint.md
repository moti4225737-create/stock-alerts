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

פרטי Continuous Accountability וסדר ההשלמה המאושר נמצאים ב־[חוזה התכנון](#continuous-accountability-design-contract) להלן.

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
## Continuous Accountability Design Contract

זהו חוזה התכנון המאושר של Documentation Checkpoint Continuous Accountability.
סעיפי החוזה 1–9 להלן הם חוזה אחד; טבלת המעברים מפנה לכלליו ואינה מוסיפה דרישות נפרדות.
החוזה אושר לעיגון תיעודי; עיגונו אינו מימוש או activation של המנגנון.
מקור האישור ומצב העבודה מתועדים ב־Chronicle של R&D 002 וב־Current Truth, בהפניה לבית סמכותי זה.

### 1. MUST invariants

**מונחים**

- **Known Material Outcome — outcome:** התפתחות שהוכרה כמהותית וידועה לפי כללי הסמכות והראיות הקיימים.
- **האוסף:** אוסף outcomes מצטבר של ספרינט ב־Chronicle הקיים.
- **מצב חשבונאי:** `PENDING` או `RESOLVED`, לצורכי Documentation Checkpoint בלבד.
- **Resolution תקף:** השלמת הטיפול החשבונאי לפי I4 להלן.
- **אי־תקפות resolution:** מצב integrity לפי I6; אינו סטטוס lifecycle נוסף.

**I1 — קליטה בלתי מותנית.** מרגע שהתפתחות נעשית Known Material Outcome, היא חייבת להיכנס לחשבונאות ה־Checkpoint של הספרינט. המשתתף שמבסס או מקבל אותה חייב לבצע intake לפני התייחסות אליה כמידע שכבר טופל. דחיפות, חסימה או היעדר חסימה אינם תנאי לקליטה.

**I2 — התמדה מצטברת.** חייב להתקיים אוסף קנוני אחד ב־Chronicle של הספרינט, מחוץ לבלוק `station-state` הניתן להחלפה. החברות והזהות נשמרות בהחלפת תחנה, החלפת סוכן, Handoff, השלמה טכנית ו־resolution חשבונאי.

**I3 — זהות וקליטה חוזרת.** קליטה חוזרת של אותה התפתחות חייבת להתייחס לאותה זהות. דמיון טקסטואלי או reference משותף אינם מוכיחים זהות. התנגשות מזהים או עמימות באיחוד/פיצול מחייבות reconciliation מפורש, ללא שינוי היסטורי שקט.

**I4 — כניסה ו־resolution.** כל outcome חייב להיכנס כ־`PENDING` ולהישאר באחריות חשבונאית עד השלמת כל הטיפול הישׂים. מעבר ל־`RESOLVED` מותר רק כאשר בסיס ההכרעה קושר בין:

- הדרישה הישימה;
- ה־disposition והטיפול שבוצעו, כולל Natural Homes, תיעוד ו־Traceability כנדרש;
- הראיות התומכות;
- אישור PO במקום שהסמכות הקיימת מחייבת אותו.

`FIXED`,‏ `VALIDATED`,‏ `CLASSIFIED_AND_PERSISTED`,‏ Handoff, קיום מסמך או מצב obligation אינם גוררים את המעבר אוטומטית.

**I5 — התפתחות מאוחרת ואי־רקורסיביות.** resolution תקף נשמר כעובדה היסטורית. החלטה, סתירה, שינוי ראיה, ממצא או השלכה מהותיים חדשים חייבים להיקלט כ־outcome חדש, המקושר לקודם כאשר הוא התפתחות שלו. Lineage הוא הפניה, ללא event replay. Intake, הוספת reference, עבודת disposition או bookkeeping אינם יוצרים outcome נוסף כשלעצמם.

**I6 — resolution היסטורי לא תקף.** אם הדרישות המקוריות לא התקיימו, חייבים לשמר את העובדה שנרשם `RESOLVED`, ולהציג במפורש ובקישור את אי־תקפותו הנוכחית. אסור לצרוך אותו כהוכחה תקפה. outcome חדש המתעד את הגילוי אינו פוטר מתיקון הטענה המקורית והשלכותיה, תוך שמירת ההיסטוריה.

**I7 — אחריות ורציפות.** לכל `PENDING` חייב להיות משתתף אחראי או next station הניתנים לזיהוי לפי כללי הרציפות הקיימים. Handoff חייב לאפשר איתור האוסף, היתרה הרלוונטית, האחריות, ה־prerequisites והפעולה המותרת הבאה. העברה שלא הושלמה אינה מוחקת את אחריות המעביר. אין טקס acknowledgement חדש.

`NO_MATERIAL_OUTCOME` מתייחס להתפתחויות החדשות של התחנה; הוא יכול להתקיים לצד `PENDING` ישנים באוסף הספרינט.

**I8 — שמירת הבקרות הקיימות.** `PENDING` אינו דוחה או מחליש Same-Station Persistence, סיווג ושימור נדרשים, אישור PO, obligations ו־required-before, בטיחות, דרישות מעבר או דרישות successor. מנגד, פריט `PENDING` תקין אינו איסור גורף על התקדמות תחנה או Handoff לגיטימיים כאשר יתר הדרישות הישימות עברו.

**I9 — גבול המנגנון.** המנגנון חייב להישאר חשבונאות Checkpoint בלבד. אין להוסיף באמצעותו workflow engine, task tracker, scheduler, event sourcing, מאגר תוכן נורמטיבי, Traceability או register חובות מקבילים, taxonomy מתחרה, Gate או סמכות Closure. Chronicle נשאר הבית המאושר להיקף single-user Alpha.

כללי הסמכות, האכיפה, הכשל, המיגרציה וההשלמה מפורטים בסעיפי החוזה 4–9 ומהווים חלק מחייב מאותו חוזה.

### 2. Required state / metadata — minimum only

אלה דרישות מידע לוגיות, ללא קביעת שמות שדות או פורמט מימוש:

| היקף | המידע המינימלי |
|---|---|
| האוסף | שיוך חד־משמעי לספרינט; אוכלוסיית outcomes מזוהה; מבנה שניתן לבדוק את תקינותו |
| outcome | זהות יציבה; זיהוי ההתפתחות ו־provenance תומך; מצב חשבונאי |
| outcome ב־`PENDING` | אחריות מזוהה או next station; הפניות שמאפשרות להבין את הטיפול והיתרה |
| resolution | ה־disposition ובסיס I4, ישירות כמידע חשבונאי או בהפניות לבתים המוסמכים |
| כשיש התפתחות קשורה | הפניה לזהות הקודמת |
| כשנתגלה resolution לא תקף | הטענה ההיסטורית, אי־התקפות הנוכחית והקישור ביניהן לפי I6 |
| אימות רציפות | נקודת השוואה מהימנה לאוכלוסייה הידועה וזיהוי הגרסה שעליה מבוססת הבדיקה |
| מיגרציה/activation | היקף השחזור, provenance ובסיס שמבחין בין שחזור חלקי לבין activation מלאה |

המידע יכול להישען על references קיימים; אין דרישה להעתיקו כולו לכל רשומה. ספירת `PENDING` היא תוצאה נגזרת, לא סמכות מצב נוספת.

אין צורך כללי בעדיפויות, אחוזי התקדמות, תאריכי יעד, גרפי משימות, העתקי obligation status, תוכן נורמטיבי או event replay. אין להמציא timestamps היסטוריים.

### 3. Lifecycle / transition table

הטבלה מסכמת את הכללים לעיל; “גילוי”, “intake” ו־“Handoff” הם אירועים, לא סטטוסים נוספים.

| אירוע או מצב | פעולה/תנאי מחייב | תוצאה חשבונאית |
|---|---|---|
| Known Material Outcome התבסס | I1: חובת intake ללא תנאי דחיפות | כניסה נדרשת כ־`PENDING` |
| Intake | I2–I3: רישום בזהות הנכונה; שימוש בזהות קיימת בקליטה חוזרת | חדש: `PENDING`; קליטה חוזרת אינה מאפסת מצב |
| `PENDING` | I4 ו־I7: אחריות וטיפול ישים נמשכים | נשאר `PENDING` כל עוד תנאי resolution לא הושלמו |
| resolution תקף | כל תנאי I4 התקיימו | `PENDING → RESOLVED`; החברות נשמרת |
| התפתחות מהותית מאוחרת | I5: קליטה חדשה וקישור רלוונטי | outcome חדש ב־`PENDING`; ההיסטוריה הקודמת נשמרת |
| גילוי resolution היסטורי לא תקף | I6: הצגת אי־תקפות וטיפול בטענה ובהשלכות; קליטת הגילוי לפי I1/I5 | אין הסתמכות על ה־resolution המקורי כהוכחה תקפה |
| Handoff | I7–I8: רציפות והעברת אחריות לפי הכללים הקיימים | הזהויות והמצבים נשמרים; אין העתק lifecycle עצמאי |
| השלמת Checkpoint | כל תנאי סעיף החוזה 9 עברו | אין `PENDING` רשום; האוסף והחברות נשמרים; אין מכאן Closure עצמאי |

### 4. Authority boundaries

**AB1 — סמכות לפי סוג מידע**

| מקור | סמכותו |
|---|---|
| האוסף המצטבר ב־Chronicle | חברות, זהות ומטא־דאטה של חשבונאות Checkpoint |
| Natural Homes התחומיים | תוכן נורמטיבי ותחומי |
| Traceability | קישור ראיות |
| `open-obligations.json` | מצב obligations |
| `station-state` | מצב התחנה הנוכחית |
| הפרוטוקול הסמכותי | סמכות Closure היחידה |

**AB2 — הפניות וסכסוכי סמכות.** `station-state`,‏ Handoff ותצוגות נגזרות רשאים להפנות ל־outcomes; אין להם עותק lifecycle בעל סמכות עריכה עצמאית. סתירה בין בתים מוסמכים מחייבת reconciliation. `RESOLVED` חשבונאי אינו סוגר obligation, קובע אמת נורמטיבית או מאשר מעבר.

### 5. Mechanical enforcement boundary

**ME1.** האכיפה המכנית מוגבלת לתכונות הניתנות לידיעה מכנית: schema, ייחודיות זהות, שיוך לספרינט, סטטוס מותר, references נדרשים, החלקים הניתנים לבדיקה בבסיס resolution, רציפות האוכלוסייה שכבר ידועה ומניית `PENDING` רשומים.

**ME2.** הבדיקה חייבת להתייחס לגרסה הנבדקת ולנקודת השוואה מהימנה. תקינות האוסף הנוכחי לבדו אינה מוכיחה שלא הוסר חבר היסטורי.

**ME3.** עקביות reference, אימות provenance של אישור והכרעת התאמת הטיפול הן שאלות נפרדות. הצלחה מכנית אינה מאמתת אוטומטית את מקור האישור או את תוכנו.

**ME4.** תוצאה מכנית אינה מוכיחה שכל outcome מהותי נלכד ואינה מעניקה Checkpoint PASS או Closure מכוחה בלבד.

### 6. Semantic / human responsibility boundary

**HR1.** Agent, Reviewer ו־PO, לפי סמכויותיהם הקיימות, אחראים לזיהוי התפתחות ידועה ומהותית, הכרעת זהות, applicability, התאמת disposition, איכות התיעוד, מספקות הראיות ואימות אישורים כנדרש.

**HR2.** ההכרעות חייבות להישען על כללי הסמכות והראיות הקיימים. החוזה אינו יוצר מערכת אישורים או taxonomy חדשה.

**HR3.** המשתתפים חייבים לזהות גם התפתחות מהותית שנחשפה במהלך טיפול חשבונאי, ולהחיל עליה I1/I5; אין להסתפק בבדיקת השדות הרשומים.

### 7. Failure / fail-closed contract

**FC1.** כשל בתקינות או ברציפות חייב למנוע מסקנות והתקדמות התלויות בנתון שנכשל. הוא אינו כשלעצמו איסור על אבחון או recovery מורשים שאינם נשענים על אותה מסקנה.

| מצב כשל | התוצאה המחייבת |
|---|---|
| אוסף חסר לאחר activation | אינו אוסף ריק; אין zero-`PENDING` תקף או PASS תלוי |
| מבנה פגום, ספרינט שגוי, סטטוס אסור או זהות כפולה | אין הסתמכות על האוסף כחשבונאות תקינה |
| כתיבה חלקית, גם אם תקינה תחבירית | אין להפיק ממנה מסקנת zero-`PENDING` או PASS |
| היעלמות לא מוסברת של חבר היסטורי | כשל רציפות; נדרש reconciliation מול נקודת ההשוואה המהימנה |
| reference או בסיס resolution נדרשים חסרים/לא תקפים | אין לבסס עליהם resolution תקף |
| אחריות לא מזוהה או העברה לא פתורה | אין לטעון שהרציפות/ההעברה הושלמה; חל I7 |
| snapshot מיושן | אין להשתמש בתוצאה הקודמת לגרסה שהשתנתה; יש לבדוק מחדש |
| migration שנקטעה | אין להציג activation מלאה או אוכלוסייה שלמה |
| resolution היסטורי לא תקף | חל I6; ספירת אפס אינה עוקפת את אי־התקפות |

**FC2.** recovery חייב להסתמך על ראיות מהימנות, לשמר זהויות ו־provenance ולהימנע מהמצאת היסטוריה. אין להחליף נקודת השוואה רק כדי להעלים כשל.

### 8. R&D 002 migration contract

סעיף זה מוגבל למיגרציה הראשונית המאושרת של R&D 002.

**MG1 — גבול.** השחזור הראשוני מוגבל ל־R&D 002, מתחילת הספרינט ועד activation של המנגנון. אין מיגרציה אוטומטית של ספרינטים מוקדמים יותר.

**MG2 — מקורות.** יש להשתמש בראיות סמכותיות/מקובלות קיימות: Chronicle והיסטוריה, material outcomes קיימים, החלטות PO, obligations, ראיות ו־Natural Homes ישימים.

**MG3 — שתי הכרעות נפרדות.**

1. האם הראיות מבססות membership כ־Known Material Outcome?
2. האם הראיות מבססות השלמת הטיפול החשבונאי?

חוסר ראיה להכרעה השנייה משאיר `PENDING`. חוסר ראיה לראשונה אינו מתיר להמציא outcome.

**MG4 — נאמנות היסטורית.** יש לשמר זהויות ו־provenance מוכחים ולהחיל I3 על התנגשויות ועמימות גרנולריות. אין להמציא timestamps, אישורים או מצב היסטורי. כל פריט נכנס לפי I4; אין קידום אוטומטי ממצב טכני או מסיווג persistence.

**MG5 — activation ורציפות.** לפני הסתמכות על activation מלאה חייב להיות בסיס מהימן להשלמת השחזור בגבול MG1 ולרציפות אוכלוסייתו. שחזור חלקי או חידוש לאחר הפרעה אינם בסיס לטענת שלמות, ואינם מצדיקים שכפול זהויות.

### 9. Documentation Checkpoint completion contract

**CP1 — סדר מחייב**

1. אימות תקינות ורציפות האוסף וסקירת מלוא האוכלוסייה הרשומה.
2. השלמת הטיפול הישׂים באוכלוסייה הרשומה לפי I4.
3. ביסוס zero registered `PENDING`.
4. ביצוע Accumulated Delta Sweep העצמאי ובקרות Governance הישימות.
5. קליטת outcomes שהושמטו והתגלו, כ־`PENDING`, וטיפול בהם.
6. ביסוס חוזר של zero registered `PENDING` ותקינות החשבונאות.
7. Final Documentation Review.
8. Final Re-grounding ובקרות הרציפות הקיימות במקומן הסמכותי.
9. authoritative Closure רק לאחר שכל שאר הדרישות הישימות עברו.

**CP2 — גילוי מאוחר.** התפתחות מהותית שהתגלתה ב־Review או Re-grounding מחייבת חזרה ל־intake וחזרה על הבקרות שהושפעו. לולאת טיפול בממצא חדש היא לגיטימית; bookkeeping בלבד כפוף לאי־הרקורסיביות שב־I5.

**CP3 — תנאי השלמה.** כל outcome רשום חייב לקבל disposition וטיפול ישימים, ומספר ה־`PENDING` הרשומים חייב להיות אפס. אפס הוא תנאי הכרחי ולא מספיק: יתר בקרות התיעוד, התקינות, הרציפות והפרוטוקול נשארות מחייבות.

**CP4 — טענת ההשלמה המרבית**

> באוסף הספרינט התקין, בגרסה שנבדקה, לא נשאר outcome רשום ב־PENDING; בדיקות התקינות והרציפות המוגדרות עברו; והביקורות הסמנטיות הישימות לא זיהו יתרה שלא טופלה.

אין להסיק מכך שכל outcome מהותי אפשרי נלכד מכנית.

<!-- DC-CONTINUOUS-ACCOUNTABILITY-DESIGN-CONTRACT-PO-APPROVED -->

## Documentation Checkpoint Continuous Accountability ? PO-Approved Design Contract

Status: **PO APPROVED**
Scope: Documentation Checkpoint internal control.
Implementation: **NOT IMPLEMENTED**.
RED: **NOT STARTED**.

This contract is an internal control of the existing single Authoritative Closure Protocol.
It creates no new Gate, Closure authority, workflow engine, task tracker, event-sourcing
system, duplicate Traceability system, duplicate obligation register, normative-content
store, or competing taxonomy.

### I1 ? Unconditional intake

From the moment a development becomes a `Known Material Outcome` under the existing
authority/evidence rules, it MUST enter the sprint Documentation Checkpoint accounting.
The contributor/agent that establishes or receives it MUST perform intake before treating
it as already-handled information. Urgency, blocking or nonblocking status is not an
intake condition.

### I2 ? Cumulative persistence and state home

One canonical cumulative sprint-scoped Known Material Outcomes collection MUST live in
the existing sprint Chronicle, outside replaceable `station-state`.

Membership and identity survive station replacement, executing-agent change, Handoff,
technical completion and checkpoint resolution.

The collection is authoritative ONLY for Documentation Checkpoint accounting metadata.
Natural Homes retain normative/domain-content authority; Traceability retains
evidence-linking authority; `open-obligations.json` retains obligation-state authority;
`station-state` retains current-station authority; the Authoritative Closure Protocol
retains sole Closure authority.

### I3 ? Identity and repeated intake

Repeated intake of the same development MUST use the same identity. Textual similarity
or a shared reference alone does not establish identity. ID collision or semantic
merge/split ambiguity requires explicit reconciliation without silent historical change.

### I4 ? PENDING and valid RESOLVED

Every outcome enters checkpoint accounting as `PENDING`.

It remains `PENDING` until all applicable documentation/accountability handling is
complete. `RESOLVED` requires a supported basis connecting:
1. the applicable requirement;
2. applicable disposition and handling, including Natural Homes, documentation and
   Traceability where required;
3. supporting evidence; and
4. PO approval where existing authority requires it.

`FIXED`, `VALIDATED`, `CLASSIFIED_AND_PERSISTED`, Handoff, document existence or
obligation status MUST NOT automatically imply `RESOLVED`.

### I5 ? Later development and non-recursive accounting

A validly `RESOLVED` outcome remains historical fact.

A genuinely later material decision, contradiction, evidence change, finding or
consequence is a NEW Known Material Outcome, linked to the earlier outcome where
applicable, and starts `PENDING`.

Intake, adding a reference, disposition work, resolution bookkeeping or other accounting
work MUST NOT create another outcome merely because the accounting action occurred.
Lineage is referential; it is not event replay.

### I6 ? Invalid historical resolution

If an original resolution never satisfied its applicable requirements, preserve the
historical fact that `RESOLVED` was recorded, but make its current invalidity explicit
and linked.

The invalid historical resolution MUST NOT be consumed as currently valid proof.
A linked new outcome recording discovery of the invalidity does not excuse correction
of the original invalid claim and its consequences. History MUST NOT be silently
rewritten.

### I7 ? Responsibility and continuity

Every `PENDING` outcome MUST retain an identifiable responsible participant or next
station under the existing continuity rules.

Handoff MUST allow the successor to locate the canonical collection and identify the
relevant remainder, responsibility, prerequisites and permitted next action.
An unresolved transfer does not erase the transferor's responsibility.

No independent lifecycle-state copy or new acknowledgement ceremony is created.

`NO_MATERIAL_OUTCOME` describes new material outcomes of the current station and may
coexist with older sprint outcomes that remain `PENDING`.

### I8 ? Existing controls remain binding

Checkpoint `PENDING` MUST NOT override or weaken Same-Station Persistence, required
classification/persistence, PO approval, obligations and `required-before`, safety
controls, transition requirements or Handoff successor requirements.

Conversely, a valid `PENDING` item is not by itself a blanket prohibition on ordinary
station progression or legitimate Handoff when every other applicable requirement passes.

### I9 ? Minimum-glue boundary

The mechanism is checkpoint accounting only. It MUST NOT become a workflow engine,
task tracker, scheduler, event-sourcing system, duplicate Traceability system, duplicate
obligation register, normative-content store, competing taxonomy, new Gate or Closure
authority.

Chronicle remains the approved state home at current single-user Alpha scale.

### Minimum required state / metadata

The logical minimum is:
- unambiguous sprint identity and a structurally valid collection;
- stable outcome identity, development identification/provenance and checkpoint status;
- for `PENDING`, identifiable responsibility/next station and references sufficient to
  understand remainder and handling;
- for resolution, disposition and the I4 resolution basis, directly or by references to
  authoritative homes;
- lineage reference when a later material development relates to an earlier outcome;
- for invalid historical resolution, preserved historical claim plus explicit current
  invalidity and linkage;
- a trustworthy population-continuity comparison point and identification of the
  reviewed version;
- for migration/activation, reconstruction scope and provenance sufficient to distinguish
  partial reconstruction from full activation.

`PENDING` count is derived state, not a second authority.

Generic priorities, progress percentages, generic due dates, task graphs, normative
content copies, obligation-state copies and event replay are not required.

### AB1?AB2 ? Authority boundaries

Checkpoint collection: membership, identity and checkpoint-accounting metadata only.
Natural Homes: normative/domain content.
Traceability: evidence relationships.
`open-obligations.json`: obligation state and required-before.
`station-state`: current-station state.
Authoritative Closure Protocol: sole Closure authority.

References in `station-state`, Handoff, Current Truth or other derived views do not gain
independent lifecycle editing authority. Conflicts among authoritative homes require
reconciliation.

Checkpoint `RESOLVED` does not close an obligation, determine normative truth or
authorize a transition.

### ME1?ME4 ? Mechanical enforcement boundary

Mechanical enforcement is limited to mechanically knowable properties, including as
applicable:
- schema;
- identity uniqueness;
- sprint identity;
- allowed checkpoint status;
- required references;
- mechanically checkable parts of resolution basis;
- continuity of already-known population;
- enumeration of registered `PENDING`.

Validation MUST use the reviewed version and a trustworthy continuity comparison point.
A valid current collection alone does not prove that no historical member disappeared.

Reference consistency, approval-provenance validation and semantic adequacy of handling
are separate questions.

Mechanical success MUST NOT claim that every possible material outcome was captured,
and does not independently grant Checkpoint PASS or Closure PASS.

### HR1?HR3 ? Semantic / human responsibility

Agent, Reviewer and PO, according to existing authority, remain responsible for semantic
recognition/materiality, identity judgment, applicability, disposition adequacy,
documentation adequacy, evidence sufficiency and required approvals.

The contract creates no new approval system or taxonomy.

A genuinely new material development discovered during checkpoint handling is itself
subject to I1/I5; checking registered fields alone is not semantic completeness.

### FC1?FC2 ? Failure / fail-closed contract

A missing collection after activation MUST NOT be interpreted as an empty collection.

Malformed structure, wrong sprint, forbidden status, duplicate identity, partial write,
unexplained disappearance of a historical member, missing/invalid required resolution
basis, unresolved ownership, stale snapshot, interrupted migration or invalid historical
resolution MUST fail closed for conclusions that depend on the failed state.

No valid zero-`PENDING` or dependent PASS may be inferred from partial, stale or
untrusted state.

Authorized diagnosis/recovery that does not rely on the failed conclusion remains
permitted.

Recovery MUST use trustworthy evidence, preserve identity/provenance and MUST NOT invent
history or replace the comparison point merely to make a failure disappear.

### MG1?MG5 ? Initial R&D 002 migration contract

Initial reconstruction is bounded to R&D 002 only, from sprint start through mechanism
activation. No automatic migration of earlier historical sprints is approved.

Use existing authoritative/accepted evidence: Chronicle/history, existing material
outcomes, PO decisions, obligations, evidence and applicable Natural Homes.

Migration MUST answer separately:
1. does evidence establish membership as a Known Material Outcome?
2. does evidence establish completion of checkpoint-accounting handling?

Insufficient evidence for (2) leaves the proved outcome `PENDING`.
Insufficient evidence for (1) MUST NOT be used to invent an outcome.

Preserve proved identities and provenance. Do not invent timestamps, approvals or
historical state. Do not automatically promote `FIXED`, `VALIDATED` or
`CLASSIFIED_AND_PERSISTED` to `RESOLVED`.

Before declaring activation complete, there MUST be a trustworthy basis for the bounded
reconstruction and population continuity. Interrupted/partial migration is not complete
activation and MUST NOT justify duplicate identities or completeness claims.

### CP1?CP4 ? Documentation Checkpoint completion contract

Required logical sequence:

1. Validate collection integrity/continuity and review the registered population.
2. Complete applicable handling for registered outcomes.
3. Establish zero registered `PENDING`.
4. Run the independent Accumulated Delta Sweep and applicable Governance checks.
5. Intake omitted Known Material Outcomes discovered by the Sweep as `PENDING` and
   handle them.
6. Re-establish zero registered `PENDING` and accounting integrity.
7. Perform Final Documentation Review.
8. Perform Final Re-grounding and existing continuity controls in their authoritative
   place.
9. Authoritative Closure may occur only after all other applicable requirements pass.

If Review or Re-grounding discovers a new material development, return to intake and
repeat the affected controls. A loop caused by a genuinely new material finding is
legitimate; bookkeeping alone is non-recursive under I5.

Every registered outcome must receive applicable disposition/handling and registered
`PENDING` must be zero before Documentation Checkpoint completion.

Zero registered `PENDING` is NECESSARY but NOT SUFFICIENT for Checkpoint PASS.

The strongest permitted completion claim is:

> For the valid sprint collection at the reviewed version, no registered outcome remains
> PENDING; defined integrity/continuity checks passed; and applicable semantic reviews
> did not identify untreated remainder.

This MUST NOT be represented as mechanical proof that every possible material outcome
was captured.

<!-- /DC-CONTINUOUS-ACCOUNTABILITY-DESIGN-CONTRACT-PO-APPROVED -->
