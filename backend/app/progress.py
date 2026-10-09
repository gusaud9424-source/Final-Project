from datetime import datetime

from flask import session
from sqlalchemy.exc import IntegrityError

from . import db
from .models import TASK_KEYS, Course, TaskProgress, User

TASK_TOTAL = len(TASK_KEYS)
TASK_TITLES = {
    "concept": "개념 학습",
    "practice": "실습 성공",
    "defense": "퀴즈 풀기",
}


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def completed_tasks(user_id, course_id):
    """{task_key: completed_at} 형태로 완료된 과제 반환 (실습 미션은 레벨 조건 적용)"""
    rows = TaskProgress.query.filter_by(user_id=user_id, course_id=course_id).all()
    return {row.task_key: row.completed_at for row in effective_task_rows(rows)}


# 2회차 실습 성공 미션 완료 조건: 하·중·상 레벨 통과 기록이 모두 있어야 함
# (레벨 구조 도입 전 "아무 레벨 1회 성공"으로 남은 practice 기록은 완료로 보지 않는다)
PRACTICE_REQUIRED_TIER_KEYS = ("tier_low", "tier_medium", "tier_high")
# 1회차 개념 학습 완료 조건: 확인 문제 통과 기록(concept_check)이 있어야 함
CONCEPT_CHECK_KEY = "concept_check"
PROGRESS_QUERY_KEYS = TASK_KEYS + ("tier_low", "tier_medium", "tier_high", "tier_impossible", CONCEPT_CHECK_KEY)


def mark_check_passed(user_id, course_id):
    """개념 확인 문제 통과 기록(멱등)"""
    return _upsert_progress(user_id, course_id, CONCEPT_CHECK_KEY)


def effective_task_rows(rows):
    """task_progress 행 목록에서 유효한 미션 완료 행만 반환.
    rows 에는 같은 사용자·과목의 tier_* 행도 함께 들어 있어야 실습 미션 조건을 판정할 수 있다."""
    tiers = {}
    for row in rows:
        if row.task_key.startswith("tier_") or row.task_key == CONCEPT_CHECK_KEY:
            tiers.setdefault((row.user_id, row.course_id), set()).add(row.task_key)
    result = []
    for row in rows:
        if row.task_key not in TASK_KEYS:
            continue
        marks = tiers.get((row.user_id, row.course_id), set())
        if row.task_key == "practice" and not set(PRACTICE_REQUIRED_TIER_KEYS) <= marks:
            continue
        if row.task_key == "concept" and CONCEPT_CHECK_KEY not in marks:
            continue
        result.append(row)
    return result


def mark_task_complete(user_id, course_id, task_key):
    """과제 완료 처리(멱등). 이미 완료된 경우 기존 기록 유지"""
    if task_key not in TASK_KEYS:
        raise ValueError(f"unknown task_key: {task_key}")
    return _upsert_progress(user_id, course_id, task_key)


# ─── 실습 레벨(하 → 중 → 상 → 안전) 진행 ───
# 피드백 반영: 레벨을 섞지 않고 순서대로 학습하도록, 이전 레벨을 통과해야 다음 레벨이 열린다.
# 별도 테이블 없이 task_progress 에 "tier_<레벨>" 키로 저장한다.
# 진도율은 이 레벨 통과 키(tier_*)로 계산한다 (아래 PROGRESS_KEYS)
TIER_ORDER = ("low", "medium", "high", "impossible")
TIER_LABELS = {"low": "하", "medium": "중", "high": "상", "impossible": "안전"}


def _tier_key(tier):
    return f"tier_{tier}"


def cleared_tiers(user_id, course_id):
    """통과한 레벨 집합 반환 (예: {"low", "medium"})"""
    keys = {_tier_key(t): t for t in TIER_ORDER}
    rows = TaskProgress.query.filter(
        TaskProgress.user_id == user_id,
        TaskProgress.course_id == course_id,
        TaskProgress.task_key.in_(keys.keys()),
    ).all()
    return {keys[row.task_key] for row in rows}


def is_tier_unlocked(tier, cleared):
    """첫 레벨은 항상 열림, 그 외에는 바로 앞 레벨을 통과해야 열림"""
    index = TIER_ORDER.index(tier)
    return index == 0 or TIER_ORDER[index - 1] in cleared


def tier_states(cleared):
    """화면 표시용 레벨 상태 목록"""
    return [
        {
            "key": tier,
            "label": TIER_LABELS[tier],
            "unlocked": is_tier_unlocked(tier, cleared),
            "cleared": tier in cleared,
        }
        for tier in TIER_ORDER
    ]


def mark_tier_cleared(user_id, course_id, tier):
    """레벨 통과 처리(멱등)"""
    if tier not in TIER_ORDER:
        raise ValueError(f"unknown tier: {tier}")
    return _upsert_progress(user_id, course_id, _tier_key(tier))


def _upsert_progress(user_id, course_id, task_key):
    """task_progress 행을 멱등하게 생성"""
    exists = TaskProgress.query.filter_by(user_id=user_id, course_id=course_id, task_key=task_key).first()
    if exists:
        return exists

    record = TaskProgress(
        user_id=user_id,
        course_id=course_id,
        task_key=task_key,
        completed_at=datetime.utcnow(),
    )
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        # 동시 요청으로 UNIQUE 위반 시 이미 완료된 것으로 간주
        db.session.rollback()
        return TaskProgress.query.filter_by(user_id=user_id, course_id=course_id, task_key=task_key).first()
    return record


# ─── 진도율 ───
# 진도율은 실습 레벨(하 · 중 · 상 · 안전) 통과만으로 계산한다. 과목당 4단계 = 100%.
# 미션(개념 확인 · 실습 미션 · 퀴즈)은 보상용이며 진도율에 포함하지 않는다.
PROGRESS_KEYS = tuple(_tier_key(t) for t in TIER_ORDER)
PROGRESS_TOTAL = len(PROGRESS_KEYS)


def progress_summary(done):
    """done: task_key 집합(또는 dict). tier_* 키만 진도로 센다."""
    completed = sum(1 for key in PROGRESS_KEYS if key in done)
    return {
        "completed": completed,
        "total": PROGRESS_TOTAL,
        "percent": round(completed / PROGRESS_TOTAL * 100),
    }


def overall_progress_total():
    """전체 진도율 분모: 전체 과목(수강신청 화면의 8개 취약점) × 4레벨
    → 8과목을 모두 수강하고 각 과목 4레벨을 전부 통과해야 100%"""
    return Course.query.filter(Course.slug.isnot(None)).count() * PROGRESS_TOTAL


def tier_progress_keys(cleared):
    """cleared_tiers() 결과({"low", ...})를 진도 키 집합으로"""
    return {_tier_key(t) for t in cleared}


def progress_rows(rows):
    """task_progress 행 중 진도율 대상(레벨 통과) 행만"""
    return [row for row in rows if row.task_key in PROGRESS_KEYS]


def serialize_datetime(value):
    # DB·앱 모두 UTC 기준 저장 → ISO 8601 UTC 표기
    return value.isoformat(timespec="seconds") + "Z" if value else None
