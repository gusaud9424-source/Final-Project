import json
import os
import resource
import shutil
import socket
import subprocess

SOCK_PATH = "/ipc/sandbox.sock"
TMP_DIR = "/tmp"
MAX_TIMEOUT_SEC = 5
MAX_STDOUT = 4000
MAX_STDERR = 2000
MAX_REQUEST_BYTES = 1_000_000


def reset_state():
    """/tmp(tmpfs)를 비워 이전 실행 흔적을 제거한다. 각 요청 전후로 호출."""
    for name in os.listdir(TMP_DIR):
        path = os.path.join(TMP_DIR, name)
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError:
            pass


def _limit_child_resources():
    # 컨테이너 레벨 제한(mem_limit/pids_limit/cpus) 위에 자식 프로세스 이중 방어.
    # RLIMIT_NPROC은 유저 네임스페이스 리맵 없는 환경에서 "실제 UID" 기준으로
    # 호스트 전체 프로세스 수를 세기 때문에(컨테이너로 격리되지 않음) 여기서는 사용하지 않는다.
    # 포크 폭탄 방어는 컨테이너 cgroup의 pids_limit(64)이 담당한다.
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))


def run_request(req):
    reset_state()
    timeout = min(req.get("timeout_sec") or MAX_TIMEOUT_SEC, MAX_TIMEOUT_SEC)
    mode = req.get("mode")

    if mode == "shell":
        args = ["/bin/sh", "-c", req.get("command", "")]
    elif mode == "argv":
        args = list(req.get("argv") or [])
    else:
        reset_state()
        return {"stdout": "", "stderr": f"unknown mode: {mode}", "exit_code": None, "timed_out": False}

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            preexec_fn=_limit_child_resources,
            cwd=TMP_DIR,
        )
        result = {
            "stdout": proc.stdout[:MAX_STDOUT],
            "stderr": proc.stderr[:MAX_STDERR],
            "exit_code": proc.returncode,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "stdout": (exc.stdout or "")[:MAX_STDOUT],
            "stderr": (exc.stderr or "")[:MAX_STDERR],
            "exit_code": None,
            "timed_out": True,
        }
    except OSError as exc:
        result = {"stdout": "", "stderr": str(exc), "exit_code": None, "timed_out": False}

    reset_state()
    return result


def _recv_until_newline(conn):
    chunks = []
    total = 0
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_REQUEST_BYTES or b"\n" in chunk:
            break
    return b"".join(chunks).split(b"\n", 1)[0]


def serve():
    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)
    reset_state()

    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK_PATH)
    os.chmod(SOCK_PATH, 0o666)
    srv.listen(1)

    while True:
        conn, _ = srv.accept()
        with conn:
            try:
                raw = _recv_until_newline(conn)
                req = json.loads(raw.decode("utf-8"))
                result = run_request(req)
            except (ValueError, UnicodeDecodeError) as exc:
                result = {"stdout": "", "stderr": f"bad request: {exc}", "exit_code": None, "timed_out": False}
            conn.sendall((json.dumps(result) + "\n").encode("utf-8"))


if __name__ == "__main__":
    serve()
