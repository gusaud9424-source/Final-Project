# 02. XSS (DOM) 실습 페이지 (DVWA 재현)

> 기준: DVWA xss_d 재현 · 2026-10-03 오현명

## 1. 한 줄 요약
서버가 값을 안전하게 넘겨도, **브라우저의 JavaScript가 그 값을 위험한 싱크(innerHTML 등)에 넣는 순간** 스크립트가 실행되는 취약점.

## 2. 개념 (비유)
택배회사(서버)는 멀쩡한 상자를 보냈는데, 받는 사람(브라우저)이 내용물을 가스레인지 위에 올려 사고가 난다. 문제는 **받은 쪽이 값을 다루는 방식**.

## 3. 용어
| 용어 | 뜻 |
|---|---|
| DOM | 브라우저가 HTML을 부품으로 쪼갠 문서 구조 |
| 싱크(sink) | 값을 화면에 반영하는 위험한 자리(innerHTML, document.write) |
| textContent | HTML로 해석하지 않고 글자로만 넣음(안전) |

## 4. DVWA 기준 난이도
`?default=` 값을 페이지 JS가 처리한다.

| 단계 | 방식/필터 | 우회 |
|---|---|---|
| Low | document.write, 필터 없음 | `<script>alert(1)</script>` |
| Medium | `<script` 포함 시 차단 | `<img src=x onerror=alert(1)>` |
| High | innerHTML + script·onerror·onload 차단 | `<details open ontoggle=alert(1)>` |
| Impossible | textContent | 불가 |

## 5. 화면 & 동작
- "Please choose a language" + `?default=` 값 입력 + Submit.
- 판정: 격리 iframe에서 스크립트 실행 시 성공.

### 관련 파일
`backend/app/practice_builders/xss_dom.py`, `frontend/src/components/practice/XssPractice.vue`

## 6. 방어
innerHTML/document.write 대신 textContent, 또는 DOMPurify. 필터를 클라이언트 JS에 두면 공격자도 읽고 우회함.

*DVWA 로직 재현. © 2026 5팀_Security Learning Platform*
