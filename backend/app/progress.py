from datetime import datetime

from flask import session
from sqlalchemy.exc import IntegrityError

from . import db
from .models import TASK_KEYS, TaskProgress, User

TASK_TOTAL = len(TASK_KEYS)
TASK_TITLES = {
    "concept": "개념 학습",
    "practice": "실습 성공",
    "defense": "방어 퀴즈",
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
