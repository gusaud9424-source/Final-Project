import secrets

from flask import Blueprint, jsonify, request, session

from . import limiter
from .course_content import DEFENSE_QUIZZES, public_quiz
from .models import TASK_KEYS, Course, Enrollment
from .practice_builders import PRACTICE_BUILDERS
from .quiz_bank import QUIZ_BANKS
from .progress import (
    TASK_TITLES,
    completed_tasks,
    current_user,
    mark_task_complete,
    progress_summary,
    serialize_datetime,
)
from .rewards import roll_pending

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
    # 미션 보상은 과목별 고정 1종, 미수령 상태로 생성(수령은 보물상자에서)
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

    return jsonify(hints=builder.hints(difficulty))


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

    result = builder.run(difficulty, user_input)

    rewarded = False
    xp_amount = None
    point_amount = None
    if result.success:
        mark_task_complete(user.id, course.id, "practice")
        # 실습 보상은 XP·포인트 2종, 미수령 상태로 생성(수령은 보물상자에서)
        rows = roll_pending(user.id, "practice", f"{course.title} 실습", ref=f"practice:{course.slug}")
        if rows:
            amounts = {row.type: row.amount for row in rows}
            rewarded = True
            xp_amount = amounts["xp"]
            point_amount = amounts["point"]

    return jsonify(
        success=result.success,
        output=result.output,
        rewarded=rewarded,
        xp=xp_amount,
        points=point_amount,
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
