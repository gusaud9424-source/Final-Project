import secrets

from flask import Blueprint, jsonify, request, session
from sqlalchemy.exc import IntegrityError

from . import db, limiter
from .course_content import DEFENSE_QUIZZES, public_quiz
from .models import TASK_KEYS, Course, Enrollment, Reward
from .practice_builders import PRACTICE_BUILDERS
from .quiz_bank import QUIZ_BANKS
from .progress import (
    TASK_TITLES,
    cleared_tiers,
    completed_tasks,
    current_user,
    is_tier_unlocked,
    mark_task_complete,
    mark_tier_cleared,
    tier_states,
    TIER_LABELS,
    progress_summary,
    serialize_datetime,
)
from .rewards import COURSE_REWARD_SOURCES, COURSE_REWARD_TYPE, LEDGER_MODELS, RANGES, _apply_claim, _balance, _reward_types, roll_pending

bp = Blueprint("courses", __name__, url_prefix="/api/v1/courses")


def _load_enrolled_course(slug):
    """(user, course, error_response) 반환. 로그인·과목 존재·수강 여부 순으로 검사"""
    user = current_user()
    if not user:
        return None, None, (jsonify(message="로그인이 필요합니다."), 401)

    course = Course.query.filter_by(slug=slug).first()
    if not course:
        return None, None, (jsonify(message="존재하지 않는 과목입니다."), 404)

    enrolled = Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first()
    if not enrolled:
        return None, None, (jsonify(message="수강 중인 과목이 아닙니다."), 403)

    return user, course, None


@bp.get("/<slug>")
def course_detail(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    done = completed_tasks(user.id, course.id)
    tasks = [
        {
            "key": key,
            "title": TASK_TITLES[key],
            "completed": key in done,
            "completedAt": serialize_datetime(done.get(key)),
        }
        for key in TASK_KEYS
    ]
    return jsonify(
        course={
            "slug": course.slug,
            "title": course.title,
            "description": course.description,
            "icon": course.icon,
            "difficulty": course.difficulty,
            "quizSetAvailable": course.slug in QUIZ_BANKS,
        },
        tasks=tasks,
        progress=progress_summary(done),
        quiz=public_quiz(course.slug),
    )


@bp.post("/<slug>/tasks/concept")
def complete_concept(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    record = mark_task_complete(user.id, course.id, "concept")
    # 개념 학습 보상도 미수령 상태로 생성(수령은 미션 탭)
    roll_pending(
        user.id, "concept", f"{course.title} 개념 학습", ref=f"concept:{course.slug}", course_slug=course.slug
    )
    return jsonify(taskKey="concept", completed=True, completedAt=serialize_datetime(record.completed_at))


@bp.post("/<slug>/quiz")
@limiter.limit("10 per minute")
def submit_quiz(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    quiz = DEFENSE_QUIZZES.get(course.slug)
    if not quiz:
        return jsonify(message="이 과목에는 퀴즈가 없습니다."), 404

    payload = request.get_json(silent=True) or {}
    answer = payload.get("answer")
    # bool 은 int 하위 타입이므로 명시적으로 제외
    if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < len(quiz["options"]):
        return jsonify(message="올바른 보기를 선택하세요."), 400

    if answer != quiz["answer"]:
        return jsonify(correct=False, explanation=quiz["explanation"])

    mark_task_complete(user.id, course.id, "defense")
    # 미션 보상은 과목별 고정 1종, 미수령 상태로 생성(수령은 과목 상세 > 미션 탭에서)
    rows = roll_pending(
        user.id, "mission", f"{course.title} 미션", ref=f"mission:{course.slug}", course_slug=course.slug
    )
    reward = rows[0] if rows else None
    return jsonify(
        correct=True,
        rewarded=reward is not None,
        rewardType=reward.type if reward else None,
        amount=reward.amount if reward else None,
    )


@bp.get("/<slug>/practice/hints")
def practice_hints(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    builder = PRACTICE_BUILDERS.get(course.slug)
    if not builder:
        return jsonify(message="이 과목에는 아직 실습이 없습니다."), 404

    difficulty = request.args.get("difficulty", "")
    if difficulty not in builder.difficulties:
        return jsonify(message="지원하지 않는 난이도입니다."), 400

    # 잠긴 레벨의 힌트는 제공하지 않는다(하 → 중 → 상 순서 학습)
    if not is_tier_unlocked(difficulty, cleared_tiers(user.id, course.id)):
        return jsonify(message=_TIER_LOCKED_MESSAGE), 403

    return jsonify(hints=builder.hints(difficulty))


_TIER_LOCKED_MESSAGE = "이전 레벨을 먼저 통과해야 이 레벨을 학습할 수 있습니다."
# 실습 미션(2회차) 완료 조건: 이 레벨을 모두 통과 (보상은 레벨마다 따로 지급)
PRACTICE_REWARD_TIERS = ("low", "medium", "high")


@bp.get("/<slug>/practice/tiers")
def practice_tiers(slug):
    """레벨별 잠금·통과 상태 (하 → 중 → 상 → 안전)"""
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    if course.slug not in PRACTICE_BUILDERS:
        return jsonify(message="이 과목에는 아직 실습이 없습니다."), 404

    cleared = cleared_tiers(user.id, course.id)
    # 레벨별 보상 도입 전에 통과한 레벨도 보상 지급(멱등: 이미 생성·지급된 레벨은 건너뜀)
    for tier in cleared:
        _roll_tier_reward(user.id, course, tier)
    return jsonify(tiers=tier_states(cleared))


def _roll_tier_reward(user_id, course, tier):
    """레벨 클리어 보상 생성(보물상자 수령). 같은 레벨은 한 번만 생성된다."""
    return roll_pending(
        user_id,
        f"practice_{tier}",
        f"{course.title} 실습 {TIER_LABELS[tier]} 레벨",
        ref=f"practice:{course.slug}:{tier}",
        course_slug=course.slug,
    )


@bp.post("/<slug>/practice/run")
@limiter.limit("90 per minute")  # Blind SQLi 등 반복 요청 실습을 위해 상향 (학습용 단일 사용자 기준)
def run_practice(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    builder = PRACTICE_BUILDERS.get(course.slug)
    if not builder:
        return jsonify(message="이 과목에는 아직 실습이 없습니다."), 404

    payload = request.get_json(silent=True) or {}
    difficulty = payload.get("difficulty")
    user_input = payload.get("input", "")

    error_message = builder.validate_input(difficulty, user_input)
    if error_message:
        return jsonify(message=error_message), 400

    # 서버에서도 레벨 순서를 강제한다(화면 조작으로 잠긴 레벨을 실행하는 것 방지)
    if not is_tier_unlocked(difficulty, cleared_tiers(user.id, course.id)):
        return jsonify(message=_TIER_LOCKED_MESSAGE), 403

    result = builder.run(difficulty, user_input)

    # 레벨 통과 판정
    # - 하·중·상: 공격 성공 시 통과
    # - 안전: 공격이 막히는 것을 직접 확인(1회 이상 시도)하면 통과
    tier_cleared = False
    if difficulty == "impossible" or result.success:
        mark_tier_cleared(user.id, course.id, difficulty)
        tier_cleared = True

    rewarded = False
    xp_amount = None
    point_amount = None
    # 레벨 클리어 보상: 하·중·상·안전 각 레벨을 처음 통과할 때마다 지급 (수령은 헤더 보물상자)
    cleared_now = cleared_tiers(user.id, course.id)
    if tier_cleared:
        rows = _roll_tier_reward(user.id, course, difficulty)
        if rows:
            # 실습 보상도 과목별 1종(경험치 또는 포인트). 해당 종류만 금액을 채운다.
            amounts = {row.type: row.amount for row in rows}
            rewarded = True
            xp_amount = amounts.get("xp")
            point_amount = amounts.get("point")

    # 실습 미션(2회차) 완료 조건: 하·중·상 3개 레벨 모두 통과 → 미션 탭에서 받을 보상 1개 생성
    if set(PRACTICE_REWARD_TIERS) <= cleared_now:
        mark_task_complete(user.id, course.id, "practice")
        roll_pending(
            user.id, "practice", f"{course.title} 실습 성공", ref=f"practice:{course.slug}", course_slug=course.slug
        )

    return jsonify(
        success=result.success,
        output=result.output,
        rewarded=rewarded,
        xp=xp_amount,
        points=point_amount,
        tierCleared=tier_cleared,
        tiers=tier_states(cleared_now),
    )


def _quiz_session_key(slug):
    return f"quiz_attempt:{slug}"


def _load_attempt(slug, attempt_id):
    """세션에 저장된 진행 중 attempt 반환. attempt_id 불일치·미존재면 None"""
    record = session.get(_quiz_session_key(slug))
    if not record or not attempt_id or record.get("attempt_id") != attempt_id:
        return None
    return record


@bp.get("/<slug>/quiz-set")
def quiz_set(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    bank = QUIZ_BANKS.get(course.slug)
    if not bank:
        return jsonify(message="이 과목에는 퀴즈 세트가 없습니다."), 404

    # 기존 진행 중이던 attempt는 폐기하고 새로 시작
    attempt_id = secrets.token_urlsafe(16)
    session[_quiz_session_key(course.slug)] = {"attempt_id": attempt_id, "answers": {}}

    questions = [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in bank]
    return jsonify(attemptId=attempt_id, questions=questions)


@bp.post("/<slug>/quiz-set/answer")
@limiter.limit("100 per minute")
def quiz_set_answer(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    bank = QUIZ_BANKS.get(course.slug)
    if not bank:
        return jsonify(message="이 과목에는 퀴즈 세트가 없습니다."), 404

    payload = request.get_json(silent=True) or {}
    attempt_id = payload.get("attemptId")
    question_id = payload.get("questionId")
    choice = payload.get("choice")

    attempt = _load_attempt(course.slug, attempt_id)
    if attempt is None:
        return jsonify(message="진행 중인 퀴즈가 없습니다."), 404

    question = next((q for q in bank if q["id"] == question_id), None)
    if question is None:
        return jsonify(message="존재하지 않는 문항입니다."), 404

    if question_id in attempt["answers"]:
        return jsonify(message="이미 응답한 문항입니다."), 409

    if not isinstance(choice, int) or isinstance(choice, bool) or not 0 <= choice < len(question["options"]):
        return jsonify(message="올바른 보기를 선택하세요."), 400

    attempt["answers"][question_id] = choice
    session[_quiz_session_key(course.slug)] = attempt
    session.modified = True

    return jsonify(correct=choice == question["answer"], answer=question["answer"])


@bp.post("/<slug>/quiz-set/submit")
@limiter.limit("10 per minute")
def quiz_set_submit(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error

    bank = QUIZ_BANKS.get(course.slug)
    if not bank:
        return jsonify(message="이 과목에는 퀴즈 세트가 없습니다."), 404

    payload = request.get_json(silent=True) or {}
    attempt_id = payload.get("attemptId")

    attempt = _load_attempt(course.slug, attempt_id)
    if attempt is None:
        return jsonify(message="진행 중인 퀴즈가 없습니다."), 404

    answers = attempt["answers"]
    if len(answers) != len(bank):
        return jsonify(message="모든 문항에 답해야 합니다."), 400

    results = []
    correct_count = 0
    for question in bank:
        choice = answers[question["id"]]
        is_correct = choice == question["answer"]
        if is_correct:
            correct_count += 1
        results.append(
            {
                "questionId": question["id"],
                "correct": is_correct,
                "choice": choice,
                "answer": question["answer"],
                "explanation": question["explanation"],
            }
        )

    score_percent = round(correct_count / len(bank) * 100)
    passed = score_percent >= 70

    rewarded = False
    reward_type = None
    amount = None
    if passed:
        mark_task_complete(user.id, course.id, "defense")
        # 기존 단일 방어 퀴즈(/quiz)와 동일 ref → 중복 지급 방지(roll_pending 내부 멱등 처리)
        rows = roll_pending(
            user.id, "mission", f"{course.title} 미션", ref=f"mission:{course.slug}", course_slug=course.slug
        )
        if rows:
            reward = rows[0]
            rewarded = True
            reward_type = reward.type
            amount = reward.amount

    session.pop(_quiz_session_key(course.slug), None)

    return jsonify(
        score=score_percent,
        total=len(bank),
        passed=passed,
        results=results,
        rewarded=rewarded,
        rewardType=reward_type,
        amount=amount,
    )


# ── 미션 탭 보상 ─────────────────────────────
# 1~3회차 미션 보상은 모두 미션 카드에서 수령 (실습 페이지 레벨별 보상만 보물상자)
# 미션(task) → 보상 source. concept(개념 학습)은 보상 없이 진도만 반영
TASK_REWARD_SOURCE = {"concept": "concept", "practice": "practice", "defense": "mission"}


def _task_reward_state(user_id, course, task_key):
    """미션 하나의 보상 상태: locked(미달성) / pending(수령 대기) / claimed(수령 완료) / none(보상 없음)"""
    source = TASK_REWARD_SOURCE.get(task_key)
    if not source:
        return {"status": "none", "items": []}
    ref = f"{source}:{course.slug}"

    # 과목별 보상 종류는 1종(경험치 또는 포인트). 구버전 데이터로 2종이 있어도 1종만 노출한다.
    canonical = COURSE_REWARD_TYPE.get(course.slug)
    rows = Reward.query.filter_by(user_id=user_id, source=source, ref=ref).order_by(Reward.type).all()
    shown = [r for r in rows if r.type == canonical] or rows
    if shown:
        pending = any(r.claimed_at is None for r in shown)
        return {
            "status": "pending" if pending else "claimed",
            # 수령 위치: 미션 탭(mission) / 헤더 보물상자(chest)
            "claimAt": "mission" if source in COURSE_REWARD_SOURCES else "chest",
            "items": [{"type": r.type, "amount": r.amount, "claimed": r.claimed_at is not None} for r in shown],
        }

    # 보물상자 도입 전 자동 지급된 기록(원장에 직접 기록)도 수령 완료로 표시 (1종만)
    model = LEDGER_MODELS.get(canonical)
    if model:
        row = model.query.filter_by(user_id=user_id, source=source, ref=ref).first()
        if row:
            return {"status": "claimed", "items": [{"type": canonical, "amount": row.amount, "claimed": True}]}

    # 아직 달성 전: 받을 보상 종류와 범위 미리보기
    return {
        "status": "locked",
        "items": [
            {"type": t, "min": RANGES[t][source][0], "max": RANGES[t][source][1]}
            for t in _reward_types(source, course.slug)
        ],
    }


@bp.get("/<slug>/rewards")
def course_rewards(slug):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error
    _backfill_mission_rewards(user.id, course)
    return jsonify(rewards={key: _task_reward_state(user.id, course, key) for key in TASK_KEYS})


# 미션 탭 수령 대상(1회차 개념 학습 · 2회차 실습 성공 · 3회차 방어 퀴즈) → (source, 보상 사유)
# 미션을 완수하면 미수령 보상 1개가 생기고, 미션 탭 오른쪽 칸을 클릭해 받는다.
_MISSION_TAB_REWARDS = {
    "concept": ("concept", "개념 학습"),
    "practice": ("practice", "실습 성공"),
    "defense": ("mission", "미션"),
}


def _backfill_mission_rewards(user_id, course):
    """미션을 완수했는데 보상 기록이 없으면(보상 기능 도입 전 완료 등) 미수령 보상을 생성한다.
    완수하지 않은 미션에는 절대 만들지 않으며, roll_pending 이 같은 ref 중복 생성을 막는다(멱등)."""
    done = completed_tasks(user_id, course.id)
    for task_key, (source, label) in _MISSION_TAB_REWARDS.items():
        if task_key not in done:
            continue
        roll_pending(
            user_id, source, f"{course.title} {label}", ref=f"{source}:{course.slug}", course_slug=course.slug
        )


@bp.post("/<slug>/rewards/<task_key>/claim")
@limiter.limit("30 per minute")
def claim_course_reward(slug, task_key):
    user, course, error = _load_enrolled_course(slug)
    if error:
        return error
    source = TASK_REWARD_SOURCE.get(task_key)
    if not source:
        return jsonify(message="보상이 없는 미션입니다."), 404
    # 실습 성공 보상은 보물상자 전용 (미션 탭에서는 상태만 표시)
    if source not in COURSE_REWARD_SOURCES:
        return jsonify(message="실습 보상은 헤더의 보물상자에서 받으세요."), 400

    # 본인 · 해당 미션의 미수령 보상만 잠금 조회. 금액·종류는 DB 값만 사용
    rows = (
        Reward.query.filter_by(user_id=user.id, source=source, ref=f"{source}:{course.slug}", claimed_at=None)
        .with_for_update()
        .all()
    )
    if not rows:
        db.session.rollback()
        return jsonify(message="받을 보상이 없습니다."), 409

    for reward in rows:
        _apply_claim(reward)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="이미 받은 보상입니다."), 409

    return jsonify(
        claimed=[{"type": r.type, "amount": r.amount} for r in rows],
        reward=_task_reward_state(user.id, course, task_key),
        profile=_balance(user.id),
    )
