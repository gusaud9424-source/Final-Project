# 05. SQL Injection (Blind) 실습 페이지 (DVWA 재현)

> 기준: DVWA sqli_blind 재현 · 2026-10-03 오현명

## 1. 한 줄 요약
조회 결과는 안 보이고 "User ID exists / is MISSING"만 응답할 때, 참/거짓 차이로 admin 비밀번호를 한 글자씩 추론하는 기법.

## 2. 개념 (비유)
상자 속을 못 보지만 "예/아니오"는 물을 수 있는 스무고개. "첫 글자가 a?" → 아니오 … "r?" → 예. 반복해 값을 알아냄.

## 3. 용어
| 용어 | 뜻 |
|---|---|
| Boolean-based Blind | 참/거짓 응답 차이로 추론 |
| SUBSTR(s,n,1) | 문자열의 n번째 글자 |
| exists / missing | 조건을 만족하는 행의 유무 응답 |

## 4. DVWA 기준 난이도
admin은 user_id=1. 비밀번호(4자, 0-9a-f)를 추출 후 제출해 성공 판정.

| 단계 | 쿼리/방어 | 우회(참/거짓 추출) |
|---|---|---|
| Low | `'$id'` | `1' AND SUBSTR(password,1,1)='a' -- ` |
| Medium | `= $id`(숫자) + 드롭다운 | 요청 변조: `0 OR (SELECT SUBSTR(password,1,1) FROM users WHERE user='admin')='a'` |
| High | `'$id' LIMIT 1` | `1' AND SUBSTR(password,1,1)='a' -- ` |
| Impossible | is_numeric + 바인딩 | 불가 |

## 5. 화면 & 동작
- "User ID:" 입력 → exists/missing. 알아낸 비밀번호를 하단에 제출하면 성공.
- 반복 요청이 많아 실행 제한을 90회/분으로 상향(`courses.py`).

### 관련 파일
`backend/app/practice_builders/sql_injection_blind.py`, `frontend/.../BlindSqlPractice.vue`

## 6. 방어
파라미터 바인딩 + 에러·응답 차이 최소화 + 요청 속도 제한.

*DVWA 로직 재현(격리 SQLite). © 2026 5팀_Security Learning Platform*
