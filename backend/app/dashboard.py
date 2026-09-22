from flask import Blueprint, jsonify, session
from sqlalchemy.orm import joinedload, selectinload

from . import db
from .models import Enrollment, User

bp = Blueprint("dashboard", __name__, url_prefix="/api/v1")


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def _serialize_course(enrollment):
    course = enrollment.course
    sessions = [
        {"n": s.session_no, "status": s.status} for s in enrollment.attendance_sessions
    ]
    done = sum(1 for s in enrollment.attendance_sessions if s.status == "submitted")
    return {
        "id": course.id,
        "icon": course.icon,
        "title": course.title,
        "description": course.description,
        "instructor": course.instructor,
        "schedule": course.schedule,
        "percent": enrollment.percent,
        "badge": {"type": enrollment.badge_type, "label": enrollment.badge_label},
        "attendance": {
            "done": done,
            "total": len(sessions),
            "sessions": sessions,
        },
    }


def _student_dashboard(user):
    enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    courses = [_serialize_course(e) for e in enrollments]
    total_rounds = sum(c["attendance"]["total"] for c in courses)
    completed_rounds = sum(c["attendance"]["done"] for c in courses)
    percent = round(completed_rounds / total_rounds * 100) if total_rounds else 0
    return jsonify(
        role="student",
        summary={
            "courseCount": len(courses),
            "completedRounds": completed_rounds,
            "totalRounds": total_rounds,
            "percent": percent,
        },
        courses=courses,
    )


def _students_overview():
    students = (
        User.query.filter_by(role="student")
        .options(
            selectinload(User.enrollments).joinedload(Enrollment.course),
            selectinload(User.enrollments).selectinload(Enrollment.attendance_sessions),
        )
        .all()
    )
    return [
        {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "courses": [_serialize_course(e) for e in student.enrollments],
        }
        for student in students
    ]


@bp.get("/dashboard")
def dashboard():
    user = _current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401
    if user.role == "admin":
        return jsonify(role="admin", students=_students_overview())
    return _student_dashboard(user)


@bp.get("/admin/students")
def admin_students():
    user = _current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401
    if user.role != "admin":
        return jsonify(message="권한이 없습니다."), 403
    return jsonify(students=_students_overview())
