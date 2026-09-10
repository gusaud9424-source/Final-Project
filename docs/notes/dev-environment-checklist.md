# 개발환경 세팅 체크리스트

| # | 항목 | 상태 | 확인 명령 |
|---|---|---|---|
| 1 | WSL2 (Ubuntu) | ✅ | `uname -r` |
| 2 | Docker Engine + Compose v2 | ✅ | `docker --version && docker compose version` |
| 3 | docker-compose.yml (5서비스) | ✅ | `docker compose config --services` |
| 4 | 컨테이너 기동/헬스체크 | ✅ | `docker compose ps` |
| 5 | Nginx 라우팅 (/api /pdf /practice) | ✅ | `curl localhost:8090/api/health`<br>`curl localhost:8090/pdf/health`<br>`curl localhost:8090/practice/health` |
| 6 | MariaDB 스키마+시드 (Flask-Migrate) | ✅ | `docker compose exec db mariadb -uappuser -papppass webseclab -e "SELECT * FROM users;"` |
| 7 | Redis 세션 연동 | ✅ | `curl -b/-c cookie localhost:8090/api/session-test` (hits 증가 확인) |
| 8 | Sandbox 격리 (network=none, read-only) | ✅ | `docker inspect final-prj-sandbox-1 --format '{{.HostConfig.NetworkMode}} {{.HostConfig.ReadonlyRootfs}}'` → `none true` |
| 9 | GitHub 브랜치 전략 + 초기 커밋 | ✅ | `git branch -a` → main, develop / `git log --oneline` |
| 10 | 아키텍처 다이어그램 | ✅ | `docs/architecture/architecture.md` (개인 프로젝트 → 셀프 확정) |

## 현재 상태

```
docker compose ps
NAME                   STATUS
final-prj-backend-1    Up
final-prj-db-1         Up (healthy)
final-prj-frontend-1   Up
final-prj-nginx-1      Up (8090:80)
final-prj-redis-1      Up (healthy)
final-prj-sandbox-1    Up
```

## 포트

- Nginx 진입점: `localhost:8090` (8080/8081은 기존 프로세스 점유로 회피)

## 서비스 구성

| 서비스 | 이미지/빌드 | 내부 포트 | 비고 |
|---|---|---|---|
| nginx | nginx:1.27-alpine | 80 | 리버스 프록시, 호스트 노출 8090 |
| frontend | ./frontend (Vue+Vite) | 5173 | dev 서버 |
| backend | ./backend (Flask) | 5000 | SQLAlchemy, Flask-Migrate, Flask-Session(Redis) |
| db | mariadb:11.4 | 3306 | 볼륨 `dbdata`로 영속화 |
| redis | redis:7-alpine | 6379 | 세션 저장소 |
| sandbox | ./sandbox | - | network=none, read-only, cap_drop=ALL, tmpfs /tmp |

## 재현 방법

```bash
cp .env.example .env
docker compose up -d
docker compose exec backend flask db upgrade
docker compose exec backend python seed.py
```
