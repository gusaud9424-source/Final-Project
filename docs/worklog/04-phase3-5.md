# 04. Phase 3.5 — 레벨/XP/포인트 시스템, 격리 Sandbox 실행 채널

> 이 단계는 다른 워크스테이션에서 개발 환경(WSL2·Docker·Claude Code 등)을 새로 세팅한 뒤 이어서 진행했다.
> ([00장](./00-개요.md) "개발 환경과 협업 방식" 참고 — 여러 대의 PC를 오가며 git으로 코드를 주고받는 방식.)
> 정확히 어느 시점에 워크스테이션을 옮겼는지는 git 커밋 메타데이터만으로는 특정할 수 없어, 이 사실은 사용자 설명에
> 근거해 기록한다.

커밋: `ab7d113` `feat: level/xp/point system with profile panel` (2026-09-27 20:16, 9개 파일, +451/-14줄),
`dcca74b` `feat: isolated sandbox execution channel (unix socket, resource limits)` (2026-09-28 00:05, 4개 파일, +171/-2줄)

## 4-1. 레벨/XP/포인트 시스템

### 무엇을

사용자가 얼마나 성장했는지 보여주는 레벨·경험치(XP)·포인트 시스템의 데이터 모델과 API, 헤더의 프로필 드롭다운을
만들었다. 이때는 아직 XP·포인트를 실제로 지급하는 실습/미션 기능 자체는 없었고, "지급하면 기록하고 계산할 수 있는
인프라"만 먼저 구축된 상태였다.

### 왜

이후 만들 실습·미션 기능이 "성공하면 보상을 준다"는 동기부여 요소를 가지려면, 그 보상을 누적·조회하는 기반이
먼저 있어야 한다. 특히 같은 보상을 실수로 여러 번 주지 않는 멱등성 장치가 처음부터 설계에 들어가야 나중에
실습 모듈을 추가할 때마다 안전하게 재사용할 수 있다.

### 어떻게

#### 원장(ledger) 테이블 — `f07d2a4eadc5_add_xp_and_point_ledger_user_nickname.py`

```python
# revision = 'f07d2a4eadc5', down_revision = 'b5d9598a80e9'
op.create_table('point_ledger', ...,
    sa.UniqueConstraint('user_id', 'source', 'ref', name='uq_point_ledger_user_source_ref'))
op.create_table('xp_ledger', ...,
    sa.UniqueConstraint('user_id', 'source', 'ref', name='uq_xp_ledger_user_source_ref'))
with op.batch_alter_table('users', schema=None) as batch_op:
    batch_op.add_column(sa.Column('nickname', sa.String(length=30), nullable=True))
```

XP와 포인트를 "누적 합계 컬럼"이 아니라 지급 내역을 한 줄씩 쌓는 **원장(ledger)** 방식으로 설계했다.
`(user_id, source, ref)`에 유니크 제약을 걸어, 같은 사용자가 같은 출처(`source`)·같은 참조 키(`ref`)로
두 번 지급받을 수 없게 DB가 막아준다. `ref`가 `NULL`인 행은 MariaDB의 유니크 제약 특성상 서로 충돌하지 않으므로
"반복 지급이 의도적으로 허용된 이벤트"를 표현하는 데 쓴다(`backend/app/models.py:114-115` 주석).

`users` 테이블에는 표시용 `nickname` 컬럼이 이때 함께 추가됐다.

#### 보상 로직 — `backend/app/rewards.py` (신규)

```python
# 퀴즈는 순수 학습용이라 보상 대상에서 제외한다. 여기 등록된 source만 roll_and_grant로 지급 가능.
XP_RANGES = {"practice": (50, 100), "mission": (30, 80)}
POINT_RANGES = {"practice": (20, 40), "mission": (10, 30)}

def roll_and_grant(user_id, source, reason, ref=None):
    """ref가 있으면 1회성 이벤트로 취급해 중복 지급을 막는다(이미 지급된 경우 (None, None) 반환)."""
    if ref is not None and XpLedger.query.filter_by(user_id=user_id, source=source, ref=ref).first():
        return None, None
    ...
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, None
    return xp_row, point_row
```

`compute_level(total_xp)`은 레벨업에 필요한 XP를 `레벨 × 100`으로 계산하며 50레벨을 상한으로 둔다.

이 시점에는 `"practice"`, `"mission"` 두 개의 보상 출처(source)가 **값만 등록**되어 있었고,
`roll_and_grant()`를 실제로 호출하는 라우트는 아직 없었다 — 즉 "배선만 된" 상태의 인프라였다.
`"practice"` 출처를 실제로 처음 사용하는 지점은 [05장](./05-command-injection.md)의 Command Injection 모듈이다.
`"mission"` 출처는 이 기록 시점 기준으로도 호출하는 코드가 없다 — **확인 필요**(향후 미션 기능에서 쓰일 것으로 보이나
설계 문서는 별도로 없다).

#### 프로필 API — `backend/app/profile.py` (신규)

`GET /api/v1/profile`이 레벨·현재 XP·다음 레벨까지 필요한 XP·누적 XP·포인트를 계산해 반환하고,
`PATCH /api/v1/profile`이 닉네임을 변경한다(2~20자, 한글·영문·숫자·밑줄만 허용, 중복 검사).

#### 화면 — `frontend/src/components/layout/AppHeader.vue`, `frontend/src/stores/profile.js`

헤더 우측 아바타를 클릭하면 레벨·XP 진행바·보유 포인트·닉네임 변경 폼이 담긴 드롭다운이 열린다.
XP와 포인트는 한 패널 안에 각각 별도 줄로 표시되지만, 포인트를 개별적으로 "수령"하는 버튼은 없다 —
`roll_and_grant`가 성공 조건 충족 시 서버에서 즉시 함께 지급하는 방식이라 별도 수령 절차 자체가 없다.
이 UI를 어떻게 다듬을지는 [06장](./06-todo.md)의 할 일 목록에 있다.

## 4-2. 격리 Sandbox 실행 채널

### 무엇을

실습 페이지에서 사용자가 입력한 값으로 실제 명령을 실행해볼 수 있게, backend가 별도의 `sandbox` 컨테이너와
유닉스 도메인 소켓으로 통신하는 채널을 만들었다. `sandbox/Dockerfile`, `sandbox/runner.py`(신규 117줄),
`backend/app/sandbox_client.py`(신규 42줄), 그리고 `docker-compose.yml`의 `sandbox` 서비스 정의가 이 커밋에 포함됐다.

### 왜

실습 코드(특히 Command Injection처럼 셸 명령을 그대로 실행하는 유형)를 backend 프로세스 안에서 직접 실행하면
서버 자체가 뚫릴 수 있다. 네트워크·파일시스템·권한을 극단적으로 제한한 별도 컨테이너에서만 실행하고,
그 컨테이너와는 최소한의 통신 채널(소켓 하나)로만 연결해야 안전하다.

### 어떻게

#### 프로토콜

줄바꿈으로 구분된 JSON 한 덩어리를 요청/응답으로 주고받는 단순한 프로토콜이다.

```python
# sandbox/runner.py
SOCK_PATH = "/ipc/sandbox.sock"
MAX_TIMEOUT_SEC = 5
MAX_STDOUT = 4000
```

요청은 `{"mode": "shell", "command": "..."}`(셸을 거쳐 문자열 그대로 실행) 또는
`{"mode": "argv", "argv": [...]}`(셸을 거치지 않고 인자 배열을 바로 `execve`, 메타문자 해석 자체가 불가능) 두 가지
모드를 지원한다. 이 두 모드의 차이는 [05장](./05-command-injection.md)의 난이도 티어 설계에서 핵심 역할을 한다.

```python
def reset_state():
    """/tmp(tmpfs)를 요청 전/후로 초기화"""
```

매 요청 **전과 후** 모두 `/tmp`를 깨끗이 비운다. 이 동작이 이후 Command Injection 모듈에서 "flag를 심고 읽는 걸
반드시 한 번의 요청 안에서 끝내야 하는" 제약으로 이어진다([05장](./05-command-injection.md) "Sandbox reset_state와의
상호작용" 절 참고).

`serve()`는 `listen(1)`로 한 번에 하나의 연결만 처리하는 단일 스레드 서버다 — 동시에 여러 요청이 오면 순서대로
직렬 처리된다.

#### 클라이언트 — `backend/app/sandbox_client.py`

```python
def execute(payload):
    """연결 실패·타임아웃·응답 파싱 실패는 모두 timed_out=True의 graceful 결과로 수렴한다."""
```

backend가 sandbox와 통신하는 유일한 창구. 연결에 실패해도 예외를 던지지 않고 `timed_out: True`를 담은 딕셔너리로
반환해, 호출하는 쪽이 항상 같은 모양의 응답을 받도록 한다.

#### 격리 옵션 — `docker-compose.yml`

| 옵션 | 값 | 의미 |
|---|---|---|
| `network_mode` | `none` | 네트워크 인터페이스 없음(loopback 제외 통신 불가) |
| `read_only` | `true` | 루트 파일시스템 쓰기 금지 |
| `tmpfs` | `/tmp` | `/tmp`만 메모리 기반으로 쓰기 허용 |
| `cap_drop` | `[ALL]` | 리눅스 capability 전부 제거 |
| `security_opt` | `no-new-privileges:true` | setuid 등으로 권한 상승 금지 |
| `mem_limit` / `pids_limit` / `cpus` | `128m` / `64` / `0.5` | 자원 남용 방지 |

`sandbox/Dockerfile`은 `python:3.12-slim` 기반이며 non-root 사용자(`runner`)로 실행된다.

이 시점에도 `sandbox_client.execute()`를 실제로 호출하는 라우트는 없었다 — 소켓 배선과 격리 설정만 갖춘 인프라
상태였다. 이 채널을 실제로 처음 사용하는 지점 역시 [05장](./05-command-injection.md)이다.

## 4-3. 난이도 4티어 방향 결정

`docs/notes/vuln-difficulty-summary.md`에 DVWA·bWAPP·WebGoat 세 플랫폼의 난이도 체계를 비교 정리한 문서가
이 무렵 작성돼 있다. Command Injection 항목 기준으로 DVWA의 **Low(필터 없음) → Medium(일부 블랙리스트, 우회 가능)
→ High(더 강한 블랙리스트, 파이프 등으로 우회 필요) → Impossible(화이트리스트 검증)** 4단계 체계가 정리되어 있고,
이 체계를 6개 취약점 모듈 전체에 적용하는 방향으로 설계 방향이 잡혔다. 이 문서가 실제로 [05장](./05-command-injection.md)의
Command Injection 4티어 설계의 근거가 됐다.

## 4-4. 코드에서 확인되지 않은 항목들

아래 항목들은 설계 논의 단계에서 이름이 오갔지만, 이 기록 시점 기준으로 실제 코드베이스에는 반영되어 있지
않았다 — 확인한 그대로 적는다.

- **탭명 "실습"/"미션" 변경**: `CourseDetailView.vue`의 탭은 여전히 `강의`/`과제`/`과목 정보` 3개다
  (`const TABS = [...]`, `frontend/src/views/CourseDetailView.vue`). "실습"/"미션"이라는 별도 탭은 없다.
- **퀴즈 모달**: 현재 방어 퀴즈는 "과제" 탭 안의 인라인 폼(`<form class="sq-quiz__form">`)으로 구현되어 있다.
  모달 형태는 아니다. 다만 `docs/references/05-quiz-modal-progress.png`, `06-quiz-modal-result.png`라는
  참고 캡처 파일명으로 미루어, 모달 형태가 디자인 참고 자료로는 검토됐을 가능성이 있다 — **확인 필요**.
- **미션 보상 UI**: `rewards.py`에 `"mission"` source가 값으로는 등록돼 있지만, 이를 호출하는 라우트나
  미션 목록을 보여주는 화면은 코드에 없다 — **확인 필요**.
- **practice_builders 재사용 구조**: 이 시점까지는 존재하지 않았다. 실습마다 다른 판정 로직이 필요하다는 것,
  그리고 sandbox·보상 인프라가 이미 준비돼 있다는 것이 이 구조를 도입하게 된 배경이며, 실제 설계와 구현은
  [05장](./05-command-injection.md)에서 이 대화 안에서 이뤄졌다.
