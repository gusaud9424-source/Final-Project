"""SQL Injection — DVWA 재현 (users 테이블 조회).

DVWA vulnerabilities/sqli 소스 기준:
  low        : WHERE user_id = '$id'            (문자열 컨텍스트, 필터 없음)
  medium     : WHERE user_id = $id              (숫자 컨텍스트 + 따옴표 이스케이프, 드롭다운 → 요청 변조로 우회)
  high       : WHERE user_id = '$id' LIMIT 1    (세션 입력, LIMIT 1 → 주석으로 우회)
  impossible : is_numeric 검사 + 파라미터 바인딩

성공 판정은 DVWA에 없지만 보상 연동을 위해
"UNION 으로 password 컬럼(admin flag)을 끌어냈는가"로 둔다.
비밀번호 컬럼은 정상 조회(first_name,last_name)로는 절대 노출되지 않는다.
"""
import secrets

from .. import sandbox_client
from .base import PracticeBuilder, PracticeResult

_MAX_INPUT_LEN = 200

# DVWA 기본 사용자 + admin 비밀번호에 일회용 flag (나머지는 실제 DVWA md5 해시 모사)
_OTHER_USERS = [
    (2, "Gordon", "Brown", "gordonb", "e99a18c428cb38d5f260853678922e03"),
    (3, "Hack", "Me", "1337", "8d3533d75ae2c3966d7e0d4fcc69216b"),
    (4, "Pablo", "Picasso", "pablo", "0d107d09f5bbe40cade3de5c71e9e9b7"),
    (5, "Bob", "Smith", "smithy", "5f4dcc3b5aa765d61d8327deb882cf99"),
]

_HINTS = {
    "low": [
        "User ID가 작은따옴표 사이에 그대로 들어갑니다: ... WHERE user_id = '입력'",
        "따옴표로 문자열을 닫고 UNION SELECT 로 다른 컬럼을 끌어올 수 있습니다. 컬럼 수는 2개(First name, Surname)입니다.",
        "예: ' UNION SELECT user, password FROM users -- ",
    ],
    "medium": [
        "입력이 드롭다운(1~5)이고 숫자 컨텍스트로 들어갑니다: ... WHERE user_id = 입력 (따옴표 없음).",
        "드롭다운이라 화면에서는 1~5만 보냅니다. DevTools나 Burp로 요청 본문의 id 값을 직접 바꿔야 합니다. 숫자 컨텍스트라 따옴표가 필요 없습니다.",
        "예(요청 변조 값): 0 UNION SELECT user, password FROM users",
    ],
    "high": [
        "쿼리 끝에 LIMIT 1 이 붙어 한 행만 반환합니다: ... WHERE user_id = '입력' LIMIT 1",
        "주석(--)으로 뒤의 LIMIT 1 을 없애면 여러 행을 가져올 수 있습니다.",
        "예: ' UNION SELECT user, password FROM users -- ",
    ],
    "impossible": [
        "입력이 숫자인지 검사한 뒤 파라미터 바인딩(?)으로 실행됩니다.",
        "입력이 쿼리 구조와 분리되어 주입이 성립하지 않습니다.",
    ],
}


class SqlInjectionBuilder(PracticeBuilder):
    difficulties = ("low", "medium", "high", "impossible")

    def _init_sql(self, flag):
        rows = [(1, "admin", "admin", "admin", flag)] + _OTHER_USERS
        stmts = ["CREATE TABLE users (user_id INTEGER, first_name TEXT, last_name TEXT, user TEXT, password TEXT)"]
        for uid, fn, ln, u, pw in rows:
            stmts.append(
                f"INSERT INTO users VALUES ({uid}, '{fn}', '{ln}', '{u}', '{pw}')"
            )
        return stmts

    def validate_input(self, difficulty, user_input):
        if difficulty not in self.difficulties:
            return "지원하지 않는 난이도입니다."
        if not isinstance(user_input, str) or not user_input.strip():
            return "User ID를 입력하세요."
        if len(user_input) > _MAX_INPUT_LEN:
            return f"입력은 {_MAX_INPUT_LEN}자 이내로 입력하세요."
        return None

    def hints(self, difficulty):
        return list(_HINTS.get(difficulty, []))

    def _escape(self, value):
        # mysqli_real_escape_string 모사 (숫자 컨텍스트라 실제 우회엔 영향 없음)
        return value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')

    def run(self, difficulty, user_input):
        flag = secrets.token_hex(16)
        init = self._init_sql(flag)
        params = None

        if difficulty == "low":
            query = f"SELECT first_name, last_name FROM users WHERE user_id = '{user_input}'"
        elif difficulty == "medium":
            query = f"SELECT first_name, last_name FROM users WHERE user_id = {self._escape(user_input)}"
        elif difficulty == "high":
            query = f"SELECT first_name, last_name FROM users WHERE user_id = '{user_input}' LIMIT 1"
        else:  # impossible
            if not user_input.strip().isdigit():
                return PracticeResult(output="입력이 숫자가 아닙니다. (파라미터 바인딩 + 숫자 검증)", success=False)
            query = "SELECT first_name, last_name FROM users WHERE user_id = ? LIMIT 1"
            params = [int(user_input.strip())]

        payload = {"mode": "sqlite", "flag": flag, "query": query, "timeout": 3}
        if params is not None:
            payload["params"] = params
        payload["init"] = init

        result = sandbox_client.execute(payload)
        if result.get("timed_out"):
            return PracticeResult(output="(실행 실패 또는 시간 초과)", success=False)
        stderr = (result.get("stderr") or "").strip()
        if "SQL 오류" in stderr:
            return PracticeResult(output=f"오류가 발생했습니다: {stderr}", success=False)

        rows = result.get("rows") or []
        output = self._format_rows(user_input, rows)
        success = flag in (result.get("stdout") or "")
        return PracticeResult(output=output, success=success)

    def _format_rows(self, submitted_id, rows):
        if not rows:
            return "조회 결과가 없습니다."
        blocks = []
        for row in rows:
            first = row[0] if len(row) > 0 else ""
            last = row[1] if len(row) > 1 else ""
            blocks.append(f"ID: {submitted_id}\nFirst name: {first}\nSurname: {last}")
        return "\n\n".join(blocks)
