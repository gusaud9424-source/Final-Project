import json
import socket

SOCK_PATH = "/ipc/sandbox.sock"
CONNECT_TIMEOUT_SEC = 2
IO_TIMEOUT_SEC = 6
MAX_RESPONSE_BYTES = 1_000_000


def _recv_until_newline(sock):
    chunks = []
    total = 0
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_RESPONSE_BYTES or b"\n" in chunk:
            break
    return b"".join(chunks).split(b"\n", 1)[0]


def execute(payload):
    """sandbox runner에 실행 요청을 보내고 결과를 받는다.
    연결 실패·타임아웃·응답 파싱 실패는 모두 timed_out=True의 graceful 결과로 수렴한다."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(CONNECT_TIMEOUT_SEC)
            sock.connect(SOCK_PATH)
            sock.settimeout(IO_TIMEOUT_SEC)
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            raw = _recv_until_newline(sock)
            return json.loads(raw.decode("utf-8"))
    except (OSError, socket.timeout, ValueError, UnicodeDecodeError):
        return {
            "stdout": "",
            "stderr": "sandbox 응답 없음",
            "exit_code": None,
            "timed_out": True,
            "error": "sandbox_unreachable",
        }
