import hashlib
import hmac
import re
import smtplib
from datetime import datetime, timedelta

import bcrypt
import requests
from flask import Blueprint, current_app, jsonify, request, session
from flask_wtf.csrf import generate_csrf

from . import db, limiter
from .mailer import send_verification_email
from .models import User, VerificationCode
from .sms import send_verification_sms
from .utils import generate_numeric_code

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

CODE_TTL_MINUTES = 5
MAX_ATTEMPTS = 5
GENERIC_SEND_MESSAGE = "입력하신 정보가 유효하면 인증코드를 발송했습니다."


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


@bp.get("/csrf")
def csrf_token():
    return jsonify(csrf_token=generate_csrf())


@bp.post("/login")
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    password = payload.get("password", "")
    role = payload.get("role", "")

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify(message="아이디 또는 비밀번호가 올바르지 않습니다."), 401
    if user.role != role:
        return jsonify(message="선택한 역할이 계정과 일치하지 않습니다."), 401

    session.clear()
    session["user_id"] = user.id
    session["role"] = user.role
    current_app.session_interface.regenerate(session)
    return jsonify(id=user.id, username=user.username, name=user.name, role=user.role, email=user.email)


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
    email = payload.get("email", "")

    user = User.query.filter_by(email=email).first()
    if user:
        code, _ = _issue_code(user, email, "find_id")
        _try_send_email(email, "[SecuQuest] 아이디 찾기 인증코드", f"인증코드: {code} (5분 이내 입력)")
    return jsonify(message=GENERIC_SEND_MESSAGE)


@bp.post("/find-id/verify")
@limiter.limit("10 per minute")
def find_id_verify():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    code = payload.get("code", "")

    user = User.query.filter_by(email=email).first()
    record = _latest_active_code(user.id, "find_id") if user else None
    if not _code_valid_and_matches(record, code):
        if record:
            record.attempts += 1
            db.session.commit()
        return jsonify(message="인증코드가 올바르지 않거나 만료되었습니다."), 400
    record.verified = True
    db.session.commit()
    return jsonify(username=user.username)


@bp.post("/reset-password/send-email-code")
@limiter.limit("5 per minute")
def reset_password_send_email_code():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    email = payload.get("email", "")

    user = User.query.filter_by(username=username, email=email).first()
    if user:
        code, _ = _issue_code(user, email, "reset_password_email")
        _try_send_email(email, "[SecuQuest] 비밀번호 재설정 인증코드", f"인증코드: {code} (5분 이내 입력)")
    return jsonify(message=GENERIC_SEND_MESSAGE)


@bp.post("/reset-password/send-sms-code")
@limiter.limit("5 per minute")
def reset_password_send_sms_code():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    phone = _normalize_phone(payload.get("phone", ""))

    user = User.query.filter_by(username=username, phone=phone).first()
    if user:
        code, _ = _issue_code(user, phone, "reset_password_sms")
        _try_send_sms(phone, f"[SecuQuest] 인증코드 {code} (5분 이내 입력)")
    return jsonify(message=GENERIC_SEND_MESSAGE)


@bp.post("/reset-password/verify-codes")
@limiter.limit("10 per minute")
def reset_password_verify_codes():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    email_code = payload.get("email_code", "")
    sms_code = payload.get("sms_code", "")

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(message="인증코드가 올바르지 않거나 만료되었습니다."), 400

    email_record = _latest_active_code(user.id, "reset_password_email")
    sms_record = _latest_active_code(user.id, "reset_password_sms")
    email_ok = _code_valid_and_matches(email_record, email_code)
    sms_ok = _code_valid_and_matches(sms_record, sms_code)

    if not email_ok and email_record:
        email_record.attempts += 1
    if not sms_ok and sms_record:
        sms_record.attempts += 1

    if email_ok and sms_ok:
        email_record.verified = True
        sms_record.verified = True
        session["reset_user_id"] = user.id
    db.session.commit()

    if not (email_ok and sms_ok):
        return jsonify(message="인증코드가 올바르지 않거나 만료되었습니다."), 400
    return jsonify(message="인증이 완료되었습니다. 새 비밀번호를 설정하세요.")


@bp.post("/reset-password/confirm")
@limiter.limit("10 per minute")
def reset_password_confirm():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    new_password = payload.get("new_password", "")

    if len(new_password) < 8:
        return jsonify(message="비밀번호는 8자 이상이어야 합니다."), 400

    user = User.query.filter_by(username=username).first()
    if not user or session.get("reset_user_id") != user.id:
        return jsonify(message="이메일·휴대폰 인증을 먼저 완료하세요."), 400

    email_record = _latest_verified_code(user.id, "reset_password_email")
    sms_record = _latest_verified_code(user.id, "reset_password_sms")
    both_verified = (
        email_record is not None
        and sms_record is not None
        and email_record.expires_at >= datetime.utcnow()
        and sms_record.expires_at >= datetime.utcnow()
    )
    if not both_verified:
        return jsonify(message="이메일·휴대폰 인증을 먼저 완료하세요."), 400

    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.session.delete(email_record)
    db.session.delete(sms_record)
    session.pop("reset_user_id", None)
    db.session.commit()
    return jsonify(message="비밀번호가 변경되었습니다.")
