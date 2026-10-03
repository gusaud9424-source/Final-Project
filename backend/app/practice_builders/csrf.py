"""CSRF — DVWA 재현 (비밀번호 변경).

DVWA vulnerabilities/csrf:
  low        : 토큰·Referer 검사 없음 → 외부 폼으로 바로 비밀번호 변경
  medium     : Referer 헤더에 서버 호스트가 포함되는지 검사(stripos) → Referer 위조로 우회
  high       : Anti-CSRF 토큰 필요 → 토큰 유출(XSS 등) 후 사용
  impossible : 현재 비밀번호 재확인 + 토큰

실제 계정 비밀번호가 아니라 세션에 둔 "연습용 비밀번호"를 대상으로 한다.
'attack' 액션 = 외부 사이트에서 보낸 위조 요청 시뮬레이션. 위조 요청이 레벨의
방어를 뚫고 비밀번호를 바꾸면 성공.
"""
import secrets

from flask import session

_HOST = "localhost"  # 서버 호스트(SERVER_NAME 상당). Referer 검사 기준.


def _pw_key():
    return "csrf_practice_pw"


def _token_key():
    return "csrf_practice_token"


class CsrfBuilder:
    difficulties = ("low", "medium", "high", "impossible")
    actions = ("info", "attack", "leak_token", "reset")

    # PracticeBuilder 인터페이스와 동일한 시그니처 유지
    def _pw(self):
        return session.get(_pw_key(), "password")

    def _token(self):
        tok = session.get(_token_key())
        if not tok:
            tok = secrets.token_hex(8)
            session[_token_key()] = tok
        return tok

    def validate_input(self, difficulty, user_input):
        if difficulty not in self.difficulties:
            return "지원하지 않는 난이도입니다."
        if not isinstance(user_input, dict):
            return "잘못된 요청입니다."
        if user_input.get("action") not in self.actions:
            return "지원하지 않는 동작입니다."
        return None

    def hints(self, difficulty):
        return {
            "low": [
                "토큰도 Referer 검사도 없습니다. 외부 사이트의 폼만으로 비밀번호를 바꿀 수 있습니다.",
                "위조 요청(공격 시뮬레이션)에서 새 비밀번호만 넣고 전송하세요.",
                "예) 외부 폼이 password_new=hacked 를 제출",
            ],
            "medium": [
                "서버가 Referer 헤더에 호스트(localhost)가 들어있는지 검사합니다.",
                "Referer 값을 호스트가 포함되도록 위조하면 통과합니다(DevTools/Burp).",
                "예) Referer: http://localhost:8090/evil",
            ],
            "high": [
                "Anti-CSRF 토큰(user_token)이 필요합니다.",
                "토큰은 보통 XSS 등으로 유출해야 합니다. 여기선 '토큰 유출' 버튼으로 얻은 값을 위조 요청에 넣으세요.",
                "예) user_token=<유출한 토큰>",
            ],
            "impossible": [
                "현재 비밀번호 재확인 + 토큰이 필요합니다.",
                "공격자는 피해자의 현재 비밀번호를 모르므로 위조가 성립하지 않습니다.",
            ],
        }.get(difficulty, [])

    def run(self, difficulty, user_input):
        from .base import PracticeResult

        action = user_input["action"]
        if action == "reset":
            session[_pw_key()] = "password"
            return PracticeResult(output="연습용 비밀번호를 'password'로 초기화했습니다.", success=False)
        if action == "info":
            return PracticeResult(
                output=f"현재 연습용 비밀번호: {self._pw()} · 목표: 외부(위조) 요청으로 비밀번호를 바꾸세요.",
                success=False,
            )
        if action == "leak_token":
            return PracticeResult(output=f"유출된 user_token: {self._token()}", success=False)

        # action == "attack" : 외부 사이트에서 온 위조 요청 시뮬레이션
        new = (user_input.get("password_new") or "").strip()
        conf = (user_input.get("password_conf") or "").strip()
        referer = user_input.get("referer") or ""   # 위조 요청이 보낸 Referer
        token = user_input.get("user_token") or ""
        current = user_input.get("password_current") or ""

        if not new or not conf:
            return PracticeResult(output="새 비밀번호를 입력하세요.", success=False)
        if new != conf:
            return PracticeResult(output="Passwords do not match.", success=False)

        # 레벨별 방어
        if difficulty == "medium":
            if _HOST not in referer:
                return PracticeResult(
                    output=f"That request didn't look to come from here. (Referer 검사 실패: {referer or '없음'})",
                    success=False,
                )
        elif difficulty == "high":
            if not secrets.compare_digest(token, self._token()):
                return PracticeResult(output="CSRF token is incorrect. (토큰 불일치)", success=False)
        elif difficulty == "impossible":
            if current != self._pw():
                return PracticeResult(output="현재 비밀번호가 올바르지 않습니다. (위조 불가)", success=False)
            if not secrets.compare_digest(token, self._token()):
                return PracticeResult(output="CSRF token is incorrect.", success=False)

        # 방어 통과 → 비밀번호 변경됨
        session[_pw_key()] = new
        # 레벨 방어를 외부 위조 요청이 뚫었는지로 성공 판정
        bypassed = difficulty in ("low", "medium", "high")
        msg = f"Password Changed. 연습용 비밀번호가 '{new}' 로 바뀌었습니다."
        if bypassed:
            msg += " — 외부 위조 요청이 통했습니다 (CSRF 성공)."
        return PracticeResult(output=msg, success=bypassed)
