# SecuQuest — Claude Code 프로젝트 지침

> 이 파일은 Claude Code가 세션 시작 시 자동으로 읽어서 모든 프롬프트에 적용한다.
> 프로젝트 루트(`/mnt/c/study/project/Final-Prj/CLAUDE.md`)에 위치해야 한다.

---

## 1. 프로젝트 개요

- **프로젝트명:** SecuQuest (시큐퀘스트)
- **성격:** 부트캠프 캡스톤 학습 프로젝트 (Topic 05)
- **팀:** 5팀_Security Learning Platform (오현명)
- **목적:** 웹 보안 6대 핵심 취약점 한국어 학습 플랫폼
- **기간:** 2026-08-24 ~ 2026-09-30
- **사용 범위:** 학습 · 부트캠프 발표 · 포트폴리오 (상업적 사용 없음)
- **저장소:** GitHub `Final-Project` (`gusaud9424-source`)
- **로컬 경로:** `/mnt/c/study/project/Final-Prj` (WSL2)
- **작업 위치:** 모노레포. 프론트엔드는 `Final-Prj/frontend/`, 백엔드는 `Final-Prj/backend/`

### 6대 취약점 (범위 고정)
1. Command Injection
2. XSS (DOM / Reflected / Stored)
3. SQL Injection
4. SQL Injection (Blind)
5. File Upload
6. CSRF

---

## 2. 기술 스택 (고정)

### 프론트엔드
- Vue 3 (Composition API + `<script setup>`)
- TypeScript **미사용** — 순수 JavaScript
- Bootstrap 5 (커스텀 SCSS 오버라이드)
- Vue Router 4
- Pinia (상태 관리)
- Axios (`baseURL: /api/v1`)
- Bootstrap Icons
- Pretendard Variable 폰트 (CDN 로드)

### 백엔드 (참고용)
- Python 3.x + Flask 3.x + Gunicorn (WSGI)
- MariaDB (Docker Volume 영속화)
- Redis (세션 · 캐시 · rate limit)
- Nginx (Reverse Proxy · HTTPS · 정적 파일)
- Docker Compose 기반 (Kubernetes 미사용)

### 인증
- 세션 기반 (Redis 세션 스토어)
- bcrypt (salt round 12) 비밀번호 해시
- HttpOnly · Secure · SameSite 쿠키

---

## 3. 사고 방식 및 작업 흐름

- 작업 시작 전 반드시 **계획을 먼저** 세워라.
- 계획 단계는 **한 줄에 다섯 단어 이내**로 요약해라.
- 실제 구현은 계획을 따라 정상적인 코드로 진행해라 (구현 단계까지 압축하지 말 것).
- 파일을 여러 개 만들거나 수정할 때는 **한 번에 하나씩**, 완료 후 다음으로 넘어가라.
- 불확실할 때는 진행 전에 질문하라. 추측으로 임의 값을 만들지 마라.

---

## 4. 디자인 규칙 (매우 중요)

### 참고 자료
- 참고 사이트: 모두의연구소 AX 교육 프로그램 (공개된 UI)
- 참고 캡처 위치: `docs/references/*.png`

### 절대 규칙
- **오직 참고 캡처에서 관찰된 색·간격·radius·그림자만 사용한다.**
- Linear · Vercel · Stripe · Notion · Apple 등 **외부 디자인 시스템의 톤을 학습 편향으로 끌어오지 마라.**
- 모든 색은 `frontend/src/assets/design-tokens.css` 의 `var(--sq-*)` 로만 사용한다.
- **하드코딩된 hex 값 절대 금지** (예: `color: #3b5bff` ❌ → `color: var(--sq-color-accent)` ✅).
- Bootstrap 기본 색상(`--bs-primary` 등)이 그대로 노출되면 안 된다. `frontend/src/assets/bootstrap-overrides.scss` 를 통해 `--sq-*` 토큰으로 오버라이드 후 사용.

### 확정된 디자인 값 (Phase 0~2 결과)
- **primary:** `#3659BE` (참고 캡처 좌표 170,58 픽셀 추출값)
- **페이지 그라데이션:** `linear-gradient(120deg, #DAEBFE 0%, #F9F4CB 60%, #EDF5FF 100%)`
- **card-radius:** 14px
- **font:** Pretendard (CDN)
- **SCSS 오버라이드 원칙:**
  - `$body-bg: transparent` 로 오버라이드 (Bootstrap 기본 흰 배경이 그라데이션 가림 방지)
  - HEX는 `design-tokens.css` 와 `bootstrap-overrides.scss` 양쪽에 동일하게 하드코딩
  - SCSS 변수에 `var(--sq-*)` 넣지 말 것 (Bootstrap 색상 함수 깨짐)

### 브랜딩
- 프로젝트 표기: **SecuQuest** (첫 S와 Q만 대문자, 붙여쓰기)
- 헤더 상단 라벨: `SECU EDUCATION`
- 헤더 메인 텍스트: `SecuQuest 학습 플랫폼`
- 로고: `frontend/src/assets/brand/secuquest-mark.svg` (HTML5 방패 형태 + "S")
- CSS 변수 접두사: `--sq-`

---

## 5. 저작권 · 출처 표기 (필수)

### 원칙
- 레이아웃 구조는 모두의연구소 AX 교육 프로그램의 공개된 UI에서 영감을 받아 재구성했으며, **부트캠프 학습 목적으로만** 사용한다.
- 로고 · 프로젝트명 · 문구 · 아이콘 · 데이터는 모두 SecuQuest 자체 자산이다.
- HTML5 방패 심볼 형태는 W3C 공개 마크에서 영감을 받아 글자를 "S" 로 재해석한 **SecuQuest 오리지널 마크**다.

### 코드 주석 (모든 페이지 컴포넌트 상단에 삽입)

```vue
<!--
  SecuQuest — <컴포넌트 목적 한 줄>
  Layout inspired by publicly viewable UI of Modulabs AX Education,
  reinterpreted for SecuQuest bootcamp capstone (educational use only).
  © 2026 5팀_Security Learning Platform
-->
```

### 화면 푸터 (홈 · 로그인 · 관리자 페이지 하단에 노출)

> SecuQuest는 5팀_Security Learning Platform의 부트캠프 캡스톤 학습 프로젝트입니다.
> © 2026 5팀_Security Learning Platform. All rights reserved.

### 리드미
- 프로젝트 `README.md` 에 위 내용을 요약한 "Attribution" 섹션을 반드시 포함한다.

---

## 6. 파일 구조 규칙

```
Final-Prj/
├── CLAUDE.md                        ← 이 파일
├── DESIGN.md                        ← (선택) 캡처에서 뽑은 디자인 토큰 스펙
├── docs/
│   └── references/                  ← 참고 캡처 PNG
├── frontend/                        ← Vue 프로젝트 루트
│   ├── src/
│   │   ├── assets/
│   │   │   ├── brand/
│   │   │   │   └── secuquest-mark.svg
│   │   │   ├── design-tokens.css
│   │   │   └── bootstrap-overrides.scss
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppHeader.vue
│   │   │   │   └── AppFooter.vue
│   │   │   ├── practice/
│   │   │   │   ├── GradingModal.vue
│   │   │   │   ├── ResultModal.vue
│   │   │   │   └── CodeBlock.vue
│   │   │   └── common/
│   │   │       └── VulnerabilityPage.vue
│   │   ├── views/
│   │   │   ├── DashboardView.vue
│   │   │   ├── ChapterSelectView.vue
│   │   │   ├── ChapterDetailView.vue
│   │   │   ├── AdminView.vue
│   │   │   ├── ResourcesView.vue
│   │   │   ├── NotFoundView.vue
│   │   │   └── LoginView.vue
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── stores/
│   │   │   └── auth.js
│   │   ├── api/
│   │   │   └── client.js            ← Axios (baseURL: /api/v1)
│   │   ├── App.vue
│   │   └── main.js
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/                         ← Flask API
└── scripts/
    └── extract_colors.py            ← Phase 0 색상 추출 스크립트
```

### 네이밍 규칙
- Vue 컴포넌트: **PascalCase** (`AppHeader.vue`, `VulnerabilityPage.vue`)
- 뷰(라우트 대응): `frontend/src/views/*View.vue` 접미사
- 재사용 컴포넌트: `frontend/src/components/**` 하위
- 스토어: `frontend/src/stores/*.js` (Pinia)

### 컴포넌트 재사용 규칙
- 6개 취약점 실습 페이지는 **`VulnerabilityPage.vue` 공통 뼈대**를 감싸고 `#practice` / `#result` / `#explanation` 슬롯만 채우는 패턴을 지킨다.
- 취약점별로 별도 페이지 컴포넌트를 새로 만들지 말 것.

---

## 7. 보안 관련 지침 (실습 페이지 특성상)

- 취약점 실습 페이지는 **의도적으로 취약**하다. Flask-WTF CSRF 토큰 등 표준 보안은 실습 페이지에서만 예외.
- 관리자 · 인증 · 보상 관련 페이지는 **표준 보안 규칙 엄수** (CSRF · Rate Limit · 감사 로그).
- 계좌번호는 AES-256-GCM (Fernet) 암호화 후 저장.
- 실습 격리: Practice Sandbox 컨테이너 (`network=none`, read-only rootfs, non-root user).

---

## 8. 커밋 · Git 규칙

- 브랜치 전략: 개인 브랜치 → main 병합
- **커밋 메시지: Conventional Commits 형식** — `feat(scope): 내용`
  - scope 예시: `style`, `router`, `view`, `layout`, `vuln`, `api`, `auth`, `design`
  - 예시: `feat(router): add vue-router with route stubs`
  - 예시: `feat(style): design tokens, bootstrap overrides, pretendard font`
- 로컬 alias 사용 중: `gs`, `ga`, `gc`, `gp`, `gl`.
- 표준 흐름: pull → work → commit → push.
- 두 환경(교육센터 · 자택) 간 이동 시 반드시 push/pull.

---

## 9. 진행 상태 요약 (참고)

- Week 1 산출물 완료: 프로젝트 헌장 · 요구사항 정의서 · WBS · 벤치마킹 분석
- Week 2 산출물: 설계서 (아키텍처 · 화면 설계 · API 설계)
- Week 3~5: 프론트엔드 · 백엔드 구현 · 테스트 · 발표 준비
- **현재 단계: 프론트엔드 UI 클론 작업 (참고 캡처 기반, 픽셀 파리티)**
  - Phase 0 완료: 색상 추출
  - Phase 1 완료: `design-tokens.css`
  - Phase 2 완료: `bootstrap-overrides.scss` + Pretendard
  - Phase 2.5 완료: 라우터 스텁 + `main.js`/`App.vue` 수정
  - **다음: Phase 3 (AppHeader 픽셀 복제)**

---

## 10. 응답 스타일

- **결론 먼저.** 근거는 요청 시에만 제공.
- **답변은 필요 최소 길이.** 대안 여러 개 제시 금지 (베스트 하나만).
- **불릿 · 헤더 남발 금지.** 짧은 답이면 그냥 문장 한두 줄.
- 코드 주석은 한글, 코드 자체는 영문.
- 설명은 한국어.
- 모호할 때만 확인 질문 → 구현.
- 파일을 만들 때는 `create_file` / `str_replace` 도구를 실제로 호출해서 파일을 저장한다. 코드 블록만 채팅에 출력하고 끝내지 말 것.
