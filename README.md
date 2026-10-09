# SecuQuest (시큐퀘스트)

> 웹 보안 6대 핵심 취약점을 **직접 공격해 보고, 막는 법까지** 배우는 한국어 학습 플랫폼
> 부트캠프 캡스톤 학습 프로젝트 (Topic 05) · 5팀_Security Learning Platform

---

## 목차

1. [소개](#소개)
2. [주요 기능](#주요-기능)
3. [기술 스택](#기술-스택)
4. [시스템 구조](#시스템-구조)
5. [빠른 시작](#빠른-시작)
6. [프로젝트 구조](#프로젝트-구조)
7. [보안 설계](#보안-설계)
8. [문서](#문서)
9. [Attribution (출처)](#attribution-출처)

---

## 소개

SecuQuest는 웹 보안을 처음 배우는 학습자를 위한 실습형 플랫폼입니다. 과목마다 **개념 학습 → 단계별 실습(하 → 중 → 상 → 안전) → 퀴즈 → 미션 보상**의 흐름으로 진행됩니다. 실습 코드는 격리된 Sandbox 컨테이너에서만 실행됩니다.

| # | 학습 범위 (고정) |
|---|---|
| 1 | Command Injection |
| 2 | XSS (DOM / Reflected / Stored) |
| 3 | SQL Injection |
| 4 | SQL Injection (Blind) |
| 5 | File Upload |
| 6 | CSRF |

- **기간:** 2026-08-24 ~ 2026-09-30 (이후 발표 전 보완 진행)
- **사용 범위:** 학습 · 부트캠프 발표 · 포트폴리오 (상업적 사용 없음)

---

## 주요 기능

| 구분 | 기능 |
|---|---|
| 회원 | 회원가입 · 로그인(학생/관리자 역할 구분) · 아이디 찾기(이메일/휴대폰 SMS) · 비밀번호 재설정 · **마이페이지(회원정보 · 비밀번호 변경)** |
| 학습 | 수강신청 · 과목 상세(정보 / 개념 / 실습 / 미션 탭) · 개념 확인 문제 · 50문항 퀴즈 세트 |
| 실습 | 취약점별 실습 페이지, 레벨 순차 잠금(하→중→상→안전), 단계별 힌트 공개 |
| 동기부여 | 경험치 · 레벨, 포인트, 레벨별 클리어 보상, 보물상자 수령, 14일 출석 체크판 |
| 진도 | 과목별 진도율, 학습 대시보드 |
| 관리자 | 회원관리(검색 · 임시 비밀번호 발급 · 삭제), 전체 학생 현황, 학생 개인 현황, 관리자 비밀번호 변경 |
| 자료실 | 취약점별 학습 문서 내려받기 |

---

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 프론트엔드 | Vue 3 (Composition API, `<script setup>`, JavaScript) · Vite · Vue Router 4 · Pinia · Axios · Bootstrap 5 (SCSS 오버라이드) · Bootstrap Icons · Pretendard |
| 백엔드 | Python 3.12 · Flask 3 · Flask-SQLAlchemy · Flask-Migrate · Flask-Session · Flask-WTF(CSRF) · Flask-Limiter · bcrypt |
| 데이터 | MariaDB 11.4 (Docker Volume) · Redis 7 (세션 · Rate Limit) |
| 인프라 | Docker Compose · Nginx 1.27 (Reverse Proxy) · Practice Sandbox 컨테이너 |
| 외부 연동 | Gmail SMTP (이메일 인증코드) · Solapi (SMS 인증코드) |

---

## 시스템 구조

```
                ┌──────────────── Docker Compose (webnet) ────────────────┐
 Browser ─▶ Nginx :8090 ─┬─ /      ─▶ frontend (Vite dev :5173)
 (127.0.0.1)             └─ /api/  ─▶ backend  (Flask :5000) ─┬─▶ MariaDB
                                                              ├─▶ Redis
                                                              └─▶ sandbox (network=none)
                └──────────────────────────────────────────────────────────┘
```

- 모든 포트는 `127.0.0.1` 에만 바인딩됩니다 (외부 노출 없음).
- API 기본 경로: `/api/v1`
- 실습 코드 실행은 공유 볼륨(`sandbox_ipc`)으로 Sandbox 컨테이너에 전달됩니다.

---

## 빠른 시작

### 1. 준비물

- Docker Desktop (Docker Compose v2 포함)
- Git

### 2. 내려받기 · 환경 변수

```bash
git clone https://github.com/gusaud9424-source/Final-Project.git
cd Final-Project

cp .env.example .env                  # DB · Redis · SECRET_KEY
cp backend/.env.example backend/.env  # SMTP · SMS · 시드 계정 연락처 (비워도 실행 가능)
# (선택) 개발용 디버그 모드
cp docker-compose.override.yml.example docker-compose.override.yml
```

> `.env` 의 `SECRET_KEY`, DB 비밀번호는 반드시 본인 값으로 바꾸세요.
> SMTP · SMS 값을 비워 두면 인증코드 발송만 실패하고(서버 로그에 경고), 나머지 기능은 동작합니다.

### 3. 실행

```bash
docker compose up -d --build
docker compose exec backend flask db upgrade   # DB 테이블 생성
docker compose exec backend python seed.py     # 과목 · 기본 계정 생성
```

브라우저에서 **http://localhost:8090** 접속

### 4. 기본 계정

`seed.py` 가 아래 계정을 만들고, **비밀번호는 실행 시 콘솔에 한 번만 출력**합니다(무작위 생성).

| 아이디 | 역할 | 비고 |
|---|---|---|
| `admin` | 관리자 | 회원관리 · 학생 현황 |
| `student1` | 학생 | 일반 학습자 |
| `demo1` | 학생 | 시연용 학습자 |

- 학생 비밀번호를 고정하려면 `backend/.env` 의 `SEED_STUDENT_PASSWORD` 를 지정합니다.
- 비밀번호를 잊었다면: `docker compose exec backend flask set-password --username admin`
- 새 학생 계정은 로그인 화면의 **회원가입**으로 만들 수 있습니다.

### 5. 상태 확인

```bash
docker compose ps
curl http://localhost:8090/api/health
```

---

## 프로젝트 구조

```
Final-Project/
├── CLAUDE.md                 # 프로젝트 지침 (디자인 · 보안 · 커밋 규칙)
├── docker-compose.yml
├── nginx/nginx.conf          # Reverse Proxy
├── sandbox/                  # 실습 코드 격리 실행 컨테이너
├── backend/
│   ├── app/
│   │   ├── auth.py           # 로그인 · 회원가입 · 아이디/비밀번호 찾기
│   │   ├── profile.py        # 프로필 · 마이페이지(회원정보 · 비밀번호 변경)
│   │   ├── courses.py        # 과목 · 실습 · 퀴즈
│   │   ├── practice_builders/  # 취약점별 실습 생성기
│   │   ├── quiz_bank/        # 취약점별 퀴즈 문항
│   │   ├── rewards.py        # 경험치 · 포인트 · 보상
│   │   ├── attendance.py     # 출석 체크
│   │   ├── admin.py          # 관리자 기능
│   │   └── models.py
│   ├── migrations/           # Alembic 마이그레이션
│   └── seed.py
├── frontend/
│   └── src/
│       ├── assets/           # design-tokens.css · bootstrap-overrides.scss
│       ├── components/       # layout · practice · dashboard · admin · auth
│       ├── views/            # *View.vue (라우트 화면)
│       ├── stores/           # Pinia
│       ├── router/
│       └── api/client.js     # Axios (baseURL: /api/v1, CSRF 자동 첨부)
└── docs/                     # 설계 · API · 작업 기록 · 개념 설명
```

---

## 보안 설계

> ⚠️ **실습 페이지는 학습을 위해 의도적으로 취약하게 만들어졌습니다.** 외부 네트워크에 공개하지 말고 로컬에서만 실행하세요.

| 영역 | 적용 내용 |
|---|---|
| 실습 격리 | Sandbox 컨테이너: `network=none` · read-only rootfs · `cap_drop: ALL` · `no-new-privileges` · 메모리 128MB · PID 64 · CPU 0.5 · `/tmp` 16MB · XSS 실습은 iframe sandbox |
| 인증 | Redis 세션, 로그인 · 비밀번호 변경 시 세션 ID 재발급, bcrypt(salt round 12) |
| 쿠키 | HttpOnly · SameSite=Lax · 운영 모드에서 Secure |
| 요청 위조 | Flask-WTF CSRFProtect (실습 페이지 제외), Axios 가 `X-CSRFToken` 자동 첨부 |
| 남용 방지 | Flask-Limiter (로그인 분당 10회, 가입 · 인증코드 · 정보 변경 분당 5회) |
| 계정 보호 | 아이디 찾기 · 비밀번호 찾기 응답에서 가입 여부 비노출, 인증코드 5분 만료 · 5회 오답 무효, 정보 변경 시 현재 비밀번호 재확인 |
| 권한 | 역할은 서버가 결정(가입 시 `student` 고정), 관리자 API 역할 검사 |
| 감사 로그 | 관리자 작업 · 회원정보 변경 · 비밀번호 변경을 `[AUDIT]` 로그로 기록 (개인정보 값은 기록하지 않음) |

---

## 문서

| 위치 | 내용 |
|---|---|
| `docs/architecture/` | 시스템 아키텍처 |
| `docs/api/` | API 명세 |
| `docs/erd/` | DB 설계 |
| `docs/worklog/` | 단계별 작업 기록 |
| `docs/learning/` | 기능별 작업 기록 + 입문자용 개념 설명 |
| `docs/notes/` | 개발 환경 점검표 · 기능 점검 |

---

## Attribution (출처)

### 디자인 · 브랜드

- **레이아웃:** 화면 레이아웃 구조는 **모두의연구소(Modulabs) AX 교육 프로그램의 공개된 UI**에서 영감을 받아 SecuQuest에 맞게 재구성했습니다. 부트캠프 학습 목적으로만 사용하며, 원본의 코드 · 이미지 · 문구는 사용하지 않았습니다.
- **로고:** HTML5 방패 심볼 형태는 **W3C의 공개 HTML5 마크**에서 영감을 받아, 글자를 "S"로 재해석한 **SecuQuest 오리지널 마크**입니다.
- **자체 자산:** 로고 · 프로젝트명 · 문구 · 아이콘 구성 · 학습 콘텐츠 · 데이터는 모두 SecuQuest 자체 자산입니다.
- 모든 페이지 컴포넌트 상단에 출처 주석이 들어 있고, 홈 · 로그인 · 관리자 화면 하단 푸터에 저작권 문구를 표시합니다.

### 오픈소스 · 폰트

| 이름 | 용도 | 라이선스 |
|---|---|---|
| [Vue](https://vuejs.org/) · [Vue Router](https://router.vuejs.org/) · [Pinia](https://pinia.vuejs.org/) · [Vite](https://vitejs.dev/) | 프론트엔드 프레임워크 · 빌드 | MIT |
| [Bootstrap](https://getbootstrap.com/) · [Bootstrap Icons](https://icons.getbootstrap.com/) | UI 컴포넌트 · 아이콘 | MIT |
| [Axios](https://axios-http.com/) | HTTP 클라이언트 | MIT |
| [Pretendard](https://github.com/orioncactus/pretendard) | 본문 폰트 (jsDelivr CDN) | SIL Open Font License 1.1 |
| [Flask](https://flask.palletsprojects.com/) 및 확장(SQLAlchemy · Migrate · Session · WTF · Limiter) | 백엔드 | BSD-3-Clause / MIT |
| [MariaDB](https://mariadb.org/) · [Redis](https://redis.io/) · [Nginx](https://nginx.org/) | DB · 세션 저장소 · 프록시 (Docker 이미지) | 각 프로젝트 라이선스 |

### 학습 참고

- 취약점 분류와 방어 원칙은 [OWASP Top 10](https://owasp.org/www-project-top-ten/) 등 공개 자료를 참고해 한국어로 새로 작성했습니다.

### 저작권

> SecuQuest는 5팀_Security Learning Platform의 부트캠프 캡스톤 학습 프로젝트입니다.
> © 2026 5팀_Security Learning Platform. All rights reserved.
