"""관리자 전용 API — 수강생 진도 현황 · 회원관리(목록·임시 비밀번호 발급·삭제) · 관리자 비밀번호 변경

관리자 기능은 실습 페이지가 아니므로 표준 보안 규칙을 따른다.
- 전역 CSRFProtect (모든 비-GET 요청)
- 역할 검사 (role == "admin")
- limiter 로 요청 횟수 제한
- 변경 작업은 [AUDIT] 로그로 남긴다
"""
import secrets
import string
from collections import defaultdict
from datetime import datetime, timedelta

import bcrypt
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func

from . import db, limiter
from .models import (
    TASK_KEYS,
    AttendanceSession,
    Course,
    Enrollment,
    PointLedger,
    Reward,
    TaskProgress,
    User,
    VerificationCode,
    XpLedger,
)
from .progress import TASK_TOTAL, current_user

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


# ── 수강생 진도 현황 ─────────────────────────────────────────────

STALL_DAYS = 7  # 마지막 활동 후 이 기간이 지나면 "정체"
ACTIVE_DAYS = 7  # 요약 카드 "최근 7일 학습" 기준
DIFFICULTY_ORDER = {"초급": 0, "중급": 1, "고급": 2}


def _iso(value):
    return value.isoformat(timespec="seconds") + "Z" if value else None


def _student_status(enrolled_count, completed, total, last_activity, first_enrolled_at, now):
    """완료 / 정체 / 진행중 / 미시작"""
    if enrolled_count == 0:
        return "미시작"
    if total and completed >= total:
        return "완료"
    # 활동이 없으면 수강 시작일을 기준으로 정체 여부 판단
    reference = last_activity or first_enrolled_at
    if reference and now - reference > timedelta(days=STALL_DAYS):
        return "정체"
    if completed == 0:
        return "미시작"
    return "진행중"


@bp.get("/progress")
def progress_overview():
    admin, error = _require_admin()
    if error:
        return error

    now = datetime.utcnow()
    courses = sorted(
        Course.query.filter(Course.slug.isnot(None)).all(),
        key=lambda c: (DIFFICULTY_ORDER.get(c.difficulty, 9), c.id),
    )
    course_by_id = {c.id: c for c in courses}
    students = User.query.filter_by(role="student").order_by(User.name, User.id).all()
    ids = [s.id for s in students]

    enrollments = Enrollment.query.filter(Enrollment.user_id.in_(ids)).all() if ids else []
    progress_rows = (
        TaskProgress.query.filter(TaskProgress.user_id.in_(ids), TaskProgress.task_key.in_(TASK_KEYS)).all()
        if ids
        else []
    )
    points = dict(
        db.session.query(PointLedger.user_id, func.sum(PointLedger.amount))
        .filter(PointLedger.user_id.in_(ids))
        .group_by(PointLedger.user_id)
        .all()
    ) if ids else {}
    attendance = dict(
        db.session.query(PointLedger.user_id, func.count(PointLedger.id))
        .filter(PointLedger.user_id.in_(ids), PointLedger.source == "attendance")
        .group_by(PointLedger.user_id)
        .all()
    ) if ids else {}
    last_point = dict(
        db.session.query(PointLedger.user_id, func.max(PointLedger.created_at))
        .filter(PointLedger.user_id.in_(ids))
        .group_by(PointLedger.user_id)
        .all()
    ) if ids else {}

    # (user_id, course_id) → {task_key: completed_at}
    done = defaultdict(dict)
    last_task = {}
    for row in progress_rows:
        done[(row.user_id, row.course_id)][row.task_key] = row.completed_at
        if row.completed_at and (row.user_id not in last_task or row.completed_at > last_task[row.user_id]):
            last_task[row.user_id] = row.completed_at

    enrolled_by_user = defaultdict(list)
    for e in enrollments:
        if e.course_id in course_by_id:
            enrolled_by_user[e.user_id].append(e)

    student_list = []
    course_acc = {c.id: {"enrolled": 0, "percentSum": 0, "completed": 0} for c in courses}
    funnel = {key: 0 for key in TASK_KEYS}
    funnel_total = 0
    active_count = 0

    for s in students:
        user_enrollments = enrolled_by_user.get(s.id, [])
        per_course = {}
        completed_sum = 0
        for e in user_enrollments:
            course = course_by_id[e.course_id]
            steps = done.get((s.id, course.id), {})
            completed = sum(1 for key in TASK_KEYS if key in steps)
            percent = round(completed / TASK_TOTAL * 100)
            completed_sum += completed
            per_course[course.slug] = {
                "completed": completed,
                "total": TASK_TOTAL,
                "percent": percent,
                "steps": {key: _iso(steps.get(key)) for key in TASK_KEYS},
                "enrolledAt": _iso(e.created_at),
            }
            acc = course_acc[course.id]
            acc["enrolled"] += 1
            acc["percentSum"] += percent
            acc["completed"] += 1 if completed == TASK_TOTAL else 0
            funnel_total += 1
            for key in TASK_KEYS:
                if key in steps:
                    funnel[key] += 1

        total_steps = len(user_enrollments) * TASK_TOTAL
        overall = round(completed_sum / total_steps * 100) if total_steps else 0
        candidates = [v for v in (last_task.get(s.id), last_point.get(s.id)) if v]
        last_activity = max(candidates) if candidates else None
        first_enrolled = min((e.created_at for e in user_enrollments if e.created_at), default=None)
        if last_activity and now - last_activity <= timedelta(days=ACTIVE_DAYS):
            active_count += 1

        student_list.append({
            "id": s.id,
            "username": s.username,
            "name": s.name,
            "email": s.email,
            "courseCount": len(user_enrollments),
            "completedSteps": completed_sum,
            "totalSteps": total_steps,
            "percent": overall,
            "lastActivity": _iso(last_activity),
            "points": int(points.get(s.id, 0) or 0),
            "attendanceDays": int(attendance.get(s.id, 0) or 0),
            "status": _student_status(len(user_enrollments), completed_sum, total_steps, last_activity, first_enrolled, now),
            "courses": per_course,
        })

    enrolled_students = [x for x in student_list if x["courseCount"]]
    summary = {
        "totalStudents": len(student_list),
        "avgPercent": round(sum(x["percent"] for x in enrolled_students) / len(enrolled_students)) if enrolled_students else 0,
        "activeLast7": active_count,
        "stalled": sum(1 for x in student_list if x["status"] == "정체"),
        "stallDays": STALL_DAYS,
    }
    course_stats = [
        {
            "slug": c.slug,
            "title": c.title,
            "difficulty": c.difficulty,
            "icon": c.icon,
            "enrolled": course_acc[c.id]["enrolled"],
            "avgPercent": round(course_acc[c.id]["percentSum"] / course_acc[c.id]["enrolled"]) if course_acc[c.id]["enrolled"] else 0,
            "completedCount": course_acc[c.id]["completed"],
        }
        for c in courses
    ]
    funnel_list = [
        {"key": key, "count": funnel[key], "percent": round(funnel[key] / funnel_total * 100) if funnel_total else 0}
        for key in TASK_KEYS
    ]
    return jsonify(
        summary=summary,
        courses=course_stats,
        funnel={"total": funnel_total, "steps": funnel_list},
        students=student_list,
    )


# ── 학생 개인 현황 (학생 전용 페이지) ─────────────────────────────

WEEKS_IN_TREND = 8
RECENT_LIMIT = 10
SOURCE_LABELS = {
    "attendance": "출석",
    "practice": "실습",
    "practice_low": "실습(하)",
    "practice_medium": "실습(중)",
    "practice_high": "실습(상)",
    "practice_impossible": "실습(안전)",
    "mission": "미션",
    "hint": "힌트",
}
STEP_EVENT_LABELS = {"concept": "개념 학습 완료", "practice": "실습 성공", "defense": "퀴즈 통과"}


def _to_kst(value):
    # DB 시각은 UTC(naive) 기준 → 한국 시간으로 변환
    from zoneinfo import ZoneInfo

    return value.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Seoul"))


@bp.get("/students/<int:user_id>")
def student_detail(user_id):
    admin, error = _require_admin()
    if error:
        return error
    target, error = _load_student(user_id)
    if error:
        return error

    from .attendance import BOARD_DAYS, _board_state
    from .rewards import compute_level, points_balance, total_xp

    now = datetime.utcnow()
    courses = sorted(
        Course.query.filter(Course.slug.isnot(None)).all(),
        key=lambda c: (DIFFICULTY_ORDER.get(c.difficulty, 9), c.id),
    )
    enrollments = {e.course_id: e for e in Enrollment.query.filter_by(user_id=target.id).all()}
    progress_rows = TaskProgress.query.filter(
        TaskProgress.user_id == target.id, TaskProgress.task_key.in_(TASK_KEYS)
    ).all()
    point_rows = PointLedger.query.filter_by(user_id=target.id).all()
    xp_rows = XpLedger.query.filter_by(user_id=target.id).all()
    pending_rewards = Reward.query.filter_by(user_id=target.id, claimed_at=None).count()

    done = defaultdict(dict)
    for row in progress_rows:
        done[row.course_id][row.task_key] = row.completed_at

    # 과목별 진도 (미수강 과목 포함, 난이도순)
    course_list = []
    step_totals = {key: 0 for key in TASK_KEYS}
    completed_steps = 0
    completed_courses = 0
    for c in courses:
        e = enrollments.get(c.id)
        steps = done.get(c.id, {}) if e else {}
        completed = sum(1 for key in TASK_KEYS if key in steps)
        if e:
            completed_steps += completed
            completed_courses += 1 if completed == TASK_TOTAL else 0
            for key in TASK_KEYS:
                if key in steps:
                    step_totals[key] += 1
        course_list.append({
            "slug": c.slug,
            "title": c.title,
            "difficulty": c.difficulty,
            "icon": c.icon,
            "enrolled": bool(e),
            "enrolledAt": _iso(e.created_at) if e else None,
            "completed": completed,
            "total": TASK_TOTAL,
            "percent": round(completed / TASK_TOTAL * 100),
            "steps": {key: _iso(steps.get(key)) for key in TASK_KEYS},
        })

    enrolled_count = len(enrollments)
    total_steps = enrolled_count * TASK_TOTAL
    percent = round(completed_steps / total_steps * 100) if total_steps else 0

    # 활동 시각 모음 → 마지막 활동 · 학습한 날 · 주간 추이
    activity_times = [r.completed_at for r in progress_rows if r.completed_at]
    activity_times += [r.created_at for r in point_rows if r.created_at]
    activity_times += [r.created_at for r in xp_rows if r.created_at]
    last_activity = max(activity_times) if activity_times else None
    learning_days = len({_to_kst(t).date() for t in activity_times})

    today_kst = _to_kst(now).date()
    this_monday = today_kst - timedelta(days=today_kst.weekday())
    week_starts = [this_monday - timedelta(weeks=i) for i in range(WEEKS_IN_TREND - 1, -1, -1)]
    week_counts = {w: 0 for w in week_starts}
    for r in progress_rows:
        if not r.completed_at:
            continue
        d = _to_kst(r.completed_at).date()
        monday = d - timedelta(days=d.weekday())
        if monday in week_counts:
            week_counts[monday] += 1
    weekly = [{"weekStart": w.isoformat(), "count": week_counts[w]} for w in week_starts]

    # 포인트 · 경험치 획득 경로 (적립분만 합산)
    def by_source(rows):
        acc = defaultdict(int)
        for r in rows:
            if r.amount > 0:
                acc[r.source] += r.amount
        return [
            {"source": s, "label": SOURCE_LABELS.get(s, s), "amount": a}
            for s, a in sorted(acc.items(), key=lambda kv: -kv[1])
        ]

    # 최근 활동 (단계 완료 + 포인트·경험치 적립)
    course_title = {c.id: c.title for c in courses}
    events = [
        {"at": r.completed_at, "type": "step",
         "text": f"{course_title.get(r.course_id, '과목')} {STEP_EVENT_LABELS[r.task_key]}"}
        for r in progress_rows if r.completed_at
    ]
    events += [
        {"at": r.created_at, "type": "point",
         "text": f"{r.reason or SOURCE_LABELS.get(r.source, r.source)} {'+' if r.amount >= 0 else ''}{r.amount}P"}
        for r in point_rows if r.created_at
    ]
    events += [
        {"at": r.created_at, "type": "xp",
         "text": f"{r.reason or SOURCE_LABELS.get(r.source, r.source)} +{r.amount}XP"}
        for r in xp_rows if r.created_at
    ]
    events.sort(key=lambda ev: ev["at"], reverse=True)
    recent = [{**ev, "at": _iso(ev["at"])} for ev in events[:RECENT_LIMIT]]

    first_enrolled = min((e.created_at for e in enrollments.values() if e.created_at), default=None)
    board = _board_state(target.id)
    level = compute_level(total_xp(target.id))

    return jsonify(
        profile={
            "id": target.id,
            "username": target.username,
            "name": target.name,
            "nickname": target.nickname,
            "email": target.email,
            "phone": target.phone,
            "createdAt": _iso(target.created_at),
            "status": _student_status(enrolled_count, completed_steps, total_steps, last_activity, first_enrolled, now),
            "stallDays": STALL_DAYS,
        },
        summary={
            "percent": percent,
            "completedSteps": completed_steps,
            "totalSteps": total_steps,
            "points": points_balance(target.id),
            "pendingRewards": pending_rewards,
            "attendanceDays": board["completed"],
            "attendanceBoardDays": BOARD_DAYS,
            "completedCourses": completed_courses,
            "enrolledCourses": enrolled_count,
            "totalCourses": len(courses),
            "level": level["level"],
            "currentXp": level["currentXp"],
            "xpForNextLevel": level["xpForNextLevel"],
            "totalXp": level["totalXp"],
            "practiceSuccess": step_totals["practice"],
            "quizPassed": step_totals["defense"],
            "learningDays": learning_days,
            "lastActivity": _iso(last_activity),
        },
        courses=course_list,
        stepTotals={"enrolled": enrolled_count, **step_totals},
        attendance=board["days"],
        weekly=weekly,
        pointsBySource=by_source(point_rows),
        xpBySource=by_source(xp_rows),
        recent=recent,
    )
