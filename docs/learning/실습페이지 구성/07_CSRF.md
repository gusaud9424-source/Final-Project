# 07. CSRF 실습 페이지 (DVWA 재현)

> 기준: DVWA csrf(비밀번호 변경) 재현 · 2026-10-03 오현명

## 1. 한 줄 요약
피해자가 로그인된 상태에서, 외부 사이트가 보낸 **위조 요청**으로 피해자 몰래 비밀번호를 바꾸는 취약점.

## 2. 개념 (비유)
은행에 로그인된 채로 수상한 사이트를 열면, 그 사이트의 숨은 양식이 "내 계좌에서 송금" 요청을 **내 이름으로** 자동 제출한다. 서버가 "이 요청이 우리 사이트에서 온 게 맞나"를 확인 안 하면 그대로 처리됨.

## 3. 용어
| 용어 | 뜻 |
|---|---|
| CSRF | 피해자 권한으로 위조 요청을 실행시키는 취약점 |
| Referer | 요청이 어느 페이지에서 왔는지 알려주는 헤더 |
| Anti-CSRF 토큰 | 정상 페이지에만 심는 일회용 값(위조 요청은 모름) |
| SameSite 쿠키 | 교차 사이트 요청에 쿠키를 안 붙이는 방어 |

## 4. DVWA 소스 기준 난이도
대상: 연습용 비밀번호(세션). "위조 요청 전송"이 레벨 방어를 뚫고 바꾸면 성공.

| 단계 | DVWA 방어 | 우회 |
|---|---|---|
| Low | 없음 | 외부 폼으로 바로 변경 |
| Medium | Referer에 호스트 포함 검사(stripos) | Referer를 `http://localhost:8090/...`로 위조 |
| High | Anti-CSRF 토큰 필요 | 토큰 유출(XSS 등) 후 요청에 포함 |
| Impossible | 현재 비밀번호 재확인 + 토큰 | 현재 비밀번호를 몰라 불가 |

## 5. 화면 & 동작
- "외부 공격 사이트(evil.example)에서 보내는 위조 요청" 패널: New password + (레벨별) Referer/user_token/현재 비밀번호.
- High는 "토큰 유출(XSS 시뮬)" 버튼으로 토큰을 얻어 넣는다.
- 판정: 위조 요청이 방어를 뚫고 비밀번호를 바꾸면 성공. Impossible은 차단.

### 관련 파일
`backend/app/practice_builders/csrf.py`, `frontend/src/components/practice/CsrfPractice.vue`

## 6. 방어
Anti-CSRF 토큰 + SameSite 쿠키 + 민감 작업 시 현재 비밀번호 재확인. Referer 검사만으론 위조 가능.

*DVWA 로직 재현. © 2026 5팀_Security Learning Platform*
