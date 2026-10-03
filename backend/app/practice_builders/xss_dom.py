from .xss_common import XssBuilderBase, escape, js_string

# DOM XSS: 서버는 값을 "안전하게 문자열로만" 페이지에 넘긴다(js_string).
# 취약점은 브라우저에서 실행되는 페이지 JS가 그 값을 위험한 싱크(document.write/innerHTML)에
# 넣는 순간 생긴다 — 서버 코드에는 문제가 없어도 터지는 것이 DOM XSS의 핵심.
#
# low:    document.write, 필터 없음
# medium: document.write, "<script" 포함 시 기본값으로 교체 → 다른 태그(img onerror)로 우회
# high:   innerHTML, "<script"·onerror·onload 차단 → 목록에 없는 이벤트(ontoggle 등)로 우회
# impossible: textContent (HTML로 해석하지 않음)
_SCRIPTS = {
    "low": (
        "document.write('<p>선택한 언어: ' + hash + '</p>');"
    ),
    "medium": (
        "if (/<script/i.test(hash)) { hash = 'Korean'; }\n"
        "document.write('<p>선택한 언어: ' + hash + '</p>');"
    ),
    "high": (
        "if (/<script|onerror|onload/i.test(hash)) { hash = 'Korean'; }\n"
        "document.getElementById('lang').innerHTML = '선택한 언어: ' + hash;"
    ),
    "impossible": (
        "document.getElementById('lang').textContent = '선택한 언어: ' + hash;"
    ),
}

_HINTS = {
    "low": [
        "이 페이지는 주소창 # 뒤의 값을 JavaScript로 읽어 document.write()로 화면에 씁니다.",
        "document.write()는 받은 문자열을 HTML로 해석합니다. 서버를 거치지 않고 브라우저 안에서 일어나는 일입니다.",
        "예: <script>alert(1)</script>",
    ],
    "medium": [
        "페이지 소스를 보세요. 값에 `<script` 가 있으면 기본값으로 바꿔버립니다.",
        "필터가 브라우저 JS에 있으면 공격자도 그대로 읽을 수 있습니다. script 태그가 아닌 다른 방법은?",
        "예: <img src=x onerror=alert(1)>",
    ],
    "high": [
        "이번엔 innerHTML을 씁니다. innerHTML로 넣은 <script> 태그는 실행되지 않습니다.",
        "필터는 `<script`, `onerror`, `onload` 만 막습니다. 이벤트 속성은 그 밖에도 많습니다.",
        "예: <details open ontoggle=alert(1)>",
    ],
    "impossible": [
        "이 단계는 innerHTML 대신 textContent를 씁니다.",
        "textContent는 값을 HTML이 아닌 순수 글자로만 넣기 때문에 태그가 만들어지지 않습니다.",
    ],
}


class XssDomBuilder(XssBuilderBase):
    slug = "xss-dom"
    _hints = _HINTS

    def build_body(self, difficulty, payload):
        # DVWA xss_d: ?default=English 를 document.write 로 select 에 반영
        return (
            f"<div class='bar'>vulnerabilities/xss_d/?default={escape(payload)}</div>"
            "<h3>XSS (DOM)</h3>"
            "<p>Please choose a language:</p>"
            "<form name='XSS'><div id='lang'></div></form>"
            "<script>\n"
            "// DVWA: var default = document.location.href 에서 default 파라미터를 읽음\n"
            f"var hash = {js_string(payload)};\n"
            f"{_SCRIPTS[difficulty]}\n"
            "</script>"
        )
