# 01. Sandbox 격리 점검

> 대상: 웹 보안을 처음 배우는 입문자
> 목표: 실습 공격이 실제로 성공해도 서비스 서버와 회원 DB가 안전한 이유를 설정과 점검 결과로 설명할 수 있다.
> 작성: 2026-10-06 · 오현명

---

## 1. 요약

- Command Injection · File Upload 실습의 셸 명령과 SQL Injection 실습의 쿼리는 **별도 sandbox 컨테이너**에서만 실행된다.
- 설정 파일 점검(8개 항목)과 실제 동작 점검(7개 항목)을 했고 **모두 통과**했다. 보완할 설정은 없다.
- 핵심: 네트워크 없음 · 읽기 전용 파일 시스템 · 일반 사용자 실행 · 관리자 권한 제거 · 자원/시간 제한.
- 그래서 학생이 공격에 성공해도 피해는 **버려지는 컨테이너 안**에 머문다.

---

## 2. 개념 설명 (비유)

**방폭 실험실**과 같다.

- 위험한 실험(공격 실습)은 본관(서비스 서버)이 아니라 별도 실험실(sandbox)에서만 한다.
- 실험실은 창문이 없고(네트워크 차단), 벽에 낙서할 수 없고(읽기 전용), 열쇠가 없는 일반 출입증만 있으며(일반 사용자·권한 제거), 재료도 정해진 양만 들어간다(자원 제한).
- 본관과는 작은 우편함(공유 소켓 파일) 하나로만 쪽지를 주고받는다.

---

## 3. 용어 설명

| 용어 | 뜻 |
|---|---|
| sandbox | 위험한 코드를 격리해 실행하는 환경 |
| `network_mode: none` | 컨테이너에 네트워크 장치를 주지 않음 (인터넷·다른 컨테이너 접근 불가) |
| `read_only` | 컨테이너 파일 시스템을 읽기 전용으로 만듦 |
| capability | 리눅스 관리자 권한을 잘게 나눈 것. `cap_drop: ALL` 은 전부 제거 |
| `no-new-privileges` | 실행 중 권한 상승(setuid 등)을 막는 옵션 |
| Unix 소켓 | 같은 컴퓨터 안에서 파일 경로로 통신하는 방식 (네트워크 불필요) |

---

## 4. 화면 & 동작

### 4-1. 구조

```
[브라우저] → [Nginx] → [Flask backend] ──(ipc 볼륨의 sandbox.sock)──> [sandbox 컨테이너]
                              │                                         · network none
                              └── [MariaDB] (회원·진도·보상)             · read-only, /tmp 16MB
                                    ↑ sandbox 에서는 접근 경로 없음       · runner(uid 1000)
                                                                         · cap_drop ALL
```

### 4-2. 설정 점검 (파일 기준)

| 항목 | 설정 | 위치 | 결과 |
|---|---|---|---|
| 네트워크 차단 | `network_mode: "none"` | docker-compose.yml | ✅ |
| 읽기 전용 FS | `read_only: true`, 쓰기는 `/tmp` 16MB 만 | docker-compose.yml | ✅ |
| 권한 제거 | `cap_drop: [ALL]`, `no-new-privileges:true` | docker-compose.yml | ✅ |
| 일반 사용자 | `USER runner` | sandbox/Dockerfile | ✅ |
| 자원 제한 | 메모리 128MB, 프로세스 64, CPU 0.5 | docker-compose.yml | ✅ |
| 시간·크기 제한 | 요청 최대 시간, 자식 CPU 2초, 파일 1MB | sandbox/runner.py | ✅ |
| 통신 경로 | Unix 소켓(`/ipc/sandbox.sock`) 만 | sandbox_client.py | ✅ |
| SQL 실습 DB | 매 요청 메모리 SQLite, 단일 쿼리만 | sandbox/runner.py | ✅ |

### 4-3. 동작 점검 (실제 컨테이너, 2026-10-06)

| # | 점검 | 기대 | 실제 결과 | 판정 |
|---|---|---|---|---|
| 1 | 실행 계정 | root 아님 | `uid=1000(runner)` | ✅ |
| 2 | 루트 FS 쓰기 | 실패 | `Read-only file system` | ✅ |
| 3 | `/tmp` 쓰기 | 성공 | `tmp-ok` | ✅ |
| 4 | 외부 인터넷 | 실패 | `Network is unreachable` | ✅ |
| 5 | 서비스 DB(`db`) 접근 | 실패 | `Temporary failure in name resolution` | ✅ |
| 6 | 비밀값 환경변수 | 없음 | `GPG_KEY` 1건 → Python 공식 이미지의 **공개 서명키 지문**(비밀 아님) | ✅ |
| 7 | 실제 적용 설정 | 설정과 일치 | `net=none readonly=true capdrop=[ALL] mem=128MB pids=64 cpu=0.5 sec=[no-new-privileges]` | ✅ |

### 점검 명령 (재현용)

```
docker compose exec sandbox id
docker compose exec sandbox sh -c "touch /sandbox/test 2>&1 || true"
docker compose exec sandbox sh -c "touch /tmp/test && echo tmp-ok"
docker compose exec sandbox python3 -c "import socket; socket.create_connection(('8.8.8.8',53),2)"
docker compose exec sandbox python3 -c "import socket; print(socket.gethostbyname('db'))"
docker compose exec sandbox sh -c "env | grep -i -E 'pass|secret|key|database' || echo no-secrets"
docker inspect $(docker compose ps -q sandbox) --format 'net={{.HostConfig.NetworkMode}} readonly={{.HostConfig.ReadonlyRootfs}} capdrop={{.HostConfig.CapDrop}}'
```

### 관련 파일

| 파일 | 역할 |
|---|---|
| `docker-compose.yml` (sandbox 서비스) | 네트워크·읽기 전용·권한·자원 제한 |
| `sandbox/Dockerfile` | 일반 사용자(runner)로 실행 |
| `sandbox/runner.py` | 요청 실행, 시간·CPU·파일 크기 제한, 메모리 SQLite |
| `backend/app/sandbox_client.py` | Unix 소켓으로 실행 요청, 응답 크기·시간 제한 |

---

## 5. 동작 원리

```
[학생이 실습 실행]
      ▼
Flask: 레벨 필터 적용 → sandbox_client.execute(요청)
      ▼  (ipc 볼륨의 Unix 소켓, 네트워크 아님)
sandbox runner: 시간·자원 제한을 걸고 셸 명령 / 메모리 SQLite 실행
      ▼
결과(stdout)만 Flask 로 반환 → 화면 표시
```

### 왜 이렇게 했나

- **피해 범위 제한**: 실습은 "진짜로 공격이 성공"해야 학습 효과가 있다. 성공해도 안전하도록 실행 장소 자체를 격리했다.
- **여러 겹 방어**: 네트워크, 파일 시스템, 권한, 자원 중 하나가 뚫려도 나머지가 막는다.
- **서비스 DB 분리**: SQL 실습은 MariaDB가 아니라 매번 새로 만드는 메모리 SQLite에서 실행해 회원 정보가 노출될 경로가 없다.
- **비밀값 미전달**: sandbox 서비스에는 `.env`(DB 비밀번호 등)를 전달하지 않는다.

---

## 6. 난이도(단계) 대신 — 격리 계층별 역할

| 계층 | 막는 것 |
|---|---|
| 네트워크 차단 | 외부로 데이터 유출, 다른 컨테이너(DB·backend) 공격 |
| 읽기 전용 FS | 악성 파일 설치·변조 (재시작 시 `/tmp` 도 초기화) |
| 일반 사용자 + 권한 제거 | 시스템 설정 변경, 권한 상승 |
| 자원·시간 제한 | 무한 루프·포크 폭탄 등으로 서버 마비 |
| 메모리 SQLite | 서비스 DB 노출 |

---

## 7. 핵심 정리

- 공격 실습은 네트워크가 없고, 쓰기·권한·자원이 제한된 sandbox 컨테이너에서만 실행된다.
- 설정 8개, 실제 동작 7개 점검 모두 통과했고 보완할 설정은 없다.
- 발표 설명: "공격이 성공해도 피해는 버려지는 격리 컨테이너 안에 머물고, 서비스 서버와 회원 DB에는 닿을 경로가 없다."

---

## 8. 검증

- 설정 파일 점검: docker-compose.yml · sandbox/Dockerfile · runner.py · sandbox_client.py
- 실제 컨테이너 동작 점검 7개 항목 전부 기대 결과와 일치 (2026-10-06)
- 코드 변경 없음 (점검·문서화만 수행)

---

*© 2026 5팀_Security Learning Platform (부트캠프 캡스톤 학습용)*
