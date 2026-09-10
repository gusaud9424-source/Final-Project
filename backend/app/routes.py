from flask import Blueprint, jsonify, session

bp = Blueprint("main", __name__)


@bp.route("/api/health")
def api_health():
    return jsonify(status="ok", module="api")


@bp.route("/api/session-test")
def session_test():
    session["hits"] = session.get("hits", 0) + 1
    return jsonify(hits=session["hits"])


@bp.route("/pdf/health")
def pdf_health():
    return jsonify(status="ok", module="pdf")


@bp.route("/practice/health")
def practice_health():
    return jsonify(status="ok", module="practice")
