from flask import Blueprint, jsonify, request

from . import limiter
from .course_content import DEFENSE_QUIZZES, public_quiz
from .models import TASK_KEYS, Course, Enrollment
from .progress import (
    TASK_TITLES,
    completed_tasks,
    current_user,
    mark_task_complete,
    progress_summary,
    serialize_datetime,
)

bp = Blueprint("courses", __name__, url_prefix="/api/v1/courses")


def _load_enrolled_course(slug):
    """(user, course, error_response) 반환. 로그인·과목 존재·수강 여부 순으로 검사"""
    user = current_user()
    if not user:
        return None, None, (jsonify(message="로그인이 필요합니다."), 401)

    course = Course.query.filter_by(slug=slug).first()
    if not course:
        return None, None, (jsonify(message="존재하지 않는 과목입니다."), 404)

    enrolled = Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first()
    if not enrolled:
        return None, None, (jsonify(message="수강 중인 과목이 아닙니다."), 403)

    return user, course, None


@bp.get("/<slug>")
def course_detail(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    done = completed_tasks(user.id, course.id)
    tasks = [
        {
            "key": key,
            "title": TASK_TITLES[key],
            "completed": key in done,
            "completedAt": serialize_datetime(done.get(key)),
        }
        for key in TASK_KEYS
    ]
    return jsonify(
        course={
            "slug": course.slug,
            "title": course.title,
            "description": course.description,
            "icon": course.icon,
            "difficulty": course.difficulty,
        },
        tasks=tasks,
        progress=progress_summary(done),
        quiz=public_quiz(course.slug),
    )


@bp.post("/<slug>/tasks/concept")
def complete_concept(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    record = mark_task_complete(user.id, course.id, "concept")
    return jsonify(taskKey="concept", completed=True, completedAt=serialize_datetime(record.completed_at))


@bp.post("/<slug>/quiz")
@limiter.limit("10 per minute")
def submit_quiz(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    quiz = DEFENSE_QUIZZES.get(course.slug)
    if not quiz:
        return jsonify(message="이 과목에는 퀴즈가 없습니다."), 404

    payload = request.get_json(silent=True) or {}
    answer = payload.get("answer")
    # bool 은 int 하위 타입이므로 명시적으로 제외
    if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < len(quiz["options"]):
        return jsonify(message="올바른 보기를 선택하세요."), 400

    if answer != quiz["answer"]:
        return jsonify(correct=False, explanation=quiz["explanation"])

    mark_task_complete(user.id, course.id, "defense")
    return jsonify(correct=True)
