from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from . import db
from .models import AttendanceSession, Course, Enrollment
from .progress import current_user

bp = Blueprint("enrollments", __name__, url_prefix="/api/v1")


@bp.get("/enrollments")
def list_enrollments():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    slugs = (
        db.session.query(Course.slug)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.user_id == user.id, Course.slug.isnot(None))
        .all()
    )
    return jsonify(enrollments=[slug for (slug,) in slugs])


@bp.post("/enrollments")
def create_enrollment():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    payload = request.get_json(silent=True) or {}
    course_slug = payload.get("course_slug")
    if not isinstance(course_slug, str) or not course_slug:
        return jsonify(message="course_slug가 필요합니다."), 400

    course = Course.query.filter_by(slug=course_slug).first()
    if not course:
        return jsonify(message="존재하지 않는 과목입니다."), 404

    if Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first():
        return jsonify(message="이미 수강 중인 과목입니다."), 409

    db.session.add(Enrollment(user_id=user.id, course_id=course.id))
    try:
        db.session.commit()
    except IntegrityError:
        # 동시 요청으로 UNIQUE(user_id, course_id) 위반 시 중복으로 처리
        db.session.rollback()
        return jsonify(message="이미 수강 중인 과목입니다."), 409

    return jsonify(course_slug=course.slug), 201


@bp.delete("/enrollments/<course_slug>")
def delete_enrollment(course_slug):
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    course = Course.query.filter_by(slug=course_slug).first()
    if not course:
        return jsonify(message="존재하지 않는 과목입니다."), 404

    enrollment = Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first()
    if not enrollment:
        return jsonify(message="수강 중인 과목이 아닙니다."), 404

    # 자식 행(출석 세션) 먼저 삭제 후 수강 정보 삭제
    # 실습·퀴즈 진도는 사용자 기준으로 보존 → 재수강 시 이어서 진행
    AttendanceSession.query.filter_by(enrollment_id=enrollment.id).delete()
    db.session.delete(enrollment)
    db.session.commit()
    return "", 204
