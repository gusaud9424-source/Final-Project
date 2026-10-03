# 04. SQL Injection 실습 페이지 (DVWA 재현)

> 기준: DVWA sqli 소스 재현 · 2026-10-03 오현명

## 1. 한 줄 요약
User ID 입력이 SQL 쿼리에 그대로 결합되어, UNION 등으로 users 테이블의 로그인·비밀번호 해시를 통째로 끌어내는 취약점.

## 2. 개념 (비유)
사서에게 "제목이 ___인 책 주세요" 쪽지를 주는데, 빈칸에 "없는책 그리고 회원명부 전체"라 적으면 사서가 그대로 실행. 데이터와 명령이 한 문장에 섞인 게 원인.

## 3. 용어
| 용어 | 뜻 |
|---|---|
| UNION SELECT | 두 조회 결과를 세로로 이어 붙임(다른 컬럼 추출) |
| `--` | SQL 주석(뒤를 무시, LIMIT 제거 등) |
| 파라미터 바인딩 | 입력을 값으로만 전달해 구조와 분리(정답 방어) |

## 4. DVWA 소스 기준 난이도
쿼리: `SELECT first_name, last_name FROM users WHERE user_id = ...` · 출력 "ID/First name/Surname". admin의 password가 추출 목표.

| 단계 | DVWA 쿼리/방어 | 우회 |
|---|---|---|
| Low | `'$id'` (문자열) | `' UNION SELECT user, password FROM users -- ` |
| Medium | `= $id` (숫자) + 이스케이프 + **드롭다운** | DevTools/Burp로 요청 변조: `0 UNION SELECT user, password FROM users` |
| High | `'$id' LIMIT 1` (세션 입력) | `' UNION SELECT user, password FROM users -- ` (주석으로 LIMIT 제거) |
| Impossible | is_numeric + 파라미터 바인딩 | 불가 |

- **Medium**: 드롭다운이라 화면에선 1~5만 전송 → **요청 변조**가 필수. 숫자 컨텍스트라 따옴표 불필요.
- **High**: `LIMIT 1`을 `--` 주석으로 잘라 여러 행 덤프.

## 5. 화면 & 동작
- DVWA "User ID:" 입력(Medium은 드롭다운) + Submit.
- 판정: 결과에 admin의 password(일회용 flag)가 나오면 성공. 정상 조회로는 password 컬럼이 안 나옴.

### 관련 파일
`backend/app/practice_builders/sql_injection.py`, `sandbox/runner.py`(sqlite), `frontend/.../SqlInjectionPractice.vue`

## 6. 방어
파라미터 바인딩(Prepared Statement) + 최소 권한 DB 계정. 이스케이프·숫자 컨텍스트만으론 부족.

*DVWA 로직 재현(격리 SQLite). © 2026 5팀_Security Learning Platform*
