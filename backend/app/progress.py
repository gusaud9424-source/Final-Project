from datetime import datetime

from flask import session
from sqlalchemy.exc import IntegrityError

from . import db
from .models import TASK_KEYS, TaskProgress, User

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
    """{task_key: completed_at} 형태로 완료된 과제 반환"""
    rows = TaskProgress.query.filter_by(user_id=user_id, course_id=course_id).all()
    return {row.task_key: row.completed_at for row in rows if row.task_key in TASK_KEYS}


def mark_task_complete(user_id, course_id, task_key):
    """과제 완료 처리(멱등). 이미 완료된 경우 기존 기록 유지"""
    if task_key not in TASK_KEYS:
        raise ValueError(f"unknown task_key: {task_key}")
    return _upsert_progress(user_id, course_id, task_key)


# ─── 실습 레벨(하 → 중 → 상 → 안전) 진행 ───
# 피드백 반영: 레벨을 섞지 않고 순서대로 학습하도록, 이전 레벨을 통과해야 다음 레벨이 열린다.
# 별도 테이블 없이 task_progress 에 "tier_<레벨>" 키로 저장한다.
# (진도율·관리자 집계는 TASK_KEYS 로 필터링하므로 이 키는 진도율에 섞이지 않는다)
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


def progress_summary(done):
    completed = sum(1 for key in TASK_KEYS if key in done)
    return {
        "completed": completed,
        "total": TASK_TOTAL,
        "percent": round(completed / TASK_TOTAL * 100),
    }


def serialize_datetime(value):
    # DB·앱 모두 UTC 기준 저장 → ISO 8601 UTC 표기
    return value.isoformat(timespec="seconds") + "Z" if value else None
