import random

from sqlalchemy.exc import IntegrityError

from . import db
from .models import PointLedger, XpLedger

LEVEL_CAP = 50

# 퀴즈는 순수 학습용이라 보상 대상에서 제외한다. 여기 등록된 source만 roll_and_grant로 지급 가능.
XP_RANGES = {
    "practice": (50, 100),
    "mission": (30, 80),
}
POINT_RANGES = {
    "practice": (20, 40),
    "mission": (10, 30),
}


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


def roll_and_grant(user_id, source, reason, ref=None):
    """source에 정의된 범위의 랜덤 XP·포인트를 굴려 원장에 함께 기록한다.
    ref가 있으면 1회성 이벤트로 취급해 중복 지급을 막는다(이미 지급된 경우 (None, None) 반환).
    ref=None은 반복 지급이 의도적으로 허용된 이벤트를 뜻한다."""
    if source not in XP_RANGES:
        raise ValueError(f"unknown reward source: {source}")

    if ref is not None and XpLedger.query.filter_by(user_id=user_id, source=source, ref=ref).first():
        return None, None

    xp_amount = random.randint(*XP_RANGES[source])
    point_amount = random.randint(*POINT_RANGES[source])
    xp_row = XpLedger(user_id=user_id, source=source, ref=ref, amount=xp_amount, reason=reason)
    point_row = PointLedger(user_id=user_id, source=source, ref=ref, amount=point_amount, reason=reason)
    db.session.add_all([xp_row, point_row])
    try:
        db.session.commit()
    except IntegrityError:
        # 동시 요청으로 UNIQUE(user_id, source, ref) 위반 시 이미 지급된 것으로 간주
        db.session.rollback()
        return None, None
    return xp_row, point_row
