# 03. Phase 3 — 과목 상세 · 과제 진도 · 방어 퀴즈

커밋: `ad048c5` `feat(phase3): course detail, task progress, defense quiz` (2026-09-26 02:01, 10개 파일, +946/-50줄)

## 무엇을

과목 하나를 클릭했을 때 보여줄 실제 상세 화면(`CourseDetailView.vue`)을 만들고, "이 과목에서 어떤 과제를 완료했는지"를
DB에 기록하는 `task_progress` 테이블, 그리고 각 과목마다 방어 지식을 확인하는 4지선다 퀴즈를 추가했다.
대시보드의 진도율 계산 방식도 이때 `task_progress` 기준으로 통일됐다.

## 왜

과목마다 "개념 학습 → 실습 → 방어 퀴�즈" 3단계 과제가 있고, 각 단계를 완료했는지 서버가 기억하고 있어야
진도율을 보여줄 수 있다. 기존 `enrollments.percent`/`attendance_sessions` 컬럼은 출석 체크용으로 설계돼 있어
이 목적에 맞지 않았다 — 그래서 과제 전용 테이블을 새로 만들고, 기존 계산 방식은 폐기했다.

## 어떻게

### 과제 진도 테이블 — `b5d9598a80e9_add_task_progress.py`

```python
# revision = 'b5d9598a80e9', down_revision = '338ece05201e'
op.create_table('task_progress',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('task_key', sa.String(length=20), nullable=False),
    sa.Column('completed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'course_id', 'task_key', name='uq_task_progress_user_course_task')
)
```

`(user_id, course_id, task_key)` 조합에 유니크 제약을 걸어, "같은 사용자가 같은 과목의 같은 과제를 두 번
완료 기록할 수 없게" DB 레벨에서 보장한다.

### 진도 도우미 — `backend/app/progress.py` (신규)

```python
TASK_KEYS = ("concept", "practice", "defense")

def mark_task_complete(user_id, course_id, task_key):
    """과제 완료 처리(멱등). 이미 완료된 경우 기존 기록 유지"""
    exists = TaskProgress.query.filter_by(user_id=user_id, course_id=course_id, task_key=task_key).first()
    if exists:
        return exists
    record = TaskProgress(user_id=user_id, course_id=course_id, task_key=task_key, completed_at=datetime.utcnow())
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return TaskProgress.query.filter_by(user_id=user_id, course_id=course_id, task_key=task_key).first()
    return record
```

> **멱등성(idempotency)이란?** 같은 요청을 여러 번 보내도 결과가 한 번 보낸 것과 같아야 한다는 성질이다.
> 여기서는 "완료 처리"를 두 번 호출해도 레코드가 하나만 남는다. 먼저 조회해서 이미 있으면 그대로 반환하고(앱 레벨 방어),
> 그 사이 다른 요청이 끼어들어 동시에 INSERT됐다면 DB의 유니크 제약이 막아주므로 `IntegrityError`를 다시 조회로
> 흡수한다(DB 레벨 방어). 이 이중 방어 패턴은 [05장](./05-command-injection.md)의 `roll_and_grant` 멱등성 검증에서
> 실제로 동시 요청 테스트까지 거친다.

과목마다 3개 과제(`concept`=개념 학습, `practice`=실습 성공, `defense`=방어 퀴즈)가 있고, `TASK_TITLES`에
한국어 라벨이, `progress_summary(done)`에 "완료 개수/전체/퍼센트" 계산 로직이 들어있다.

### 방어 퀴즈 콘텐츠 — `backend/app/course_content.py` (신규, 99줄)

8개 과목 전체의 퀴즈 문항·보기·정답 인덱스·해설을 담은 `DEFENSE_QUIZZES` 딕셔너리. 정답과 해설은
`public_quiz(slug)`가 걸러내고 문항·보기만 클라이언트로 내려간다(클라이언트에 정답을 노출하지 않기 위함).

### 라우트 — `backend/app/courses.py` (신규)

```python
@bp.get("/<slug>")
def course_detail(slug): ...       # 과목 정보 + 과제 진도 + 퀴즈(정답 제외)

@bp.post("/<slug>/tasks/concept")
def complete_concept(slug): ...    # "과목 정보" 탭 열람 시 concept 과제 완료 처리

@bp.post("/<slug>/quiz")
@limiter.limit("10 per minute")
def submit_quiz(slug): ...         # 정답 맞히면 defense 과제 완료 처리
```

세 라우트 모두 `_load_enrolled_course(slug)`라는 공통 가드를 통과해야 한다 — 로그인 → 과목 존재 →
수강 여부 순서로 검사하고, 실패하면 401/404/403을 반환한다. 이 가드는 이후 모든 과목별 라우트(퀴즈, 실습 등)에서
재사용된다.

### 화면 — `frontend/src/views/CourseDetailView.vue` (신규 수준, 589줄)

"강의/과제/과목 정보" 3개 탭으로 구성됐다. "과제" 탭에서 3개 과제의 완료 여부와 퀴즈 폼을 보여주고,
"과목 정보" 탭을 처음 열람하면 `concept` 과제를 자동으로 완료 처리한다(`completeConcept()`).

### 대시보드 진도 계산 통일 — `backend/app/dashboard.py`

```python
def _task_map(user_ids):
    """{(user_id, course_id): {task_key, ...}} — 진도는 task_progress 기준으로만 계산
    (enrollment.percent · attendance_sessions 는 사용 중단)"""
```

주석에 명시된 대로, 이전까지 `Enrollment.percent`나 `AttendanceSession`으로 진도를 추정하던 방식을 버리고
`task_progress` 조회 하나로 통일했다. `Enrollment.percent`, `AttendanceSession` 모델 자체는 아직 코드에
남아 있지만 대시보드 계산에는 더 이상 쓰이지 않는다.

## 검증 방법과 결과

이 시점의 수동 검증 절차나 결과는 커밋 이력만으로는 확인할 수 없다 — **확인 필요**.
