import re

import bcrypt
from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy.exc import IntegrityError

from . import db, limiter
from .auth import EMAIL_RE, NAME_MAX, PHONE_RE, _normalize_phone, _password_policy_error
from .models import User
from .progress import current_user
from .rewards import compute_level, points_balance, total_xp

bp = Blueprint("profile", __name__, url_prefix="/api/v1/profile")

NICKNAME_RE = re.compile(r"^[a-zA-Z0-9가-힣_]+$")


@bp.get("")
def get_profile():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    level_info = compute_level(total_xp(user.id))
    return jsonify(
        nickname=user.nickname or user.name,
        level=level_info["level"],
        currentXp=level_info["currentXp"],
        xpForNextLevel=level_info["xpForNextLevel"],
        totalXp=level_info["totalXp"],
        points=points_balance(user.id),
    )



# ─────────────────────────────────────────────
# 마이페이지: 회원정보 조회 · 수정 · 비밀번호 변경
# (닉네임 변경도 여기서만 처리. 비밀번호 확인 없던 PATCH /profile 은 제거)
# ─────────────────────────────────────────────

def _audit(user, action, detail=""):
    """인증 관련 변경은 [AUDIT] 로그로 남김 (관리자 기능과 같은 형식)"""
    suffix = f" {detail}" if detail else ""
    current_app.logger.info(
        "[AUDIT] user_id=%s action=%s%s ip=%s", user.id, action, suffix, request.remote_addr
    )


def _check_current_password(user, raw):
    if not isinstance(raw, str) or not raw:
        return False
    return bcrypt.checkpw(raw.encode("utf-8"), user.password_hash.encode("utf-8"))


def _serialize_account(user):
    return dict(
        username=user.username,
        role=user.role,
        name=user.name,
        nickname=user.nickname or "",
        email=user.email,
        phone=user.phone,
        createdAt=user.created_at.isoformat() if user.created_at else None,
    )


@bp.get("/account")
def get_account():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401
    return jsonify(_serialize_account(user))


def _validate_account(name, nickname, email, phone):
    """회원정보 입력 검증 (회원가입 · 닉네임 규칙과 같은 기준)"""
    if not name or len(name) > NAME_MAX:
        return f"이름은 1~{NAME_MAX}자로 입력하세요."
    if nickname and not (2 <= len(nickname) <= 20):
        return "닉네임은 2~20자여야 합니다."
    if nickname and not NICKNAME_RE.match(nickname):
        return "닉네임은 한글·영문·숫자·밑줄만 사용할 수 있습니다."
    if len(email) > 120 or not EMAIL_RE.match(email):
        return "이메일 형식이 올바르지 않습니다."
    if not PHONE_RE.match(phone):
        return "휴대폰 번호는 숫자 10~11자리(예: 01012345678)로 입력하세요."
    return None


@bp.patch("/account")
@limiter.limit("5 per minute")
def update_account():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    payload = request.get_json(silent=True) or {}
    # 개인정보 변경은 현재 비밀번호를 다시 확인 (자리를 비운 사이 다른 사람이 바꾸는 것 방지)
    if not _check_current_password(user, payload.get("current_password")):
        return jsonify(message="현재 비밀번호가 올바르지 않습니다."), 400

    name = str(payload.get("name", "")).strip()
    nickname = str(payload.get("nickname", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    phone = _normalize_phone(str(payload.get("phone", "")))

    error = _validate_account(name, nickname, email, phone)
    if error:
        return jsonify(message=error), 400

    if nickname and User.query.filter(User.nickname == nickname, User.id != user.id).first():
        return jsonify(message="이미 사용 중인 닉네임입니다."), 409
    if User.query.filter(User.email == email, User.id != user.id).first():
        return jsonify(message="이미 사용 중인 이메일입니다."), 409

    # 감사 로그에는 값이 아니라 바뀐 항목 이름만 남김 (개인정보 노출 방지)
    changed = [
        field
        for field, old, new in (
            ("name", user.name, name),
            ("nickname", user.nickname or "", nickname),
            ("email", user.email, email),
            ("phone", user.phone, phone),
        )
        if old != new
    ]
    if not changed:
        return jsonify(message="변경된 내용이 없습니다.", **_serialize_account(user))

    user.name = name
    user.nickname = nickname or None
    user.email = email
    user.phone = phone
    try:
        db.session.commit()
    except IntegrityError:
        # 중복 확인과 저장 사이에 같은 값이 먼저 저장된 경우
        db.session.rollback()
        return jsonify(message="이미 사용 중인 닉네임 또는 이메일입니다."), 409

    _audit(user, "update_account", "fields=" + ",".join(changed))
    return jsonify(message="회원정보가 변경되었습니다.", **_serialize_account(user))


@bp.post("/password")
@limiter.limit("5 per minute")
def change_password():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password", "")
    new_password = payload.get("new_password", "")
    if not isinstance(new_password, str):
        return jsonify(message="입력 형식이 올바르지 않습니다."), 400
    if not _check_current_password(user, current_password):
        return jsonify(message="현재 비밀번호가 올바르지 않습니다."), 400
    if new_password == current_password:
        return jsonify(message="새 비밀번호가 현재 비밀번호와 같습니다."), 400

    error = _password_policy_error(new_password, user.username)  # 회원가입과 같은 규칙
    if error:
        return jsonify(message=error), 400

    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    db.session.commit()
    # 비밀번호가 바뀌면 세션 ID도 새로 발급 (기존 세션 ID 재사용 차단)
    current_app.session_interface.regenerate(session)
    _audit(user, "change_password")
    return jsonify(message="비밀번호가 변경되었습니다.")
