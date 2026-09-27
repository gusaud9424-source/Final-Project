import re

from flask import Blueprint, jsonify, request

from . import db, limiter
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


@bp.patch("")
@limiter.limit("5 per minute")
def update_profile():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    payload = request.get_json(silent=True) or {}
    nickname = (payload.get("nickname") or "").strip()
    if not (2 <= len(nickname) <= 20):
        return jsonify(message="닉네임은 2~20자여야 합니다."), 400
    if not NICKNAME_RE.match(nickname):
        return jsonify(message="닉네임은 한글·영문·숫자·밑줄만 사용할 수 있습니다."), 400

    conflict = User.query.filter(User.nickname == nickname, User.id != user.id).first()
    if conflict:
        return jsonify(message="이미 사용 중인 닉네임입니다."), 409

    user.nickname = nickname
    db.session.commit()
    return jsonify(nickname=user.nickname)
