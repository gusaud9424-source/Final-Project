"""Command Injection — DVWA 재현 (ping 도구).

DVWA vulnerabilities/exec 의 low/medium/high/impossible 소스를 그대로 옮긴 필터.
  low        : 필터 없음
  medium     : str_replace(['&&', ';'], '', target)
  high       : str_replace(['||','&',';','| ','-','$','(',')','`'], '', target)  (순서대로)
  impossible : '.' 로 쪼개 4옥텟이 모두 숫자인지 검사 후에만 ping

성공 판정은 DVWA에 없지만, SecuQuest 보상 연동을 위해
"주입된 명령으로 /etc/passwd 를 읽어냈는가"(출력에 root: 포함)로 둔다.
"""
from .. import sandbox_client
from .base import PracticeBuilder, PracticeResult

_MAX_INPUT_LEN = 200

# DVWA high substitutions (배열 순서 그대로 — '||' 가 '| ' 보다 먼저, '|' 단독은 목록에 없음)
_HIGH_SUBS = ["||", "&", ";", "| ", "-", "$", "(", ")", "`"]
_MEDIUM_SUBS = ["&&", ";"]

_HINTS = {
    "low": [
        "입력값이 `ping -c 4 ` 뒤에 그대로 붙어 셸에서 실행됩니다. 필터가 없습니다.",
        "셸 구분자(`;`, `&&`, `|`)로 ping 뒤에 새 명령을 이어 실행할 수 있습니다.",
        "예: 127.0.0.1; cat /etc/passwd",
    ],
    "medium": [
        "서버가 `&&` 와 `;` 를 제거합니다. 그 둘만 막습니다.",
        "파이프(`|`)는 걸러지지 않습니다.",
        "예: 127.0.0.1 | cat /etc/passwd",
    ],
    "high": [
        "이번엔 `||`, `&`, `;`, `| `(파이프+공백), `-`, `$`, `(`, `)`, 백틱을 제거합니다.",
        "목록을 자세히 보세요. `| `(파이프 뒤 공백)은 막지만 공백 없는 `|` 는 빠져 있습니다.",
        "예: 127.0.0.1|cat /etc/passwd   (파이프 뒤 공백 없이)",
    ],
    "impossible": [
        "입력을 `.` 으로 쪼개 4개의 숫자 옥텟인지 검사한 뒤에만 ping 합니다.",
        "숫자 4마디(예: 127.0.0.1)가 아니면 거부되므로 셸 메타문자를 넣을 수 없습니다.",
    ],
}


class CommandInjectionBuilder(PracticeBuilder):
    difficulties = ("low", "medium", "high", "impossible")

    def validate_input(self, difficulty, user_input):
        if difficulty not in self.difficulties:
            return "지원하지 않는 난이도입니다."
        if not isinstance(user_input, str) or not user_input.strip():
            return "IP 주소를 입력하세요."
        if len(user_input) > _MAX_INPUT_LEN:
            return f"입력은 {_MAX_INPUT_LEN}자 이내로 입력하세요."
        return None

    def hints(self, difficulty):
        return list(_HINTS.get(difficulty, []))

    def _apply_filter(self, difficulty, target):
        if difficulty == "medium":
            for token in _MEDIUM_SUBS:
                target = target.replace(token, "")
        elif difficulty == "high":
            for token in _HIGH_SUBS:
                target = target.replace(token, "")
        return target

    def run(self, difficulty, user_input):
        if difficulty == "impossible":
            # DVWA impossible: '.' 4마디 + 모두 숫자
            target = user_input.replace("\\", "")
            octets = target.split(".")
            if len(octets) == 4 and all(o.isdigit() for o in octets):
                target = ".".join(octets)
                command = f"ping -c 4 {target}"
                result = sandbox_client.execute({"mode": "shell", "command": command, "timeout": 4})
                return PracticeResult(output=self._format_output(result), success=False)
            return PracticeResult(output="ERROR: You have entered an invalid IP.", success=False)

        target = self._apply_filter(difficulty, user_input)
        command = f"ping -c 4 {target}"
        result = sandbox_client.execute({"mode": "shell", "command": command, "timeout": 4})
        stdout = result.get("stdout") or ""
        # 주입으로 /etc/passwd 를 읽어냈으면 성공
        success = "root:" in stdout
        return PracticeResult(output=self._format_output(result), success=success)

    def _format_output(self, result):
        if result.get("timed_out"):
            return "(실행 시간 초과)"
        stdout = (result.get("stdout") or "").rstrip()
        stderr = (result.get("stderr") or "").rstrip()
        parts = [p for p in (stdout, stderr) if p]
        return "\n".join(parts) if parts else "(출력 없음)"
