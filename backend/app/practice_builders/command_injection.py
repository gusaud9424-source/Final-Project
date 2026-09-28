import re
import secrets

from .. import sandbox_client
from .base import PracticeBuilder, PracticeResult

_WHITELIST_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_MAX_INPUT_LEN = 200

# Low는 필터 없음. Medium/High 모두 파이프(|)는 걸러내지 않는다 —
# High가 더 많은 문자를 막아도 여전히 뚫리는 지점이 있다는 걸 보여주기 위한 의도적 설계.
_BLACKLISTS = {
    "medium": [";", "&&"],
    "high": [";", "&&", "`", "$(", "\n", "\r"],
}

_HINTS = {
    "low": [
        "입력값이 필터링 없이 명령어 뒤에 그대로 이어붙습니다.",
        "셸 구분자(`;`, `&&`, `|` 등)로 원래 명령 뒤에 새 명령을 실행할 수 있습니다.",
        "예: 검색어 자리에 `아무값 ; cat /tmp/flag.txt` 를 넣어보세요.",
    ],
    "medium": [
        "`;` 와 `&&` 는 서버가 제거합니다.",
        "구분자가 그 두 개뿐일까요? 파이프(`|`)를 떠올려보세요.",
        "예: 검색어 자리에 `아무값 | cat /tmp/flag.txt` 를 넣어보세요.",
    ],
    "high": [
        "`;`, `&&`, 백틱, `$()`, 개행까지 막혔습니다.",
        "그런데 필터 목록에 파이프(`|`)는 있었나요?",
        "예: 검색어 자리에 `아무값 | cat /tmp/flag.txt` 를 넣어보세요.",
    ],
    "impossible": [
        "이 티어는 화이트리스트 검증(영숫자·`.`·`_`·`-`만 허용) 후 셸을 거치지 않고 인자 배열로 바로 실행합니다.",
        "특수문자가 입력 단계에서 거부되므로 셸이 해석할 메타문자 자체가 전달되지 않습니다.",
    ],
}


class CommandInjectionBuilder(PracticeBuilder):
    difficulties = ("low", "medium", "high", "impossible")

    def validate_input(self, difficulty, user_input):
        if difficulty not in self.difficulties:
            return "지원하지 않는 난이도입니다."
        if not isinstance(user_input, str) or not user_input.strip():
            return "검색어를 입력하세요."
        if len(user_input) > _MAX_INPUT_LEN:
            return f"검색어는 {_MAX_INPUT_LEN}자 이내로 입력하세요."
        if difficulty == "impossible" and not _WHITELIST_RE.match(user_input):
            return "영문·숫자·`.`·`_`·`-`만 허용됩니다."
        return None

    def hints(self, difficulty):
        return list(_HINTS.get(difficulty, []))

    def run(self, difficulty, user_input):
        if difficulty == "impossible":
            result = sandbox_client.execute(
                {"mode": "argv", "argv": ["grep", user_input, "/etc/hostname"], "timeout": 3}
            )
            return PracticeResult(output=self._format_output(result), success=False)

        flag_token = secrets.token_hex(16)
        filtered_input = self._apply_filter(difficulty, user_input)
        # flag 심기 + 로그 준비 + 취약한 검색 실행을 한 요청으로 묶는다.
        # sandbox runner가 /tmp 를 요청 전/후로 초기화하므로, 두 번의 요청에 걸쳐서는
        # flag 파일이 생존할 수 없다 (reset_state 상호작용).
        command = (
            f"echo {flag_token} > /tmp/flag.txt && "
            f"echo 'search log ready' > /tmp/app.log && "
            f"grep {filtered_input} /tmp/app.log"
        )
        result = sandbox_client.execute({"mode": "shell", "command": command, "timeout": 3})
        stdout = result.get("stdout") or ""
        success = flag_token in stdout
        return PracticeResult(output=self._format_output(result), success=success)

    def _apply_filter(self, difficulty, user_input):
        filtered = user_input
        for token in _BLACKLISTS.get(difficulty, []):
            filtered = filtered.replace(token, "")
        return filtered

    def _format_output(self, result):
        if result.get("timed_out"):
            return "(실행 실패 또는 시간 초과)"
        stdout = (result.get("stdout") or "").strip()
        stderr = (result.get("stderr") or "").strip()
        return stdout or stderr or "(출력 없음)"
