from collections import defaultdict

from flask import Blueprint, jsonify
from sqlalchemy.orm import joinedload, selectinload

from .models import TASK_KEYS, Enrollment, TaskProgress, User
from .progress import PROGRESS_KEYS
from .progress import PROGRESS_QUERY_KEYS, current_user, effective_task_rows, progress_rows, progress_summary

bp = Blueprint("dashboard", __name__, url_prefix="/api/v1")


def _task_map(user_ids):
    """{(user_id, course_id): {task_key, ...}} — 진도는 task_progress 기준으로만 계산
    (enrollment.percent · attendance_sessions 는 사용 중단)"""
    done = defaultdict(set)
    if not user_ids:
        return done
    rows = TaskProgress.query.filter(
        TaskProgress.user_id.in_(user_ids), TaskProgress.task_key.in_(PROGRESS_QUERY_KEYS)
    ).all()
    # 미션 완료(표시용) + 레벨 통과(진도율용)
    for row in effective_task_rows(rows) + progress_rows(rows):
        done[(row.user_id, row.course_id)].add(row.task_key)
    return done


def _serialize_course(enrollment, done_keys):
    course = enrollment.course
    return {
        "id": course.id,
        "slug": course.slug,
        "icon": course.icon,
        "title": course.title,
        "description": course.description,
        "instructor": course.instructor,
        "schedule": course.schedule,
        # 학습 진도 화면의 레벨별(하 · 중 · 상 · 안전) 통과 표시 + 미션 완료 키
        "doneKeys": [key for key in PROGRESS_KEYS + TASK_KEYS if key in done_keys],
        **progress_summary(done_keys),
    }


def _student_dashboard(user):
    enrollments = (
        Enrollment.query.filter_by(user_id=user.id).options(joinedload(Enrollment.course)).all()
    )
    done = _task_map([user.id])
    courses = [_serialize_course(e, done[(user.id, e.course_id)]) for e in enrollments]
    total_tasks = sum(c["total"] for c in courses)
    completed_tasks = sum(c["completed"] for c in courses)
    percent = round(completed_tasks / total_tasks * 100) if total_tasks else 0
    return jsonify(
        role="student",
        summary={
            "courseCount": len(courses),
            "completedTasks": completed_tasks,
            "totalTasks": total_tasks,
            "percent": percent,
        },
        courses=courses,
    )


def _students_overview():
    students = (
        User.query.filter_by(role="student")
        .options(selectinload(User.enrollments).joinedload(Enrollment.course))
        .all()
    )
    done = _task_map([s.id for s in students])
    return [
        {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "courses": [
                _serialize_course(e, done[(student.id, e.course_id)]) for e in student.enrollments
            ],
        }
        for student in students
    ]


@bp.get("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401
    if user.role == "admin":
        return jsonify(role="admin", students=_students_overview())
    return _student_dashboard(user)


@bp.get("/admin/students")
def admin_students():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401
    if user.role != "admin":
        return jsonify(message="권한이 없습니다."), 403
    return jsonify(students=_students_overview())
