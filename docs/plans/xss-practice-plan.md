# XSS 실습 계획 (보류)

> 상태: 보류. 코드 미구현. 재개 시 이 문서를 기준으로 진행.
> 결정 사항: flag 토큰·stored 게시물 모두 **세션 저장**(DB 테이블 신규 생성 없음).

## A. 재사용 요소 vs XSS 전용 신규 요소

**그대로 재사용**
- `courses.py`의 `/api/v1/courses/<slug>/practice/run`, `/practice/hints` — `PRACTICE_BUILDERS.get(course.slug)` 기반이라 슬러그 제네릭. XSS 빌더만 등록하면 라우트 코드 변경 없음.
- `rewards.py` 보상 로직 — `XP_RANGES`/`POINT_RANGES`는 source(practice/mission) 기준. `MISSION_REWARD_TYPE`에 `xss-reflected`/`xss-dom`/`xss-stored` 이미 등록됨(수정 불필요).
- `ChapterDetailView.vue`의 `PRACTICE_SUPPORTED_SLUGS` 게이팅 배열 + `practiceSupported` computed — 3개 슬러그 추가만.
- `VulnerabilityPage.vue` 공통 뼈대(실습/결과/설명 슬롯) — 그대로.
- `#explanation` 슬롯의 `detail.exploit`/`detail.defense` — `enroll.js`에 3개 슬러그 모두 이미 채워져 있음.
- `PracticeBuilder` 베이스 클래스(`validate_input`/`run`/`hints`) 인터페이스 — 그대로 상속.

**XSS 전용 신규**
- CI는 `sandbox_client.py`(유닉스 소켓 → OS 샌드박스)로 서버가 명령을 대신 실행해 성공 판정. XSS는 브라우저 실행이 성립 조건이라 이 경로를 그대로 못 씀 (B 참고).

## B. 샌드박스 명령 실행 vs 격리 iframe — 판단: iframe 격리로 충분, `sandbox_client` 불필요

- `sandbox_client.py`는 OS 프로세스(셸 명령) 격리용. XSS는 서버가 아니라 피해자 브라우저에서 스크립트가 실행되는 취약점이라 위협 모델이 다름 — OS 샌드박스 재사용은 과설계.
- `<iframe sandbox="allow-scripts">`(`allow-same-origin` 미포함)로 렌더링. 매 로드마다 opaque origin이 부여되어 주입 스크립트가 앱의 실제 세션 쿠키·localStorage·SameSite 인증 요청에 접근 불가.
- `v-html` 금지 원칙(프로젝트 공통 규칙) 때문에도 reflected/stored 결과를 메인 앱에 직접 꽂는 방식은 불가 — iframe 격리가 유일한 선택지.
- **성공 판정**: CI의 "서버가 flag 파일을 읽어 stdout에 있으면 성공" 철학을 브라우저 컨텍스트로 확장. 서버가 시도별 랜덤 flag 토큰을 발급(세션 저장)하고 취약 페이지 안에만 심어둠 → 주입 스크립트 실행 시 `postMessage`로 부모(Vue 앱)에 flag 전달 → 앱이 `/practice/run`에 캡처한 flag 문자열을 `input`으로 제출 → 서버가 세션에 저장된 발급값과 비교해 `PracticeResult(success=...)` 반환. `run()`/`validate_input()` 인터페이스는 유지, 내용만 "명령 실행" 대신 "flag 비교"로 대체.

## C. 1개 과목 vs 3개 과목 — 3개 과목 확인

`seed.py:49-54`, `course_content.py`(DEFENSE_QUIZZES), `rewards.py:MISSION_REWARD_TYPE`, `enroll.js` 모두 `xss-reflected`/`xss-dom`/`xss-stored` 독립 slug·title·난이도·설명으로 등록. 탭 전환이 아니라 과목별 개별 화면.

라우트는 CI와 동일하게 `/chapters/:id`(기존, 슬러그 제네릭) 하나만 재사용. "개별 화면"은 `ChapterDetailView.vue` 안에서 slug별 하위 컴포넌트 렌더링으로 구현.

## D. 새로 만들 파일 (미착수)

| 경로 | 역할 |
|---|---|
| `backend/app/practice_builders/xss_reflected.py` | flag 발급(세션) + `/practice/run` 제출값 검증 |
| `backend/app/practice_builders/xss_dom.py` | 〃 |
| `backend/app/practice_builders/xss_stored.py` | 〃 + 게시물도 세션 저장(임시 리스트, DB 테이블 없음) |
| `backend/app/xss_pages.py` | 취약 페이지 서빙용 신규 블루프린트(reflected 에코, stored 게시판) — `courses.py` 비수정 |
| `frontend/public/practice/xss-dom.html` | DOM XSS는 100% 클라이언트 로직 — 정적 HTML로 iframe에 직접 로드, 백엔드 불필요 |
| `frontend/src/components/practice/XssSandboxFrame.vue` | 3종 공통 격리 iframe 래퍼(`sandbox="allow-scripts"`, flag postMessage 수신) |
| `frontend/src/components/practice/xss/XssReflectedPractice.vue` | reflected 입력 폼 + iframe |
| `frontend/src/components/practice/xss/XssDomPractice.vue` | dom 입력 폼 + iframe |
| `frontend/src/components/practice/xss/XssStoredPractice.vue` | stored 입력 폼 + iframe |

## E. 기존 파일 변경 (미착수, 예정 diff)

```diff
--- a/backend/app/practice_builders/__init__.py
+++ b/backend/app/practice_builders/__init__.py
 from .command_injection import CommandInjectionBuilder
+from .xss_reflected import XssReflectedBuilder
+from .xss_dom import XssDomBuilder
+from .xss_stored import XssStoredBuilder

 PRACTICE_BUILDERS = {
     "command-injection": CommandInjectionBuilder(),
+    "xss-reflected": XssReflectedBuilder(),
+    "xss-dom": XssDomBuilder(),
+    "xss-stored": XssStoredBuilder(),
 }
```

```diff
--- a/backend/app/__init__.py
+++ b/backend/app/__init__.py
+    app.register_blueprint(xss_pages_bp)
```

```diff
--- a/frontend/src/views/ChapterDetailView.vue
+++ b/frontend/src/views/ChapterDetailView.vue
-const PRACTICE_SUPPORTED_SLUGS = ["command-injection"];
+const PRACTICE_SUPPORTED_SLUGS = ["command-injection", "xss-reflected", "xss-dom", "xss-stored"];
```
`#practice` 슬롯: 기존 CI `<template v-if="practiceSupported">` 폼은 수정하지 않고, slug 분기(`v-else-if slug==='xss-reflected'` 등)로 3개 XSS 컴포넌트를 추가 렌더링.

## 미결정 사항(재개 시 먼저 확정)
- flag 토큰 세션 키 이름·만료 시점 — 재개 시 상세 설계
- xss-stored 세션 저장 게시물의 최대 개수/초기화 시점(세션 만료 시 소멸로 충분한지)
