# 05. 마이그레이션 정리 · Command Injection 실습 모듈

이 챕터는 이 대화 세션 안에서 실제로 있었던 작업을 다룬다. 최종 커밋: `63df235`
`feat: command-injection practice (4 tiers, sandbox exec, reward)`.

## 5-1. Alembic 고아 리비전 정리

### 무엇을 발견했나

`flask db heads`를 실행하자 두 개의 head가 나왔다 — 정상적으로 이어진 체인이라면 head는 하나여야 한다.

- `cf3d75db6757`(`init users table`) — `down_revision = None`
- `f07d2a4eadc5`(`add xp and point ledger, user nickname`) — 정상 체인의 끝

또한 `backend/migrations/versions/`에는 `git status`에 잡히지 않는(`untracked`) 파일이 이미 두 개 있었다:
`cf3d75db6757_init_users_table.py`와, 그 파일과 `f07d2a4eadc5`를 하나의 head로 합치는
`9b4a31d6c0e0_merge_heads.py`(`upgrade()`/`downgrade()`가 모두 `pass`인 빈 병합 리비전).

### 왜 문제였나

`cf3d75db6757`도 `down_revision = None`이었다. 즉 정상 체인의 시작점인 `b1a9b6c8c456`(`add auth, roles, courses`,
[01장](./01-phase1.md) 이전에 이미 존재하던 커밋, `down_revision = None`)와 서로 무관한 **별도의 root**였다.

| 리비전 | down_revision | create_table 대상 |
|---|---|---|
| `cf3d75db6757` | `None` | `users` (id, username, email, created_at — 4컬럼) |
| `b1a9b6c8c456` | `None` | `courses`, `users`(id, username, **password_hash, role, name**, email, **phone**, created_at — 8컬럼), `enrollments`, `verification_codes`, `attendance_sessions` |

두 리비전이 각각 `users` 테이블을 만든다. `cf3d75db6757`의 `users`는 인증에 필요한 `password_hash`/`role` 컬럼조차
없는 초기 버전으로, `b1a9b6c8c456`의 `users`로 완전히 대체된 구식 스키마였다.

`9b4a31d6c0e0` 병합 리비전은 `upgrade()`가 `pass`라 겉보기엔 문제를 해결한 것처럼 보이지만, `flask db upgrade head`를
실행하면 Alembic은 두 root의 `upgrade()`를 **각각 먼저 실행한 뒤** 병합점에서 합류한다 — 즉 `users` 테이블을
두 번 만들려다 `table already exists` 오류로 실패하는 구조였다.

### 어떻게 정리했나

먼저 DB 상태를 확인했다(`docker compose exec db sh -c 'MYSQL_PWD="$MARIADB_PASSWORD" mariadb ...'`):
`alembic_version` 테이블만 존재하고 앱 테이블은 하나도 없었으며, `alembic_version`에 저장된 행도 0건이었다.
즉 스탬프조차 안 된 완전히 빈 DB — 데이터 손실 위험 없이 정리할 수 있는 상태임을 먼저 확인한 뒤 진행했다.

1. `cf3d75db6757_init_users_table.py`, `9b4a31d6c0e0_merge_heads.py` 두 파일을 백업 후 `versions/`에서 삭제
   (둘 다 `git status`에 잡히지 않던 untracked 파일이라 git 이력에는 흔적이 남지 않는다)
2. `flask db heads` → 단일 head(`f07d2a4eadc5`) 확인
3. `flask db upgrade head` 실행 → 정상 체인(`b1a9b6c8c456 → 338ece05201e → b5d9598a80e9 → f07d2a4eadc5`)만 적용
4. `SHOW TABLES`로 8개 테이블(`users`, `courses`, `enrollments`, `verification_codes`, `attendance_sessions`,
   `task_progress`, `point_ledger`, `xp_ledger`)이 모두 생성됐는지, `flask db current`가 `f07d2a4eadc5` 단일
   head를 가리키는지 확인

## 5-2. Command Injection 실습 설계

### 확인 질문과 답

구현 전에 세 가지를 먼저 검증했다.

**(1) `cap_drop ALL`·비특권·`read_only` 환경에서 Low 티어(필터 없음)가 실제로 실행 가능한가?**
가능하다. `cap_drop ALL`은 `CAP_NET_RAW` 같은 리눅스 특권 capability만 제거할 뿐, `echo`/`cat`/`grep` 같은
일반 명령 실행 자체를 막지 않는다. `/tmp`는 `tmpfs`로 쓰기가 허용되어 있어, flag 파일을 그 안에 심고 읽는
방식이 그대로 동작한다. 다만 `network_mode: none`이라 네트워크 의존 명령(예: `ping`)은 항상 실패하므로,
실습 테마를 네트워크에 의존하지 않는 **로그 검색(`grep`)** 방식으로 설계했다.

**(2) flag를 심는 방법과 `reset_state()` 초기화의 상호작용은?**
`sandbox/runner.py`의 `reset_state()`는 매 요청 **전과 후** 모두 `/tmp`를 비운다([04장](./04-phase3-5.md) 참고).
즉 두 번의 `sandbox_client.execute()` 호출 사이에는 어떤 상태도 남지 않는다. 그래서 **flag 심기 + 취약한 검색
명령 실행을 하나의 셸 문자열로 묶어 단일 요청**으로 보내도록 설계했다:

```
echo {flag_token} > /tmp/flag.txt && echo 'search log ready' > /tmp/app.log && grep {filtered_input} /tmp/app.log
```

`flag_token`은 매 요청마다 서버에서 새로 생성(`secrets.token_hex(16)`)하고, DB나 Redis에 저장하지 않은 채
같은 요청-응답 사이클 안에서 sandbox의 stdout과 즉시 비교한 뒤 버린다 — "고정 문자열 금지, 매 실행 시 심고
그 토큰으로만 판정"이라는 요구사항을 별도 저장 없이 충족한다.

Impossible 티어는 `argv` 모드(셸을 거치지 않음)를 쓰는데, `argv` 모드는 명령을 하나만 실행할 수 있어
"flag 심기 + 실행"을 한 요청으로 묶을 방법이 없다. 이를 해결하려고 `runner.py` 프로토콜을 확장하는 대신,
Impossible 티어는 애초에 **flag/보상 개념을 쓰지 않는 순수 데모**로 설계했다(아래 5-3 참고) — sandbox
서버 코드는 건드리지 않았다.

**(3) `PRACTICE_BUILDERS` 등록 구조가 나머지 5개 모듈에도 재사용되는가?**
공통 인터페이스(`validate_input`, `run`, `hints`)만 정의하고 `run()`의 내부 구현(sandbox 실행이든, DB 쿼리든)은
모듈이 자유롭게 정하도록 열어뒀다 — Command Injection 외 다른 취약점(SQL Injection처럼 DB를 직접 쓰는 경우 등)도
같은 인터페이스로 등록할 수 있다.

### 승인받은 세 가지 결정

1. **테마**: `ping` 대신 로그 검색(`grep`) 테마 — network=none 환경에서 `ping`이 항상 실패해 학습에 방해가 되므로
2. **Impossible 무보상 데모**: 화이트리스트를 통과하면 애초에 셸 인젝션 경로가 없으므로, flag·보상 없이
   "안전하게 처리된다"는 것만 보여주는 데모로 처리
3. **`practice_builders/` 패키지 구조**로 진행

## 5-3. `roll_and_grant` 멱등성 검증

구현 전, 이미 [04장](./04-phase3-5.md)에서 만든 `roll_and_grant`(`backend/app/rewards.py:43-64`)가 실전에서도
멱등한지 두 가지 시나리오로 직접 검증했다(Flask `test_client` + `session_transaction()`으로 로그인 세션을
직접 주입해, 비밀번호 없이 student1 계정으로 테스트). 검증 스크립트는 1회성으로 작성해 실행 후 삭제했다.

| 시나리오 | 방법 | 결과 |
|---|---|---|
| 순차 이중 호출 | 같은 `(user_id, source, ref)`로 `roll_and_grant`를 두 번 연속 호출 | 1번째: XP 65·포인트 25 지급. 2번째: `(None, None)`. `xp_ledger` 행 1개만 존재 |
| 동시(경쟁 조건) 호출 | `threading.Barrier(10)`으로 스레드 10개를 같은 순간에 출발시켜 동시에 호출 | 10개 중 1개만 성공(XP 52·포인트 31), 나머지 9개는 `(None, None)`. `xp_ledger`/`point_ledger` 각각 1행만 존재 |

동시 테스트에서 10개 스레드가 모두 "사전 조회(SELECT)"를 통과한 뒤 거의 동시에 INSERT를 시도했지만,
`UNIQUE(user_id, source, ref)` 제약이 최종 방어선 역할을 해 1건만 커밋되고 나머지는 `IntegrityError` →
`(None, None)`으로 정상 처리됐다. 즉 앱 레벨의 사전 조회만으로는 막지 못하는 진짜 경쟁 조건도 DB 제약이
막아준다는 것을 실제로 확인했다.

## 5-4. 힌트 설계

"정답 노출이 아니라 구분자를 시도해보라는 수준"으로, 티어마다 3단계(개념 → 구체적 힌트 → 예시 페이로드) 힌트를
`backend/app/practice_builders/command_injection.py`의 `_HINTS` 딕셔너리에 정의했다.

Medium과 High의 블랙리스트를 의도적으로 **둘 다 파이프(`|`)는 막지 않도록** 구성해서, "필터를 더 강화해도
결국 빠지는 지점이 생긴다"는 교훈이 자연스럽게 드러나게 했다(`docs/notes/vuln-difficulty-summary.md`의
"DVWA High = 파이프 등 우회 필요"라는 설명과 일치).

| 티어 | 힌트 1 | 힌트 2 | 힌트 3(예시) |
|---|---|---|---|
| Low | 입력값이 필터링 없이 명령어 뒤에 그대로 이어붙는다 | 셸 구분자(`;`, `&&`, `\|` 등)로 새 명령을 실행할 수 있다 | `아무값 ; cat /tmp/flag.txt` |
| Medium | `;`와 `&&`는 서버가 제거한다 | 구분자가 그 둘뿐일까? 파이프(`\|`)를 떠올려보라 | `아무값 \| cat /tmp/flag.txt` |
| High | `;`, `&&`, 백틱, `$()`, 개행까지 막혔다 | 필터 목록에 파이프(`\|`)는 있었나? | `아무값 \| cat /tmp/flag.txt` |
| Impossible | 화이트리스트 검증 후 셸 없이 인자 배열로 바로 실행한다 | 특수문자가 입력 단계에서 거부돼 셸이 해석할 메타문자 자체가 전달되지 않는다 | (해당 없음) |

## 5-5. 구현 파일

### `backend/app/practice_builders/base.py` — 공통 인터페이스

```python
class PracticeBuilder:
    """실습 모듈 공통 인터페이스. 6개 취약점 모듈이 각자 구현해 PRACTICE_BUILDERS에 등록한다."""
    difficulties = ()
    def validate_input(self, difficulty, user_input): ...   # 에러 메시지 or None
    def run(self, difficulty, user_input): ...               # PracticeResult(output, success)
    def hints(self, difficulty): ...                          # 단계별 힌트 리스트
```

### `backend/app/practice_builders/command_injection.py` — 핵심 로직

```python
_BLACKLISTS = {
    "medium": [";", "&&"],
    "high": [";", "&&", "`", "$(", "\n", "\r"],
}

def run(self, difficulty, user_input):
    if difficulty == "impossible":
        result = sandbox_client.execute(
            {"mode": "argv", "argv": ["grep", user_input, "/etc/hostname"], "timeout": 3}
        )
        return PracticeResult(output=self._format_output(result), success=False)

    flag_token = secrets.token_hex(16)
    filtered_input = self._apply_filter(difficulty, user_input)
    command = (
        f"echo {flag_token} > /tmp/flag.txt && "
        f"echo 'search log ready' > /tmp/app.log && "
        f"grep {filtered_input} /tmp/app.log"
    )
    result = sandbox_client.execute({"mode": "shell", "command": command, "timeout": 3})
    success = flag_token in (result.get("stdout") or "")
    return PracticeResult(output=self._format_output(result), success=success)
```

`validate_input()`은 빈 입력·200자 초과·Impossible 티어의 화이트리스트(`^[A-Za-z0-9._-]{1,64}$`) 위반을 걸러낸다.

### `backend/app/practice_builders/__init__.py` — 레지스트리

```python
PRACTICE_BUILDERS = {"command-injection": CommandInjectionBuilder()}
```

### `backend/app/courses.py` — 라우트 2개 추가

```python
@bp.get("/<slug>/practice/hints")
def practice_hints(slug): ...   # 난이도별 힌트 조회

@bp.post("/<slug>/practice/run")
@limiter.limit("10 per minute")
def run_practice(slug):
    user, course, error = _load_enrolled_course(slug)   # 로그인 + 수강 가드 재사용 (03장)
    if error:
        return error
    builder = PRACTICE_BUILDERS.get(course.slug)
    ...
    result = builder.run(difficulty, user_input)
    if result.success:
        mark_task_complete(user.id, course.id, "practice")          # 03장의 멱등 함수
        xp_row, point_row = roll_and_grant(
            user.id, "practice", f"{course.title} 실습 성공", ref=f"practice:{course.slug}"
        )                                                            # 04장의 멱등 함수
    ...
```

`_load_enrolled_course`(로그인+수강 확인), `mark_task_complete`(과제 완료, [03장](./03-phase3.md)),
`roll_and_grant`(보상 지급, [04장](./04-phase3-5.md)) 모두 기존에 이미 있던 함수를 그대로 재사용했다 —
Command Injection 모듈에서 새로 만든 건 판정 로직(`practice_builders`)과 라우트 2개뿐이다.
CSRF는 전역 `CSRFProtect()`가 모든 POST에 자동 적용되므로 별도 처리가 필요 없었고, 실습 엔드포인트에는
예외를 두지 않았다(`CLAUDE.md` 7절 — 관리자·인증·보상 관련 페이지는 표준 보안 규칙 엄수).

### `frontend/src/components/common/VulnerabilityPage.vue` — 공통 뼈대 (신규)

`#practice`/`#result`/`#explanation` 세 개의 named slot을 제공하는 공통 레이아웃. `CLAUDE.md` 6절의
"6개 취약점 실습 페이지는 공통 뼈대를 감싸고 슬롯만 채운다"는 규칙을 따라, 이후 5개 취약점도 별도 페이지
컴포넌트 없이 이 컴포넌트를 재사용하도록 만들었다.

### `frontend/src/views/ChapterDetailView.vue` — 슬롯 채우기 (스텁 → 전면 구현)

`/chapters/:id` 라우트에 대응하며, `VulnerabilityPage`를 감싸고 난이도 선택 폼·실행 버튼·힌트 아코디언·결과
표시를 `#practice`/`#result` 슬롯에, `enrollStore`의 기존 `detail.exploit`/`detail.defense`([01장](./01-phase1.md)에서
이미 만들어진 텍스트)를 `#explanation` 슬롯에 채운다. 현재는 `PRACTICE_SUPPORTED_SLUGS = ["command-injection"]`으로
지원 과목을 제한해두어, 아직 구현되지 않은 나머지 5개 과목은 "이 과목의 실습은 준비 중입니다" 메시지만 보여준다.
실습 성공 시 `profileStore.fetchProfile()`을 호출해 헤더의 레벨/XP/포인트 패널이 즉시 갱신되도록 연결했다.

## 5-6. 4티어 검증 결과

Flask `test_client` + 세션 주입 방식으로 4개 티어 전체를 검증했다(비밀번호 불필요, 검증 스크립트는 실행 후 삭제).

| 티어 | 입력 | 기대 동작 | 실제 결과 |
|---|---|---|---|
| Low | `aaa ; cat /tmp/flag.txt` | 필터 없음 → 즉시 성공 | `success=True`, `rewarded=True` (XP·포인트 지급) |
| Low(재실행) | 동일 | 이미 완료 → 성공이지만 무보상 | `success=True`, `rewarded=False` |
| Medium | `aaa ; cat /tmp/flag.txt` | `;` 제거됨 → 실패 | `success=False` (`grep: cat: No such file or directory`) |
| Medium | `aaa \| cat /tmp/flag.txt` | `\|` 미필터 → 우회 성공 | `success=True` |
| High | `aaa ; cat /tmp/flag.txt` | `;`/백틱/`$()`/개행 제거됨 → 실패 | `success=False` |
| High | `aaa \| cat /tmp/flag.txt` | `\|` 여전히 미필터 → 우회 성공 | `success=True` |
| Impossible | `aaa \| cat /tmp/flag.txt` | 화이트리스트 위반 → 400 거부 | `status=400`, `"영문·숫자·.·_·-만 허용됩니다."` |
| Impossible | `hostname` | 통과하지만 셸 미개입 → 항상 실패, 무보상 | `success=False`, `rewarded=False` |
| 힌트 조회(4개 티어) | `GET /practice/hints?difficulty=...` | 단계별 힌트 반환 | 4개 티어 모두 정상 반환 |
| 멱등성 최종 확인 | Low 2회 성공 시도 후 | ledger·과제 진도 각 1건만 존재 | `xp_ledger=1`, `point_ledger=1`, `task_progress=1` |

검증 후 테스트로 생성된 `task_progress`/`xp_ledger`/`point_ledger` 행은 모두 삭제해 student1 계정을 실습 전
상태로 원복했다.
