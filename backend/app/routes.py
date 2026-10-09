from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


# 서버 상태 확인용 (Docker · Nginx 연결 점검). 디버그용 /api/session-test, 초기 설계의
# /pdf/health · /practice/health 는 쓰이지 않아 삭제 (기능 점검표 #11 · #12)
@bp.route("/api/health")
def api_health():
    return jsonify(status="ok", module="api")
