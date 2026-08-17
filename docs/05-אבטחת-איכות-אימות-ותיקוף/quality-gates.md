# Quality Gates

Quality Gate מונע משינוי להתקדם לשלב הבא לפני שהוכח שהוא עומד בתנאים שהוגדרו.

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

## לפני סגירת ספרינט

- הערך שהוגדר לספרינט סופק.
- Scope נשמר.
- Verification עבר.
- Validation בוצע כאשר נדרש.
- Repository נמצא במצב ידוע ונקי.
- Documentation Checkpoint הושלם.

## עיקרון

Quality Gate אינו טקס.

מטרתו להעביר את Stock Sentinel ממצב יציב ומאומת אחד למצב יציב ומאומת חדש.
