import re

from flask import session

from .xss_common import XssBuilderBase, escape

# DVWA xss_s 재현: 방명록(Guestbook)에 Name + Message 두 입력.
# 레벨별 취약 벡터:
#   low        : message 거의 그대로 → message 로 주입
#   medium     : message 는 strip_tags+htmlspecialchars(안전), name 은 str_replace('<script>') → name 으로 주입
#   high       : message 안전, name 은 preg_replace(/<...s...c...r...i...p...t/i) → name 으로 img 주입
#   impossible : name·message 모두 htmlspecialchars → 불가
MAX_POSTS = 5
_HIGH_RE = re.compile(r"<(.*)s(.*)c(.*)r(.*)i(.*)p(.*)t", re.IGNORECASE)

_HINTS = {
    "low": [
        "방명록 글(Message)이 거의 그대로 저장돼 모든 방문자 화면에서 실행됩니다.",
        "Message 칸에 스크립트를 넣어보세요.",
        "예) Message: <script>alert(1)</script>",
    ],
    "medium": [
        "Message 는 안전하게 처리되지만, Name 은 '<script>' 문자열만 지웁니다.",
        "Name 칸에 script 가 아닌 태그로 주입하세요(이벤트 속성). Name 이 짧으면 요청을 변조해 늘릴 수 있습니다.",
        "예) Name: <img src=x onerror=alert(1)>",
    ],
    "high": [
        "Message 는 안전, Name 은 정규식으로 script 태그류를 제거합니다.",
        "Name 칸에 script 없는 태그(img/svg 등)의 이벤트 속성으로 주입하세요.",
        "예) Name: <img src=x onerror=alert(1)>",
    ],
    "impossible": [
        "Name·Message 모두 출력 시 HTML 인코딩됩니다.",
        "어떤 태그를 넣어도 글자로만 보여 실행되지 않습니다.",
    ],
}


class XssStoredBuilder(XssBuilderBase):
    slug = "xss-stored"
    actions = ("render", "post", "reset", "verify")
    _hints = _HINTS

    def _posts_key(self, difficulty):
        return f"xss_stored_posts:{difficulty}"

    def validate_input(self, difficulty, user_input):
        if difficulty not in self.difficulties:
            return "지원하지 않는 난이도입니다."
        if not isinstance(user_input, dict):
            return "잘못된 요청입니다."
        action = user_input.get("action")
        if action not in self.actions:
            return "지원하지 않는 동작입니다."
        if action == "verify" and not isinstance(user_input.get("flag"), str):
            return "flag 값이 없습니다."
        if action == "post":
            name = user_input.get("name", "")
            message = user_input.get("message", "")
            if not isinstance(name, str) or not isinstance(message, str):
                return "Name/Message 형식이 올바르지 않습니다."
            if not name.strip() or not message.strip():
                return "Name 과 Message 를 모두 입력하세요."
            if len(name) > 200 or len(message) > 200:
                return "입력은 200자 이내로 입력하세요."
        return None

    def hints(self, difficulty):
        return list(_HINTS.get(difficulty, []))

    def _sanitize_name(self, difficulty, name):
        if difficulty == "medium":
            return name.replace("<script>", "")
        if difficulty == "high":
            return _HIGH_RE.sub("", name)
        if difficulty == "impossible":
            return escape(name)
        return name

    def _sanitize_message(self, difficulty, message):
        # DVWA: low 외에는 message 안전 처리(strip_tags + htmlspecialchars)
        if difficulty == "low":
            return message
        no_tags = re.sub(r"<[^>]*>", "", message)  # strip_tags 근사
        return escape(no_tags)

    def run(self, difficulty, user_input):
        action = user_input["action"]
        if action == "verify":
            return self._verify(difficulty, user_input["flag"])
        key = self._posts_key(difficulty)
        posts = list(session.get(key, []))
        if action == "post":
            posts.append(
                {
                    "name": self._sanitize_name(difficulty, user_input.get("name", "")),
                    "message": self._sanitize_message(difficulty, user_input.get("message", "")),
                }
            )
            posts = posts[-MAX_POSTS:]
            session[key] = posts
        elif action == "reset":
            posts = []
            session[key] = posts
        return self.render_page(difficulty, posts)

    def build_body(self, difficulty, posts):
        if posts:
            items = "".join(
                f"<div class='post'><b>Name</b>: {p['name']}<br><b>Message</b>: {p['message']}</div>"
                for p in posts
            )
        else:
            items = "<p>아직 남겨진 글이 없습니다.</p>"
        return f"<h3>XSS (Stored) — Guestbook</h3>{items}"
