import re

from .xss_common import XssBuilderBase, escape

# DVWA Reflected XSS 단계 구성을 따른다.
# medium: "<script>" 문자열만(대소문자 구분) 제거 → 대문자/다른 태그로 우회
# high:   s·c·r·i·p·t 순서로 들어간 태그를 정규식으로 제거 → script 아닌 태그(img 등)로 우회
_HIGH_RE = re.compile(r"<(.*)s(.*)c(.*)r(.*)i(.*)p(.*)t", re.IGNORECASE)

_HINTS = {
    "low": [
        "검색어가 아무 처리 없이 HTML 응답에 그대로 들어갑니다(반사).",
        "HTML 태그를 넣으면 브라우저가 태그로 해석합니다. 스크립트 태그를 넣어보세요.",
        "예: <script>alert(1)</script>",
    ],
    "medium": [
        "서버가 `<script>` 라는 문자열을 지웁니다. 그런데 정확히 그 글자만 지울까요?",
        "HTML 태그 이름은 대소문자를 구분하지 않습니다. 또는 script 태그가 아니어도 스크립트를 실행할 수 있습니다.",
        "예: <SCRIPT>alert(1)</SCRIPT>  또는  <img src=x onerror=alert(1)>",
    ],
    "high": [
        "이번엔 대소문자와 상관없이 s·c·r·i·p·t 가 들어간 태그를 정규식으로 통째로 지웁니다.",
        "script 태그 없이도 이벤트 속성(onerror 등)으로 스크립트를 실행할 수 있습니다.",
        "예: <img src=x onerror=alert(1)>",
    ],
    "impossible": [
        "이 단계는 출력 직전에 HTML 특수문자(< > \" ' &)를 엔티티로 인코딩합니다.",
        "브라우저는 &lt;script&gt; 를 태그가 아닌 글자로 보여주므로 스크립트가 실행되지 않습니다.",
    ],
}


class XssReflectedBuilder(XssBuilderBase):
    slug = "xss-reflected"
    _hints = _HINTS

    def _filter(self, difficulty, payload):
        if difficulty == "medium":
            return payload.replace("<script>", "")
        if difficulty == "high":
            return _HIGH_RE.sub("", payload)
        if difficulty == "impossible":
            return escape(payload)
        return payload

    def build_body(self, difficulty, payload):
        shown = self._filter(difficulty, payload)
        # DVWA xss_r: echo "Hello {name}"
        return (
            "<h3>XSS (Reflected)</h3>"
            "<p>What's your name?</p>"
            f"<pre>Hello {shown}</pre>"
        )
