from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from . import db
from .models import AttendanceSession, Course, Enrollment, Reward, TaskProgress
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

    # 수강신청 = 처음부터 시작: 이전 수강 때 남은 진도·레벨 기록과 받지 않은 과목 보상을 정리해 0%에서 시작
    _reset_course_progress(user.id, course)
    db.session.add(Enrollment(user_id=user.id, course_id=course.id))
    try:
        db.session.commit()
    except IntegrityError:
        # 동시 요청으로 UNIQUE(user_id, course_id) 위반 시 중복으로 처리
        db.session.rollback()
        return jsonify(message="이미 수강 중인 과목입니다."), 409

    return jsonify(course_slug=course.slug), 201


def _reset_course_progress(user_id, course):
    """과목 진도 초기화(커밋은 호출부).
    - task_progress: 미션(개념·실습·퀴즈) + 레벨(tier_*) 기록 전부 삭제
    - rewards: 이 과목의 미수령 보상만 삭제
    이미 받은 보상(원장 기록)은 남겨 두므로, 다시 완수해도 같은 보상이 중복 지급되지 않는다."""
    TaskProgress.query.filter_by(user_id=user_id, course_id=course.id).delete(synchronize_session=False)
    Reward.query.filter(
        Reward.user_id == user_id,
        Reward.claimed_at.is_(None),
        db.or_(Reward.ref.like(f"%:{course.slug}"), Reward.ref.like(f"%:{course.slug}:%")),
    ).delete(synchronize_session=False)


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
    # 진도는 다음 수강신청 시 초기화된다(_reset_course_progress)
    AttendanceSession.query.filter_by(enrollment_id=enrollment.id).delete()
    db.session.delete(enrollment)
    db.session.commit()
    return "", 204
