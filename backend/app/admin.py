"""관리자 전용 API — 회원관리(목록·임시 비밀번호 발급·삭제) · 관리자 비밀번호 변경

관리자 기능은 실습 페이지가 아니므로 표준 보안 규칙을 따른다.
- 전역 CSRFProtect (모든 비-GET 요청)
- 역할 검사 (role == "admin")
- limiter 로 요청 횟수 제한
- 변경 작업은 [AUDIT] 로그로 남긴다
"""
import secrets
import string

import bcrypt
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func

from . import db, limiter
from .models import (
    AttendanceSession,
    Enrollment,
    PointLedger,
    Reward,
    TaskProgress,
    User,
    VerificationCode,
    XpLedger,
)
from .progress import current_user

bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")

MIN_PASSWORD_LENGTH = 8
TEMP_PASSWORD_LENGTH = 10


def _require_admin():
    """(admin, error_response) — 관리자가 아니면 error_response 반환"""
    user = current_user()
    if not user:
        return None, (jsonify(message="로그인이 필요합니다."), 401)
    if user.role != "admin":
        return None, (jsonify(message="권한이 없습니다."), 403)
    return user, None


def _audit(admin, action, target=None):
    # 감사 로그: 누가(관리자) · 무엇을 · 누구에게 · 어디서
    current_app.logger.warning(
        "[AUDIT] admin_id=%s action=%s target_user_id=%s ip=%s",
        admin.id,
        action,
        target.id if target else "-",
        request.remote_addr,
    )


def _hash_password(raw):
    # bcrypt salt round 12 (gensalt 기본값)
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _generate_temp_password():
    # 영문 대소문자 + 숫자, 각 1자 이상 포함
    alphabet = string.ascii_letters + string.digits
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(TEMP_PASSWORD_LENGTH))
        if any(c.islower() for c in value) and any(c.isupper() for c in value) and any(c.isdigit() for c in value):
            return value


def _serialize_member(user, course_counts, point_sums):
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "nickname": user.nickname,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "createdAt": user.created_at.isoformat(timespec="seconds") + "Z" if user.created_at else None,
        "courseCount": course_counts.get(user.id, 0),
        "points": int(point_sums.get(user.id, 0) or 0),
    }


@bp.get("/users")
def list_users():
    admin, error = _require_admin()
    if error:
        return error

    keyword = (request.args.get("q") or "").strip()
    query = User.query.filter_by(role="student")
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            db.or_(User.username.ilike(like), User.name.ilike(like), User.email.ilike(like))
        )
    users = query.order_by(User.created_at.desc(), User.id.desc()).all()
    ids = [u.id for u in users]

    course_counts, point_sums = {}, {}
    if ids:
        course_counts = dict(
            db.session.query(Enrollment.user_id, func.count(Enrollment.id))
            .filter(Enrollment.user_id.in_(ids))
            .group_by(Enrollment.user_id)
            .all()
        )
        point_sums = dict(
            db.session.query(PointLedger.user_id, func.sum(PointLedger.amount))
            .filter(PointLedger.user_id.in_(ids))
            .group_by(PointLedger.user_id)
            .all()
        )

    return jsonify(users=[_serialize_member(u, course_counts, point_sums) for u in users])


def _load_student(user_id):
    target = db.session.get(User, user_id)
    if not target:
        return None, (jsonify(message="존재하지 않는 회원입니다."), 404)
    if target.role != "student":
        return None, (jsonify(message="관리자 계정은 이 기능으로 관리할 수 없습니다."), 400)
    return target, None


@bp.post("/users/<int:user_id>/reset-password")
@limiter.limit("10 per minute")
def reset_user_password(user_id):
    admin, error = _require_admin()
    if error:
        return error
    target, error = _load_student(user_id)
    if error:
        return error

    temp_password = _generate_temp_password()
    target.password_hash = _hash_password(temp_password)
    db.session.commit()
    _audit(admin, "reset_password", target)
    # 임시 비밀번호는 이 응답에서 한 번만 노출 (DB에는 해시만 저장)
    return jsonify(message="임시 비밀번호가 발급되었습니다.", tempPassword=temp_password)


@bp.delete("/users/<int:user_id>")
@limiter.limit("10 per minute")
def delete_user(user_id):
    admin, error = _require_admin()
    if error:
        return error
    target, error = _load_student(user_id)
    if error:
        return error

    # users.id 를 참조하는 자식 행을 먼저 정리 (외래키 제약)
    enrollment_ids = [e.id for e in Enrollment.query.filter_by(user_id=target.id).all()]
    if enrollment_ids:
        AttendanceSession.query.filter(AttendanceSession.enrollment_id.in_(enrollment_ids)).delete(
            synchronize_session=False
        )
    for model in (Enrollment, TaskProgress, Reward, PointLedger, XpLedger, VerificationCode):
        model.query.filter_by(user_id=target.id).delete(synchronize_session=False)
    db.session.delete(target)
    db.session.commit()
    _audit(admin, "delete_user", target)
    return "", 204


@bp.post("/password")
@limiter.limit("5 per minute")
def change_admin_password():
    admin, error = _require_admin()
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password", "")
    new_password = payload.get("new_password", "")
    if not isinstance(current_password, str) or not isinstance(new_password, str):
        return jsonify(message="잘못된 요청입니다."), 400

    if not bcrypt.checkpw(current_password.encode("utf-8"), admin.password_hash.encode("utf-8")):
        return jsonify(message="현재 비밀번호가 올바르지 않습니다."), 400
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return jsonify(message=f"새 비밀번호는 {MIN_PASSWORD_LENGTH}자 이상이어야 합니다."), 400
    if new_password == current_password:
        return jsonify(message="새 비밀번호가 현재 비밀번호와 같습니다."), 400

    admin.password_hash = _hash_password(new_password)
    db.session.commit()
    _audit(admin, "change_own_password")
    return jsonify(message="비밀번호가 변경되었습니다.")
