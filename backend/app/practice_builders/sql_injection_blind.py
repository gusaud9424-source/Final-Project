"""SQL Injection (Blind) — DVWA 재현.

DVWA sqli_blind: User ID 조회 결과를 보여주지 않고 "User ID exists / is MISSING" 만 응답.
users 테이블(일반 SQLi와 동일)에서 admin 의 password 를 참/거짓으로 한 글자씩 추출한다.
  low        : WHERE user_id = '$id'
  medium     : WHERE user_id = $id        (숫자 + 이스케이프, 드롭다운 → 요청 변조)
  high       : WHERE user_id = '$id' LIMIT 1
  impossible : is_numeric + 파라미터 바인딩

보상 연동: 추출한 admin 비밀번호를 제출해 세션 값과 일치하면 성공.
"""
import secrets

from flask import session

from .. import sandbox_client
from .base import PracticeBuilder, PracticeResult

_MAX_INPUT_LEN = 200
_PW_ALPHABET = "0123456789abcdef"
_PW_LEN = 4

_OTHER_USERS = [
    (2, "Gordon", "Brown", "gordonb", "ab12"),
    (3, "Hack", "Me", "1337", "cd34"),
    (4, "Pablo", "Picasso", "pablo", "ef56"),
    (5, "Bob", "Smith", "smithy", "7890"),
]

_HINTS = {
    "low": [
        "결과는 안 보이고 'User ID exists / is MISSING' 만 나옵니다. 조건의 참/거짓을 관찰하세요.",
        "admin 은 user_id=1 입니다. user_id=1 조건에 비밀번호 한 글자 조건을 AND로 걸어 exists(참)/missing(거짓)을 봅니다. SUBSTR(password,위치,1).",
        "예: 1' AND SUBSTR(password,1,1)='a' -- ",
    ],
    "medium": [
        "숫자 컨텍스트(= $id) + 드롭다운입니다. DevTools/Burp로 id 값을 변조하세요(따옴표 불필요).",
        "서브쿼리로 admin 비밀번호 글자를 비교합니다.",
        "예(변조 값): 0 OR (SELECT SUBSTR(password,1,1) FROM users WHERE user='admin')='a'",
    ],
    "high": [
        "끝에 LIMIT 1 이 붙습니다. 주석(--)으로 잘라내고 참/거짓을 관찰하세요.",
        "예: 1' AND SUBSTR(password,1,1)='a' -- ",
    ],
    "impossible": [
        "숫자 검증 + 파라미터 바인딩이라 주입이 성립하지 않습니다.",
        "항상 정상 조회만 되어 참/거짓 추론이 불가능합니다.",
    ],
}


class SqlInjectionBlindBuilder(PracticeBuilder):
    difficulties = ("low", "medium", "high", "impossible")
    actions = ("probe", "submit", "info")

    def _secret_key(self, difficulty):
        return f"blind_pw:{difficulty}"

    def _get_secret(self, difficulty):
        key = self._secret_key(difficulty)
        secret = session.get(key)
        if not secret:
            secret = "".join(secrets.choice(_PW_ALPHABET) for _ in range(_PW_LEN))
            session[key] = secret
        return secret

    def _init_sql(self, secret):
        rows = [(1, "admin", "admin", "admin", secret)] + _OTHER_USERS
        stmts = ["CREATE TABLE users (user_id INTEGER, first_name TEXT, last_name TEXT, user TEXT, password TEXT)"]
        for uid, fn, ln, u, pw in rows:
            stmts.append(f"INSERT INTO users VALUES ({uid}, '{fn}', '{ln}', '{u}', '{pw}')")
        return stmts

    def validate_input(self, difficulty, user_input):
        if difficulty not in self.difficulties:
            return "지원하지 않는 난이도입니다."
        if not isinstance(user_input, dict):
            return "잘못된 요청입니다."
        action = user_input.get("action")
        if action not in self.actions:
            return "지원하지 않는 동작입니다."
        payload = user_input.get("payload", "")
        if not isinstance(payload, str) or len(payload) > _MAX_INPUT_LEN:
            return f"입력은 {_MAX_INPUT_LEN}자 이내 문자열이어야 합니다."
        if action == "probe" and not payload.strip():
            return "User ID를 입력하세요."
        return None

    def hints(self, difficulty):
        return list(_HINTS.get(difficulty, []))

    def _escape(self, value):
        return value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')

    def run(self, difficulty, user_input):
        action = user_input["action"]
        secret = self._get_secret(difficulty)

        if action == "info":
            return PracticeResult(
                output=f"admin 비밀번호는 {len(secret)}글자(0-9,a-f)입니다. exists/missing 응답으로 추출하세요.",
                success=False,
            )

        if action == "submit":
            guess = (user_input.get("payload") or "").strip().lower()
            if secrets.compare_digest(guess, secret):
                session.pop(self._secret_key(difficulty), None)
                return PracticeResult(output="정답입니다! 블라인드로 admin 비밀번호를 추출했습니다.", success=True)
            return PracticeResult(output="비밀번호가 틀렸습니다. 참/거짓으로 더 좁혀보세요.", success=False)

        # probe
        init = self._init_sql(secret)
        params = None
        uid = user_input["payload"]
        if difficulty == "low":
            query = f"SELECT first_name FROM users WHERE user_id = '{uid}'"
        elif difficulty == "medium":
            query = f"SELECT first_name FROM users WHERE user_id = {self._escape(uid)}"
        elif difficulty == "high":
            query = f"SELECT first_name FROM users WHERE user_id = '{uid}' LIMIT 1"
        else:  # impossible
            if not uid.strip().isdigit():
                return PracticeResult(output="User ID is MISSING from the database. (숫자 검증 + 바인딩)", success=False)
            query = "SELECT first_name FROM users WHERE user_id = ? LIMIT 1"
            params = [int(uid.strip())]

        payload = {"mode": "sqlite", "flag": secret, "query": query, "init": init, "timeout": 3}
        if params is not None:
            payload["params"] = params
        result = sandbox_client.execute(payload)
        if result.get("timed_out"):
            return PracticeResult(output="(실행 실패 또는 시간 초과)", success=False)
        stderr = (result.get("stderr") or "").strip()
        if "SQL 오류" in stderr:
            # DVWA 는 블라인드라 에러도 안 보여주지만, 학습을 위해 문법 오류만 간단히 알림
            return PracticeResult(output="User ID is MISSING from the database.", success=False)
        rows = result.get("rows") or []
        if rows:
            return PracticeResult(output="User ID exists in the database.", success=False)
        return PracticeResult(output="User ID is MISSING from the database.", success=False)
