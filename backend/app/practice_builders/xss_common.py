"""XSS 3종(reflected/dom/stored) 공통 로직.

판정 방식: CI가 "서버가 심은 flag 파일을 stdout으로 읽어내면 성공"이었다면,
XSS는 "브라우저에서 스크립트가 실제로 실행되면 성공"이다.

1. render: 서버가 시도마다 랜덤 flag를 세션에 저장하고, 취약 페이지 HTML 안에
   alert/confirm/prompt를 가로채는 감시 스크립트로 심어서 돌려준다.
2. 프런트는 이 HTML을 <iframe sandbox="allow-scripts">(opaque origin)에 넣는다.
3. 주입한 스크립트가 alert()을 호출하면 감시 스크립트가 flag를 부모 창에 postMessage.
4. verify: 프런트가 받은 flag를 제출 → 세션 값과 같으면 성공.
"""
import html
import json
import secrets

from flask import session

from .base import PracticeBuilder, PracticeResult

MAX_PAYLOAD_LEN = 200
DIFFICULTIES = ("low", "medium", "high", "impossible")

# 페이지 공통 스타일 — iframe 내부(격리된 별도 문서)라 앱의 디자인 토큰을 읽을 수 없어
# 최소한의 중립 스타일만 둔다.
_PAGE_STYLE = (
    "body{font-family:sans-serif;font-size:14px;margin:16px;line-height:1.6}"
    ".bar{padding:6px 10px;border:1px solid #ccc;background:#f5f5f5;font-family:monospace;margin-bottom:12px}"
    ".post{border-bottom:1px solid #ddd;padding:6px 0}"
)

_WATCHER = (
    "<script>(function(){{var t={token};"
    "function hit(){{try{{parent.postMessage({{type:'sq-xss',flag:t}},'*');}}catch(e){{}}}}"
    "window.alert=hit;window.confirm=hit;window.prompt=hit;}})();</script>"
)


def js_string(value):
    """서버→페이지 JS로 값을 안전하게 넘길 때 사용(</script> 탈출 방지)."""
    return json.dumps(value).replace("<", "\\u003c").replace(">", "\\u003e")


class XssBuilderBase(PracticeBuilder):
    slug = ""
    difficulties = DIFFICULTIES
    actions = ("render", "verify")
    _hints = {}

    # ---- 하위 클래스 구현 ----
    def build_body(self, difficulty, payload):
        raise NotImplementedError

    # ---- 공통 ----
    def _flag_key(self, difficulty):
        return f"xss_flag:{self.slug}:{difficulty}"

    def validate_input(self, difficulty, user_input):
        if difficulty not in self.difficulties:
            return "지원하지 않는 난이도입니다."
        if not isinstance(user_input, dict):
            return "잘못된 요청입니다."
        action = user_input.get("action")
        if action not in self.actions:
            return "지원하지 않는 동작입니다."
        payload = user_input.get("payload", "")
        if not isinstance(payload, str) or len(payload) > MAX_PAYLOAD_LEN:
            return f"입력값은 {MAX_PAYLOAD_LEN}자 이내 문자열이어야 합니다."
        if action == "post" and not payload.strip():
            return "내용을 입력하세요."
        if action == "verify" and not isinstance(user_input.get("flag"), str):
            return "flag 값이 없습니다."
        return None

    def hints(self, difficulty):
        return list(self._hints.get(difficulty, []))

    def run(self, difficulty, user_input):
        action = user_input["action"]
        if action == "verify":
            return self._verify(difficulty, user_input["flag"])
        return self.handle(difficulty, action, user_input.get("payload", ""))

    def handle(self, difficulty, action, payload):
        """render 외 동작(post/reset)이 필요한 모듈은 오버라이드"""
        return self.render_page(difficulty, payload)

    def render_page(self, difficulty, payload):
        token = secrets.token_hex(16)
        if difficulty == "impossible":
            # 안전 단계는 flag를 세션에 저장하지 않는다 — 어떤 값을 제출해도 실패
            session.pop(self._flag_key(difficulty), None)
        else:
            session[self._flag_key(difficulty)] = token
        page = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{_PAGE_STYLE}</style>{_WATCHER.format(token=js_string(token))}</head>"
            f"<body>{self.build_body(difficulty, payload)}</body></html>"
        )
        return PracticeResult(output=page, success=False)

    def _verify(self, difficulty, flag):
        expected = session.pop(self._flag_key(difficulty), None)
        success = bool(expected) and secrets.compare_digest(expected, flag)
        if success:
            output = "스크립트 실행이 확인되었습니다. XSS 성공!"
        elif difficulty == "impossible":
            output = "안전 단계는 출력 인코딩으로 스크립트가 실행되지 않습니다."
        else:
            output = "flag가 일치하지 않습니다. 페이지를 다시 불러와 시도하세요."
        return PracticeResult(output=output, success=success)


def escape(value):
    return html.escape(value, quote=True)
