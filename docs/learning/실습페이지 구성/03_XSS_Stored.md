# 03. XSS (Stored) 실습 페이지 (DVWA 재현)

> 기준: DVWA xss_s(Guestbook) 재현 · 2026-10-03 오현명

## 1. 한 줄 요약
방명록(Name/Message)에 저장된 스크립트가 그 글을 보는 **모든 사용자** 브라우저에서 실행되는, 가장 위험한 XSS.

## 2. 개념 (비유)
벽에 몰래 독을 발라두면 그 벽을 만지는 모든 사람이 당한다. 한 번 저장 → 반복 피해. 관리자가 글 목록을 열다 당하면 권한 탈취로 이어짐.

## 3. 용어
| 용어 | 뜻 |
|---|---|
| Stored/Persistent XSS | 저장되어 여러 사용자에게 반복 실행되는 유형 |
| strip_tags | 태그를 제거하는 함수(Message에 적용) |

## 4. DVWA 기준 난이도 (벡터가 Name/Message로 나뉨)
DVWA는 Name·Message를 다르게 처리한다.

| 단계 | Message | Name | 벡터·우회 |
|---|---|---|---|
| Low | 거의 그대로 | 그대로 | **Message**: `<script>alert(1)</script>` |
| Medium | strip_tags+인코딩(안전) | `str_replace('<script>','')` | **Name**: `<img src=x onerror=alert(1)>` |
| High | 안전 | preg_replace(script류) | **Name**: `<img src=x onerror=alert(1)>` |
| Impossible | 인코딩 | 인코딩 | 불가 |

## 5. 화면 & 동작
- DVWA Guestbook: **Name** + **Message** 입력 + Sign Guestbook → 목록에 "Name: / Message:".
- 판정: 격리 iframe에서 스크립트 실행 시 성공. "방명록 비우기"로 초기화.

### 관련 파일
`backend/app/practice_builders/xss_stored.py`, `frontend/src/components/practice/StoredXssPractice.vue`

## 6. 방어
저장·출력 양쪽 인코딩 + 검증된 새니타이저(DOMPurify). 한 지점만 막으면 우회로가 남음.

*DVWA 로직 재현. © 2026 5팀_Security Learning Platform*
