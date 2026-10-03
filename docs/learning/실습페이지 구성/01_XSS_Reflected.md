# 01. XSS (Reflected) 실습 페이지 (DVWA 재현)

> 대상: 웹 보안 입문자 · 기준: DVWA xss_r 소스 재현 · 2026-10-03 오현명

## 1. 한 줄 요약
입력한 이름이 응답 HTML에 그대로 반사되어("Hello {name}") 그 안의 스크립트가 피해자 브라우저에서 실행되는 취약점.

## 2. 개념 (비유)
안내데스크에 이름을 적으면 직원이 "○○님 환영합니다"를 **그대로 전광판에 띄운다**. 이름 대신 명령을 적으면 전광판이 그 명령을 실행한다. 저장 안 되고 그 순간만 반사 → Reflected.

## 3. 용어
| 용어 | 뜻 |
|---|---|
| XSS | 남의 브라우저에서 내 스크립트를 실행시키는 취약점 |
| Reflected | 입력이 저장 없이 즉시 응답에 반사되는 유형 |
| 이벤트 속성 | `onerror` 등 특정 상황에 자동 실행되는 HTML 속성 |
| htmlspecialchars | `<`→`&lt;` 로 바꿔 태그를 글자로 만드는 출력 인코딩 |

## 4. DVWA 소스 기준 난이도
DVWA는 `Hello {name}` 으로 echo 한다.

| 단계 | DVWA 필터 | 우회 |
|---|---|---|
| Low | 없음 | `<script>alert(1)</script>` |
| Medium | `str_replace('<script>','')` (소문자만) | `<SCRIPT>...` 또는 `<img src=x onerror=alert(1)>` |
| High | `preg_replace('/<(.*)s(.*)c(.*)r(.*)i(.*)p(.*)t/i','')` | `<img src=x onerror=alert(1)>` |
| Impossible | `htmlspecialchars()` | 불가 |

## 5. 화면 & 동작
- DVWA "What's your name?" 입력 + Submit → "Hello {name}".
- 판정: 격리 iframe 안에서 주입 스크립트가 실행되면(일회용 flag가 부모로 전달) 성공. (SPA 안전을 위해 iframe 격리 — 이 점만 DVWA와 다름)

### 관련 파일
`backend/app/practice_builders/xss_reflected.py`, `frontend/src/components/practice/XssPractice.vue`

## 6. 방어
출력 시점 컨텍스트별 이스케이프(htmlspecialchars) + CSP. 블랙리스트 태그 제거는 대소문자·이벤트 속성으로 우회됨.

*DVWA 로직 재현. © 2026 5팀_Security Learning Platform*
