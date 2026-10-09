# 01. 불필요한 파일 · API · Nginx 경로 정리

> 작성: 2026-10-09 · 오현명
> 관련: 기능 점검표 #10 · #11 · #12

---

## 1. 요약

발표 전 저장소와 서버에서 **쓰이지 않는데 남아 있으면 오해 · 공격 면(attack surface)만 늘리는 것** 3가지를 지웠다.

| # | 삭제한 것 | 위치 | 이유 |
|---|---|---|---|
| 10 | `csrf_test.html` | 프로젝트 루트 (git 추적) | 열면 `localhost:8080/WebGoat/csrf/review` 로 **자동 제출되는 CSRF 공격 PoC**. 서비스와 무관하고, 저장소를 본 사람이 "공격 코드가 포함된 프로젝트"로 오해할 수 있음 |
| 11 | `GET /api/session-test` | `backend/app/routes.py` | 호출할 때마다 세션 값(`hits`)을 증가시키는 **초기 Redis 세션 점검용 디버그 API**. 화면에서 호출하지 않음 |
| 12 | `GET /pdf/health`, `GET /practice/health` + Nginx `location /pdf/`, `location /practice/` | `routes.py`, `nginx/nginx.conf` | 초기 설계의 빈 모듈 확인용. 실제 실습 · 자료실은 모두 `/api/v1/...` 사용 |

서버 상태 확인은 **`GET /api/health` 하나만** 남겼다.

---

## 2. 왜 지워야 하나 (개념)

- **공격 면 최소화**: 쓰지 않는 API 도 인터넷에 열려 있으면 공격자가 두드릴 수 있는 문이다. 특히 디버그 API 는 인증 · Rate Limit 없이 만들어지는 경우가 많다(`/api/session-test` 도 둘 다 없었음).
- **설정 단순화**: Nginx 경로가 줄면 보안 헤더를 붙일 곳도 줄어 실수할 여지가 작아진다.
- **저장소 신뢰도**: 보안 학습 플랫폼 저장소에 다른 사이트를 공격하는 HTML 이 있으면 발표 · 포트폴리오 검토 때 질문 대상이 된다. 실습 코드는 격리된 실습 페이지 안에만 둔다.

---

## 3. 변경 내용

| 파일 | 변경 |
|---|---|
| `csrf_test.html` | 삭제 (`git rm`) |
| `backend/app/routes.py` | `/api/health` 만 남김 (session · 2개 health 삭제) |
| `nginx/nginx.conf` | `location /pdf/`, `location /practice/` 블록 삭제 → 해당 주소는 앱(Vue)으로 가서 404 화면 표시 |
| `docs/notes/dev-environment-checklist.md` | 점검 명령에서 삭제된 경로 정리 |
| `docs/learning/보안 헤더와 404/*` | 경로별 헤더 표에서 `/pdf/` · `/practice/` 제거 |

> 참고: XSS 실습 프레임 경로 `/practice-frame.html` 은 `location /practice/` 와 **다른 경로**(슬래시 없음)라 영향 없다.
> 과거 작업 기록(`docs/worklog/*`, `git-작업기록_2026-09-10.md`)은 당시 기록이므로 수정하지 않았다.

---

## 4. 확인

| 확인 | 결과 |
|---|---|
| `GET /api/health` | 200 ✅ |
| `GET /api/session-test` · `/pdf/health` · `/practice/health` (Flask) | 404 ✅ |
| `nginx -t` (수정된 설정) | syntax ok ✅ |

### 직접 적용하는 방법

```bash
docker compose restart nginx        # nginx.conf 변경 반영
curl -s http://localhost:8090/api/health               # {"module":"api","status":"ok"}
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8090/api/session-test   # 404
```

`/pdf/health` · `/practice/health` 를 브라우저로 열면 SecuQuest 404 화면(로그인 상태) 또는 로그인 화면이 나온다.

---

*© 2026 5팀_Security Learning Platform (부트캠프 캡스톤 학습용)*
