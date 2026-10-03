"""File Upload — DVWA 재현.

DVWA vulnerabilities/upload:
  low        : 검사 없음 → 웹셸 바로 업로드·실행
  medium     : $_FILES type(Content-Type/MIME) 가 image/jpeg|png 인지 + 크기 검사
               → Burp/DevTools 로 Content-Type 을 위조해 우회
  high       : 확장자(jpg/jpeg/png) 화이트리스트 + getimagesize()(매직바이트) 검사
               → 폴리글랏(이미지 매직 + 코드) + 이중 확장자로 우회
  impossible : 재인코딩/실행 불가 격리 → 실행 안 됨

실행 모델: 파일명에 .php 또는 .sh 가 포함되면 서버가 셸로 실행(업로드 경로가 실행 가능하게
잘못 설정된 상황 모사). 성공 = 업로드된 내용이 실행되어 심어둔 flag 를 출력.
"""
import secrets

from .. import sandbox_client
from .base import PracticeBuilder, PracticeResult

_MAX_NAME_LEN = 100
_MAX_CONTENT_LEN = 2000
_IMAGE_MIMES = {"image/jpeg", "image/png", "image/gif"}
_IMAGE_EXTS = {"jpg", "jpeg", "png", "gif"}
_IMAGE_MAGICS = ("GIF89a", "GIF87a", "\x89PNG", "\xff\xd8\xff")

_HINTS = {
    "low": [
        "확장자·타입 검사가 전혀 없습니다. 서버는 파일명에 .php/.sh 가 있으면 실행합니다.",
        "flag 는 실행 환경의 /tmp/flag.txt 에 있습니다. 그 내용을 출력하는 웹셸을 올리세요.",
        "예) 파일명: shell.sh / 내용: cat /tmp/flag.txt",
    ],
    "medium": [
        "서버가 요청의 Content-Type(MIME)이 image/jpeg·png 인지 검사합니다. 파일명/내용은 안 봅니다.",
        "화면에서는 파일에 맞는 MIME가 자동으로 붙습니다. DevTools/Burp로 요청의 mimetype 을 image/jpeg 로 위조하면 .sh 도 통과합니다.",
        "예) 파일명 shell.sh + 내용 cat /tmp/flag.txt + (변조) mimetype=image/jpeg",
    ],
    "high": [
        "마지막 확장자가 이미지(jpg/png/gif)여야 하고, 내용도 이미지 매직바이트로 시작해야 합니다(getimagesize).",
        "이미지 매직바이트(GIF89a) 뒤에 셸 명령을 붙인 폴리글랏으로, 이름엔 .sh 를 포함시키세요.",
        "예) 파일명: shell.sh.gif / 내용 첫 줄 GIF89a; 다음 줄 cat /tmp/flag.txt",
    ],
    "impossible": [
        "이미지 검사에 더해 업로드 파일을 재인코딩/실행 불가 영역에 저장합니다.",
        "검사를 통과해도 실행되지 않아 코드가 돌지 않습니다.",
    ],
}


class FileUploadBuilder(PracticeBuilder):
    difficulties = ("low", "medium", "high", "impossible")

    def validate_input(self, difficulty, user_input):
        if difficulty not in self.difficulties:
            return "지원하지 않는 난이도입니다."
        if not isinstance(user_input, dict):
            return "잘못된 요청입니다."
        filename = user_input.get("filename", "")
        content = user_input.get("content", "")
        if not isinstance(filename, str) or not filename.strip():
            return "파일명을 입력하세요."
        if len(filename) > _MAX_NAME_LEN:
            return f"파일명은 {_MAX_NAME_LEN}자 이내로 입력하세요."
        if "/" in filename or "\\" in filename:
            return "파일명에 경로 구분자는 쓸 수 없습니다."
        if not isinstance(content, str) or not content.strip():
            return "파일 내용을 입력하세요."
        if len(content) > _MAX_CONTENT_LEN:
            return f"파일 내용은 {_MAX_CONTENT_LEN}자 이내로 입력하세요."
        mimetype = user_input.get("mimetype", "")
        if not isinstance(mimetype, str) or len(mimetype) > 100:
            return "mimetype 형식이 올바르지 않습니다."
        return None

    def hints(self, difficulty):
        return list(_HINTS.get(difficulty, []))

    def _last_ext(self, filename):
        return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    def _looks_like_image(self, content):
        return any(content.startswith(m) for m in _IMAGE_MAGICS)

    def _filter(self, difficulty, filename, content, mimetype):
        if difficulty == "low":
            return True, ""
        if difficulty == "medium":
            # DVWA medium: 클라이언트가 보낸 Content-Type(MIME)만 검사
            if mimetype not in _IMAGE_MIMES:
                return False, f"이미지 파일만 업로드할 수 있습니다. (받은 Content-Type: {mimetype or '없음'})"
            return True, ""
        # high / impossible: 확장자 화이트리스트 + 매직바이트
        if self._last_ext(filename) not in _IMAGE_EXTS:
            return False, "이미지 파일(jpg·png·gif)만 업로드할 수 있습니다."
        if not self._looks_like_image(content):
            return False, "파일 내용이 이미지 형식이 아닙니다(매직바이트 불일치)."
        return True, ""

    def _executes(self, filename):
        name = filename.lower()
        return ".php" in name or ".sh" in name

    def run(self, difficulty, user_input):
        filename = user_input["filename"]
        content = user_input["content"]
        mimetype = user_input.get("mimetype", "")

        accepted, reason = self._filter(difficulty, filename, content, mimetype)
        if not accepted:
            return PracticeResult(output=f"업로드 거부됨 — {reason}", success=False)

        if difficulty == "impossible":
            return PracticeResult(
                output="업로드 성공. 단, 재인코딩되어 실행 불가 영역에 저장되므로 코드가 실행되지 않습니다.",
                success=False,
            )

        if not self._executes(filename):
            return PracticeResult(
                output=f"업로드 성공: {filename}\n하지만 서버가 이 파일을 실행 대상으로 인식하지 않아 코드가 실행되지 않았습니다.",
                success=False,
            )

        flag = secrets.token_hex(16)
        command = f"echo {flag} > /tmp/flag.txt\n{content}"
        result = sandbox_client.execute({"mode": "shell", "command": command, "timeout": 3})
        if result.get("timed_out"):
            return PracticeResult(output="(실행 실패 또는 시간 초과)", success=False)
        stdout = result.get("stdout") or ""
        success = flag in stdout
        shown = (stdout.strip() or (result.get("stderr") or "").strip() or "(출력 없음)")
        header = f"파일 업로드됨: {filename}\n업로드된 웹셸이 서버에서 실행되었습니다.\n실행 결과:\n"
        return PracticeResult(output=header + shown, success=success)
