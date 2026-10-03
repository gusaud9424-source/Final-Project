import random
from datetime import datetime

from flask import Blueprint, current_app, jsonify
from sqlalchemy.exc import IntegrityError

from . import db, limiter
from .models import PointLedger, Reward, User, XpLedger
from .progress import current_user, serialize_datetime

bp = Blueprint("rewards", __name__, url_prefix="/api/v1/rewards")

LEVEL_CAP = 50

# 여기 등록된 source만 roll_pending으로 보상 생성 가능
XP_RANGES = {
    "practice": (50, 100),
    "mission": (30, 80),
}
POINT_RANGES = {
    "practice": (20, 40),
    "mission": (10, 30),
}

# 미션(방어 퀴즈) 보상 종류: 초급=경험치, 중급·고급=포인트
MISSION_REWARD_TYPE = {
    "command-injection": "xp",
    "xss-reflected": "xp",
    "xss-dom": "xp",
    "xss-stored": "xp",
    "sql-injection": "point",
    "csrf": "point",
    "file-upload": "point",
    "sql-injection-blind": "point",
}

LEDGER_MODELS = {"xp": XpLedger, "point": PointLedger}
RANGES = {"xp": XP_RANGES, "point": POINT_RANGES}


def compute_level(total_xp):
    """누적 XP로 레벨·다음 레벨까지 남은 XP 산출. L→L+1 필요 XP = L*100, 50레벨 상한"""
    level, remaining = 1, total_xp
    while level < LEVEL_CAP:
        needed = level * 100
        if remaining < needed:
            return {"level": level, "currentXp": remaining, "xpForNextLevel": needed, "totalXp": total_xp}
        remaining -= needed
        level += 1
    return {"level": LEVEL_CAP, "currentXp": remaining, "xpForNextLevel": None, "totalXp": total_xp}


def total_xp(user_id):
    total = db.session.query(db.func.coalesce(db.func.sum(XpLedger.amount), 0)).filter_by(user_id=user_id).scalar()
    return int(total)


def points_balance(user_id):
    total = db.session.query(db.func.coalesce(db.func.sum(PointLedger.amount), 0)).filter_by(user_id=user_id).scalar()
    return int(total)


def _reward_types(source, course_slug):
    """source별 생성할 보상 종류. 실습=XP+포인트, 미션=과목별 고정 1종"""
    if source == "practice":
        return ["xp", "point"]
    if source == "mission":
        reward_type = MISSION_REWARD_TYPE.get(course_slug)
        if not reward_type:
            # 잘못된 값으로 지급되지 않도록 미등록 과목은 보상을 만들지 않는다
            current_app.logger.warning("mission reward type not defined for course: %s", course_slug)
            return []
        return [reward_type]
    raise ValueError(f"unknown reward source: {source}")


def _already_rewarded(user_id, source, ref):
    """미수령·수령 보상 또는 기존 자동 지급 원장에 같은 이벤트가 있는지"""
    if Reward.query.filter_by(user_id=user_id, source=source, ref=ref).first():
        return True
    return any(
        model.query.filter_by(user_id=user_id, source=source, ref=ref).first()
        for model in LEDGER_MODELS.values()
    )


def roll_pending(user_id, source, reason, ref, course_slug=None):
    """source에 정의된 범위로 액수를 굴려 미수령 보상을 생성한다(원장 반영은 수령 시점).
    같은 ref로 이미 생성·지급된 이벤트면 빈 리스트 반환"""
    types = _reward_types(source, course_slug)
    if not types:
        return []

    # 동시 요청 직렬화: 사용자 행을 잠근 뒤 중복 확인 → 생성
    db.session.query(User).filter_by(id=user_id).with_for_update().one()
    if _already_rewarded(user_id, source, ref):
        db.session.rollback()
        return []

    rows = [
        Reward(
            user_id=user_id,
            type=reward_type,
            amount=random.randint(*RANGES[reward_type][source]),
            source=source,
            ref=ref,
            reason=reason,
        )
        for reward_type in types
    ]
    db.session.add_all(rows)
    try:
        db.session.commit()
    except IntegrityError:
        # UNIQUE(user_id, source, ref, type) 위반 시 이미 생성된 것으로 간주
        db.session.rollback()
        return []
    return rows


def _apply_claim(reward):
    """미수령 보상을 수령 처리하고 원장에 같은 source·ref로 기록(커밋은 호출부)"""
    reward.claimed_at = datetime.utcnow()
    ledger_model = LEDGER_MODELS[reward.type]
    db.session.add(
        ledger_model(
            user_id=reward.user_id,
            source=reward.source,
            ref=reward.ref,
            amount=reward.amount,
            reason=reward.reason,
        )
    )


def serialize_reward(reward):
    return {
        "id": reward.id,
        "type": reward.type,
        "amount": reward.amount,
        "reason": reward.reason,
        "createdAt": serialize_datetime(reward.created_at),
    }


def _balance(user_id):
    level_info = compute_level(total_xp(user_id))
    return {
        "level": level_info["level"],
        "currentXp": level_info["currentXp"],
        "xpForNextLevel": level_info["xpForNextLevel"],
        "totalXp": level_info["totalXp"],
        "points": points_balance(user_id),
    }


@bp.get("/pending")
def list_pending():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    rows = (
        Reward.query.filter_by(user_id=user.id, claimed_at=None)
        .order_by(Reward.created_at.desc(), Reward.id.desc())
        .all()
    )
    return jsonify(items=[serialize_reward(row) for row in rows], count=len(rows))


# 보상 수령은 과목 상세 > 미션 탭에서만 가능하다 (courses.py 의 /<slug>/rewards/<task>/claim).
# 헤더 보물상자의 개별·일괄 수령 API(/rewards/<id>/claim, /rewards/claim-all)는 제거했다.
