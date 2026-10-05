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
# practice_<레벨>: 실습 레벨별 클리어 보상. 높은 레벨일수록 크게, 안전 레벨은 방어 확인용으로 작게.
# (practice: 레벨 구조 도입 전 과목당 1회 실습 보상 — 기존 기록 표시용으로 유지)
XP_RANGES = {
    "concept": (20, 50),
    "practice": (50, 100),
    "practice_low": (20, 40),
    "practice_medium": (40, 70),
    "practice_high": (70, 110),
    "practice_impossible": (20, 40),
    "mission": (30, 80),
}
POINT_RANGES = {
    "concept": (10, 20),
    "practice": (20, 40),
    "practice_low": (10, 20),
    "practice_medium": (20, 35),
    "practice_high": (35, 55),
    "practice_impossible": (10, 20),
    "mission": (10, 30),
}
PRACTICE_TIER_SOURCES = ("practice_low", "practice_medium", "practice_high", "practice_impossible")

# 과목 미션 보상 source (헤더 보물상자가 아니라 과목 미션 탭에서만 수령)
# 과목 미션 탭에서만 수령하는 보상: 1회차 개념 학습 · 2회차 실습 성공 · 3회차 방어 퀴즈(각 1개)
# 실습 페이지의 레벨별 클리어 보상(practice_<레벨>)은 보물상자에서 수령한다.
COURSE_REWARD_SOURCES = ("concept", "practice", "mission")

# 과목별 단일 보상 종류 (실습·미션 공통): 초급=경험치, 중급·고급=포인트
COURSE_REWARD_TYPE = {
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
    """source별 생성할 보상 종류. 개념·실습·미션 모두 과목별 고정 1종(경험치 또는 포인트)."""
    if source in ("concept", "practice", "mission") or source in PRACTICE_TIER_SOURCES:
        reward_type = COURSE_REWARD_TYPE.get(course_slug)
        if not reward_type:
            # 잘못된 값으로 지급되지 않도록 미등록 과목은 보상을 만들지 않는다
            current_app.logger.warning("reward type not defined for course: %s", course_slug)
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


# ─── 레벨업 보상 ───
# 레벨이 오를 때마다 보물상자로 보상 1개 지급. 종류는 경험치/포인트 중 랜덤,
# 금액은 레벨이 높을수록 커진다. 같은 레벨은 ref("levelup:<레벨>")로 1회만 생성(멱등).
LEVELUP_SOURCE = "levelup"


def levelup_range(reward_type, level):
    """레벨별 레벨업 보상 금액 범위 (예: 2레벨 경험치 50~80, 10레벨 경험치 170~240)"""
    if reward_type == "xp":
        return (20 + level * 15, 40 + level * 20)
    return (10 + level * 5, 20 + level * 8)


def ensure_levelup_rewards(user_id):
    """현재 레벨까지 받지 않은 레벨업 보상을 미수령 상태로 생성한다(2레벨부터).
    레벨업 보상(경험치)을 받아 다시 레벨이 오르면 다음 호출 때 그 레벨 보상도 생성된다."""
    level = compute_level(total_xp(user_id))["level"]
    if level < 2:
        return []

    # 동시 요청 직렬화: 사용자 행을 잠근 뒤 중복 확인 → 생성
    db.session.query(User).filter_by(id=user_id).with_for_update().one()
    created = []
    for lv in range(2, level + 1):
        ref = f"{LEVELUP_SOURCE}:{lv}"
        if _already_rewarded(user_id, LEVELUP_SOURCE, ref):
            continue
        reward_type = random.choice(("xp", "point"))
        row = Reward(
            user_id=user_id,
            type=reward_type,
            amount=random.randint(*levelup_range(reward_type, lv)),
            source=LEVELUP_SOURCE,
            ref=ref,
            reason=f"레벨 {lv} 달성",
        )
        db.session.add(row)
        created.append(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return []
    return created


def _balance_after_claim(user_id):
    """수령 직후 레벨업 보상을 확인·생성한 뒤 잔액 반환"""
    ensure_levelup_rewards(user_id)
    return _balance(user_id)


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

    # 놓친 레벨업 보상이 있으면 먼저 생성(보물상자에 표시)
    ensure_levelup_rewards(user.id)

    # 과목 미션 보상(개념·실습·미션)은 과목 미션 탭에서만 수령한다.
    # 보물상자에는 그 외 보상만 모은다.
    rows = (
        Reward.query.filter_by(user_id=user.id, claimed_at=None)
        .filter(Reward.source.notin_(COURSE_REWARD_SOURCES))
        .order_by(Reward.created_at.desc(), Reward.id.desc())
        .all()
    )
    return jsonify(items=[serialize_reward(row) for row in rows], count=len(rows))


@bp.post("/<int:reward_id>/claim")
@limiter.limit("30 per minute")
def claim_reward(reward_id):
    """보물상자 개별 수령 — 과목 미션(개념·실습 성공·퀴즈) 보상은 여기서 받지 않는다(미션 탭 전용)."""
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    reward = Reward.query.filter_by(id=reward_id, user_id=user.id).with_for_update().first()
    if not reward:
        db.session.rollback()
        return jsonify(message="존재하지 않는 보상입니다."), 404
    if reward.source in COURSE_REWARD_SOURCES:
        db.session.rollback()
        return jsonify(message="이 보상은 과목의 미션 탭에서 받으세요."), 400
    if reward.claimed_at:
        db.session.rollback()
        return jsonify(message="이미 받은 보상입니다."), 409

    _apply_claim(reward)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="이미 받은 보상입니다."), 409

    return jsonify(claimed=[serialize_reward(reward)], profile=_balance_after_claim(user.id))


@bp.post("/claim-all")
@limiter.limit("5 per minute")
def claim_all():
    """보물상자 일괄 수령 — 미션 보상은 제외한다."""
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    rewards = (
        Reward.query.filter_by(user_id=user.id, claimed_at=None)
        .filter(Reward.source.notin_(COURSE_REWARD_SOURCES))
        .with_for_update()
        .all()
    )
    for reward in rewards:
        _apply_claim(reward)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="보상 수령 중 충돌이 발생했습니다. 다시 시도하세요."), 409

    return jsonify(claimed=[serialize_reward(reward) for reward in rewards], profile=_balance_after_claim(user.id))
