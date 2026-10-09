import hashlib
import hmac
import re
import smtplib
from datetime import datetime, timedelta

import bcrypt
import requests
from flask import Blueprint, current_app, jsonify, request, session
from flask_wtf.csrf import generate_csrf
from sqlalchemy.exc import IntegrityError

from . import db, limiter
from .audit import record_audit, record_login_failure
from .mailer import send_verification_email
from .models import User, VerificationCode
from .sms import send_verification_sms
from .utils import generate_numeric_code

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

CODE_TTL_MINUTES = 5
MAX_ATTEMPTS = 5
GENERIC_SEND_MESSAGE = "입력하신 정보가 유효하면 인증코드를 발송했습니다."

# 회원가입 입력 규칙 (프론트 SignupView 안내 문구와 같은 값)
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{4,20}$")          # 영문·숫자·밑줄 4~20자
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")      # 형식만 확인 (실제 존재 여부는 X)
PHONE_RE = re.compile(r"^01[0-9]{8,9}$")                    # 숫자만, 01로 시작 10~11자리
PASSWORD_MIN, PASSWORD_MAX = 8, 64                          # bcrypt는 72바이트까지만 사용
NAME_MAX = 30


def _hash_code(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _normalize_phone(phone):
    return re.sub(r"\D", "", phone or "")


def _issue_code(user, target, purpose):
    code = generate_numeric_code()
    record = VerificationCode(
        user_id=user.id,
        target=target,
        purpose=purpose,
        code_hash=_hash_code(code),
        expires_at=datetime.utcnow() + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.session.add(record)
    db.session.commit()
    return code, record


def _latest_active_code(user_id, purpose):
    return (
        VerificationCode.query.filter_by(user_id=user_id, purpose=purpose, verified=False)
        .order_by(VerificationCode.id.desc())
        .first()
    )


def _latest_verified_code(user_id, purpose):
    return (
        VerificationCode.query.filter_by(user_id=user_id, purpose=purpose, verified=True)
        .order_by(VerificationCode.id.desc())
        .first()
    )


def _code_valid_and_matches(record, submitted_code):
    if record is None:
        return False
    if record.attempts >= MAX_ATTEMPTS:
        return False
    if record.expires_at < datetime.utcnow():
        return False
    return hmac.compare_digest(record.code_hash, _hash_code(submitted_code))


def _try_send_email(*args, **kwargs):
    try:
        send_verification_email(*args, **kwargs)
    except (smtplib.SMTPException, OSError) as exc:
        current_app.logger.warning("email send failed: %s", type(exc).__name__)


def _try_send_sms(*args, **kwargs):
    try:
        send_verification_sms(*args, **kwargs)
    except requests.RequestException as exc:
        current_app.logger.warning("sms send failed: %s", type(exc).__name__)


# 없는 아이디 로그인 시 비교용 더미 해시 (실제 계정과 같은 cost 12)
_DUMMY_HASH = bcrypt.hashpw(b"secuquest-dummy-password", bcrypt.gensalt(rounds=12))


@bp.get("/csrf")
def csrf_token():
    return jsonify(csrf_token=generate_csrf())


@bp.post("/login")
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", ""))
    password = str(payload.get("password", ""))
    role = str(payload.get("role", ""))

    user = User.query.filter_by(username=username).first()
    if not user:
        # 없는 아이디도 bcrypt 비교를 한 번 해서 응답 시간을 맞춤 (시간 차이로 가입 여부를 알아내는 것 방지)
        bcrypt.checkpw(password.encode("utf-8"), _DUMMY_HASH)
        record_login_failure(username, None, "unknown_user")
        return jsonify(message="아이디 또는 비밀번호가 올바르지 않습니다."), 401
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        record_login_failure(username, user, "wrong_password")
        return jsonify(message="아이디 또는 비밀번호가 올바르지 않습니다."), 401
    if user.role != role:
        record_login_failure(username, user, "role_mismatch")
        return jsonify(message="선택한 역할이 계정과 일치하지 않습니다."), 401

    session.clear()
    session["user_id"] = user.id
    session["role"] = user.role
    current_app.session_interface.regenerate(session)
    return jsonify(id=user.id, username=user.username, name=user.name, role=user.role, email=user.email)


def _validate_signup(username, password, name, email, phone):
    """회원가입 입력 검증: 문제가 있으면 안내 문구, 없으면 None"""
    if not USERNAME_RE.match(username):
        return "아이디는 영문·숫자·밑줄(_) 4~20자로 입력하세요."
    if not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        return f"비밀번호는 {PASSWORD_MIN}~{PASSWORD_MAX}자로 입력하세요."
    if not (re.search(r"[A-Za-z]", password) and re.search(r"[0-9]", password)):
        return "비밀번호에는 영문과 숫자가 모두 들어가야 합니다."
    if password.lower() == username.lower():
        return "비밀번호는 아이디와 같을 수 없습니다."
    if not name or len(name) > NAME_MAX:
        return f"이름은 1~{NAME_MAX}자로 입력하세요."
    if len(email) > 120 or not EMAIL_RE.match(email):
        return "이메일 형식이 올바르지 않습니다."
    if not PHONE_RE.match(phone):
        return "휴대폰 번호는 숫자 10~11자리(예: 01012345678)로 입력하세요."
    return None


@bp.post("/signup")
@limiter.limit("5 per minute")
def signup():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    phone = _normalize_phone(str(payload.get("phone", "")))

    error = _validate_signup(username, password, name, email, phone)
    if error:
        return jsonify(message=error), 400

    if User.query.filter_by(username=username).first():
        return jsonify(message="이미 사용 중인 아이디입니다."), 409
    if User.query.filter_by(email=email).first():
        return jsonify(message="이미 가입된 이메일입니다."), 409

    user = User(
        username=username,
        password_hash=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8"),
        role="student",  # 역할은 서버가 고정: 요청에 role이 와도 무시 (관리자 셀프 가입 차단)
        name=name,
        email=email,
        phone=phone,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # 위 중복 확인과 저장 사이에 같은 값이 먼저 저장된 경우 (동시 가입)
        db.session.rollback()
        return jsonify(message="이미 사용 중인 아이디 또는 이메일입니다."), 409

    current_app.logger.info("signup user_id=%s", user.id)
    return jsonify(message=f"{username} 님, 회원가입이 완료되었습니다. 로그인해 주세요."), 201


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="로그아웃되었습니다.")


@bp.get("/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(message="로그인이 필요합니다."), 401
    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return jsonify(message="로그인이 필요합니다."), 401
    return jsonify(id=user.id, username=user.username, name=user.name, role=user.role, email=user.email)


@bp.post("/find-id/send-code")
@limiter.limit("5 per minute")
def find_id_send_code():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()

    user = User.query.filter_by(email=email).first()
    if user:
        code, _ = _issue_code(user, email, "find_id")
        _try_send_email(email, "[SecuQuest] 아이디 찾기 인증코드", f"인증코드: {code} (5분 이내 입력)")
    return jsonify(message=GENERIC_SEND_MESSAGE)


@bp.post("/find-id/verify")
@limiter.limit("10 per minute")
def find_id_verify():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    code = payload.get("code", "")

    user = User.query.filter_by(email=email).first()
    record = _latest_active_code(user.id, "find_id") if user else None
    if record and record.target != email:  # 가장 최근 코드가 휴대폰용이면 이메일 코드로 인정하지 않음
        record = None
    if not _code_valid_and_matches(record, code):
        if record:
            record.attempts += 1
            db.session.commit()
        return jsonify(message="인증코드가 올바르지 않거나 만료되었습니다."), 400
    record.verified = True
    db.session.commit()
    return jsonify(username=user.username)



@bp.post("/find-id/send-sms-code")
@limiter.limit("5 per minute")
def find_id_send_sms_code():
    """휴대폰으로 아이디 찾기: 이름 + 휴대폰 번호가 맞는 계정이 있으면 SMS 인증코드 발송"""
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    phone = _normalize_phone(str(payload.get("phone", "")))

    user = User.query.filter_by(name=name, phone=phone).order_by(User.id).first() if name and phone else None
    if user:
        code, _ = _issue_code(user, phone, "find_id")  # 목적은 find_id, target(번호)로 이메일 방식과 구분
        _try_send_sms(phone, f"[SecuQuest] 아이디 찾기 인증코드 {code} (5분 이내 입력)")
    # 계정이 없어도 같은 문구 (가입 여부를 알려주지 않음)
    return jsonify(message=GENERIC_SEND_MESSAGE)


@bp.post("/find-id/verify-sms")
@limiter.limit("10 per minute")
def find_id_verify_sms():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    phone = _normalize_phone(str(payload.get("phone", "")))
    code = str(payload.get("code", ""))

    users = User.query.filter_by(name=name, phone=phone).order_by(User.id).all() if name and phone else []
    record = _latest_active_code(users[0].id, "find_id") if users else None
    if record and record.target != phone:
        record = None
    if not _code_valid_and_matches(record, code):
        if record:
            record.attempts += 1
            db.session.commit()
        return jsonify(message="인증코드가 올바르지 않거나 만료되었습니다."), 400
    record.verified = True
    db.session.commit()
    # 같은 이름·번호로 가입한 계정이 여러 개일 수 있어 모두 알려줌
    return jsonify(username=users[0].username, usernames=[u.username for u in users])

@bp.post("/reset-password/send-email-code")
@limiter.limit("5 per minute")
def reset_password_send_email_code():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    email = str(payload.get("email", "")).strip().lower()

    user = User.query.filter_by(username=username, email=email).first()
    if user:
        code, _ = _issue_code(user, email, "reset_password_email")
        _try_send_email(email, "[SecuQuest] 비밀번호 재설정 인증코드", f"인증코드: {code} (5분 이내 입력)")
    return jsonify(message=GENERIC_SEND_MESSAGE)


@bp.post("/reset-password/send-sms-code")
@limiter.limit("5 per minute")
def reset_password_send_sms_code():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    phone = _normalize_phone(payload.get("phone", ""))

    user = User.query.filter_by(username=username, phone=phone).first()
    if user:
        code, _ = _issue_code(user, phone, "reset_password_sms")
        _try_send_sms(phone, f"[SecuQuest] 인증코드 {code} (5분 이내 입력)")
    return jsonify(message=GENERIC_SEND_MESSAGE)


# 비밀번호 찾기: 아이디 찾기와 같은 방식으로 이메일 또는 휴대폰(SMS) 중 하나를 골라 인증
RESET_PURPOSES = {"email": "reset_password_email", "sms": "reset_password_sms"}


def _password_policy_error(password, username):
    """회원가입과 같은 비밀번호 규칙"""
    if not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        return f"비밀번호는 {PASSWORD_MIN}~{PASSWORD_MAX}자로 입력하세요."
    if not (re.search(r"[A-Za-z]", password) and re.search(r"[0-9]", password)):
        return "비밀번호에는 영문과 숫자가 모두 들어가야 합니다."
    if password.lower() == username.lower():
        return "비밀번호는 아이디와 같을 수 없습니다."
    return None


@bp.post("/reset-password/verify-code")
@limiter.limit("10 per minute")
def reset_password_verify_code():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    method = str(payload.get("method", ""))
    code = str(payload.get("code", ""))
    purpose = RESET_PURPOSES.get(method)

    user = User.query.filter_by(username=username).first() if purpose else None
    record = _latest_active_code(user.id, purpose) if user else None
    if not _code_valid_and_matches(record, code):
        if record:
            record.attempts += 1
            db.session.commit()
        return jsonify(message="인증코드가 올바르지 않거나 만료되었습니다."), 400

    record.verified = True
    # 인증한 사람·방식을 세션에 기록 → 다음 단계(confirm)에서 같은 브라우저인지 확인
    session["reset_user_id"] = user.id
    session["reset_purpose"] = purpose
    db.session.commit()
    return jsonify(message="인증이 완료되었습니다. 새 비밀번호를 설정하세요.")


@bp.post("/reset-password/confirm")
@limiter.limit("10 per minute")
def reset_password_confirm():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    new_password = str(payload.get("new_password", ""))

    error = _password_policy_error(new_password, username)
    if error:
        return jsonify(message=error), 400

    user = User.query.filter_by(username=username).first()
    purpose = session.get("reset_purpose")
    if not user or session.get("reset_user_id") != user.id or purpose not in RESET_PURPOSES.values():
        return jsonify(message="인증을 먼저 완료하세요."), 400

    record = _latest_verified_code(user.id, purpose)
    if record is None or record.expires_at < datetime.utcnow():
        return jsonify(message="인증 시간이 지났습니다. 인증코드를 다시 받아 주세요."), 400

    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    db.session.delete(record)  # 한 번 쓴 인증은 삭제 → 같은 인증으로 두 번 변경 불가
    session.pop("reset_user_id", None)
    session.pop("reset_purpose", None)
    record_audit(user, "reset_password_self", detail="via=" + ("sms" if purpose.endswith("sms") else "email"))
    db.session.commit()
    return jsonify(message="비밀번호가 변경되었습니다.")
