"""감사 로그 공통 기록 함수

- 모든 [AUDIT] 기록은 이 함수 하나로 남긴다 (관리자 · 마이페이지 · 비밀번호 재설정)
- DB(audit_logs)에 저장 + 서버 로그에도 같은 내용 출력
- 호출한 쪽의 변경 작업과 **같은 트랜잭션**에 넣는다 → 변경만 되고 기록이 빠지는 일 방지
  (record_audit 는 session.add 만 하고, commit 은 호출한 쪽에서 한 번에)
- 개인정보 값(이메일 · 번호 · 비밀번호)은 detail 에 넣지 않는다
"""
from flask import current_app, request

from . import db
from .models import AuditLog

# 화면에 보여줄 동작 이름 (관리자 감사 로그 탭)
ACTION_LABELS = {
    "reset_password": "임시 비밀번호 발급",
    "delete_user": "회원 삭제",
    "change_own_password": "관리자 비밀번호 변경",
    "update_account": "회원정보 변경",
    "change_password": "비밀번호 변경",
    "reset_password_self": "비밀번호 찾기로 재설정",
    "login_failed": "로그인 실패",
}

# 로그인 실패 사유 (관리자만 보는 기록이므로 구체적으로 남김. 화면 응답은 구분하지 않음)
LOGIN_FAIL_REASONS = ("unknown_user", "wrong_password", "role_mismatch")
ATTEMPT_USERNAME_MAX = 30  # 입력한 아이디는 이 길이까지만 저장 (아이디 칸에 비밀번호를 잘못 넣은 경우 노출 최소화)


def _client_ip():
    # Nginx 가 X-Forwarded-For 를 넘기지 않는 구성이라 remote_addr 사용 (요청 헤더 위조 방지)
    return request.remote_addr


def record_audit(actor, action, target=None, detail=""):
    """감사 기록 1건을 세션에 추가 (commit 은 호출한 쪽에서)"""
    entry = AuditLog(
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else None,
        actor_role=actor.role if actor else None,
        action=action,
        target_id=target.id if target else None,
        target_username=target.username if target else None,
        detail=(detail or None) and detail[:255],
        ip=_client_ip(),
    )
    db.session.add(entry)
    current_app.logger.warning(
        "[AUDIT] actor_id=%s action=%s target_user_id=%s%s ip=%s",
        entry.actor_id,
        action,
        entry.target_id if entry.target_id is not None else "-",
        f" {detail}" if detail else "",
        entry.ip,
    )
    return entry


def record_login_failure(attempted_username, user, reason):
    """로그인 실패 1건 기록 (변경 작업이 없으므로 여기서 바로 commit)

    - 행위자: 실제 계정이 있으면 그 계정, 없으면 입력한 아이디만
    - 기록 실패가 로그인 응답을 막지 않도록 예외는 서버 로그로만 남김
    - 대량 시도는 로그인 Rate Limit(분당 10회/IP)이 먼저 막으므로 기록 폭증도 제한됨
    """
    entry = AuditLog(
        actor_id=user.id if user else None,
        actor_username=(user.username if user else str(attempted_username)[:ATTEMPT_USERNAME_MAX]) or None,
        actor_role=user.role if user else None,
        action="login_failed",
        detail=f"reason={reason}",
        ip=_client_ip(),
    )
    try:
        db.session.add(entry)
        db.session.commit()
    except Exception as exc:  # 기록 실패해도 로그인 응답(401)은 그대로
        db.session.rollback()
        current_app.logger.error("audit write failed: %s", type(exc).__name__)
    current_app.logger.warning(
        "[AUDIT] actor_id=%s action=login_failed reason=%s ip=%s", entry.actor_id, reason, entry.ip
    )
