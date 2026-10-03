"""로그인 출석 체크판 — 14일(2줄), 하루 1회, 포인트만 랜덤 지급.

별도 테이블 없이 PointLedger(source="attendance")를 진실의 원천으로 사용한다.
  - ref="att:<KST 날짜>" 로 '하루 1회' 를 UNIQUE(user,source,ref)로 강제
  - 적립 순서(created_at)로 N일차를 산출
  - 7·14일차는 보너스 범위로 더 많은 포인트
"""
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify
from sqlalchemy.exc import IntegrityError

from . import db, limiter
from .models import PointLedger
from .progress import current_user
from .rewards import points_balance

bp = Blueprint("attendance", __name__, url_prefix="/api/v1/attendance")

BOARD_DAYS = 14
BONUS_DAYS = {7, 14}
NORMAL_RANGE = (50, 200)
BONUS_RANGE = (300, 500)
_KST = ZoneInfo("Asia/Seoul")


def _today():
    return datetime.now(_KST).date().isoformat()


def _rows(user_id):
    return (
        PointLedger.query.filter_by(user_id=user_id, source="attendance")
        .order_by(PointLedger.created_at.asc(), PointLedger.id.asc())
        .all()
    )


def _roll(day):
    lo, hi = BONUS_RANGE if day in BONUS_DAYS else NORMAL_RANGE
    return random.randint(lo, hi)


def _board_state(user_id):
    rows = _rows(user_id)
    claimed_count = len(rows)
    today = _today()
    claimed_today = any((r.ref or "") == f"att:{today}" for r in rows)
    completed = min(claimed_count, BOARD_DAYS)
    next_day = completed + 1
    can_claim = completed < BOARD_DAYS and not claimed_today

    days = []
    for d in range(1, BOARD_DAYS + 1):
        if d <= completed:
            state, amount = "claimed", rows[d - 1].amount
        elif d == next_day and can_claim:
            state, amount = "claimable", None
        else:
            state, amount = "locked", None
        days.append({"day": d, "state": state, "amount": amount, "bonus": d in BONUS_DAYS})

    return {
        "days": days,
        "canClaimToday": can_claim,
        "nextDay": next_day if completed < BOARD_DAYS else None,
        "completed": completed,
        "claimedToday": claimed_today,
        "points": points_balance(user_id),
    }


@bp.get("")
def get_board():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401
    return jsonify(_board_state(user.id))


@bp.post("/claim")
@limiter.limit("20 per minute")
def claim():
    user = current_user()
    if not user:
        return jsonify(message="로그인이 필요합니다."), 401

    rows = _rows(user.id)
    completed = min(len(rows), BOARD_DAYS)
    today = _today()

    if completed >= BOARD_DAYS:
        return jsonify(message="14일 출석을 모두 완료했습니다."), 409
    if any((r.ref or "") == f"att:{today}" for r in rows):
        return jsonify(message="오늘은 이미 출석했습니다."), 409

    day = completed + 1
    amount = _roll(day)
    db.session.add(
        PointLedger(
            user_id=user.id,
            source="attendance",
            ref=f"att:{today}",
            amount=amount,
            reason=f"출석 {day}일차",
        )
    )
    try:
        db.session.commit()
    except IntegrityError:
        # 같은 날짜 ref UNIQUE 위반 = 동시요청으로 이미 출석됨
        db.session.rollback()
        return jsonify(message="오늘은 이미 출석했습니다."), 409

    state = _board_state(user.id)
    return jsonify(day=day, amount=amount, bonus=day in BONUS_DAYS, points=state["points"], board=state)
