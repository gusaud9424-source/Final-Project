import os
import re
import secrets

import bcrypt

from app import create_app, db
from app.models import AttendanceSession, Course, Enrollment, User

app = create_app()


def _hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _normalize_phone(phone):
    return re.sub(r"\D", "", phone or "")


def _seed_user(username, role, name, email, phone, password=None):
    """반환하는 두 번째 값은 이번 호출에서 새로 자동 생성한 비밀번호일 때만 채워진다.
    .env로 전달된 값이나 기존 계정의 값은 이미 알려진 값이므로 어떤 경로로도 다시 반환·출력하지 않는다."""
    user = User.query.filter_by(username=username).first()
    if user:
        if password:
            user.password_hash = _hash_password(password)
            db.session.commit()
        return user, None

    generated_password = password is None
    password = password or secrets.token_urlsafe(9)
    user = User(
        username=username,
        password_hash=_hash_password(password),
        role=role,
        name=name,
        email=email,
        phone=_normalize_phone(phone),
    )
    db.session.add(user)
    db.session.commit()
    return user, (password if generated_password else None)


CATALOG = [
    dict(slug="command-injection", difficulty="초급", title="Command Injection",
         description="입력값에 OS 명령을 주입해 서버에서 실행시키는 취약점", icon="bi-terminal"),
    dict(slug="xss-reflected", difficulty="초급", title="XSS (Reflected)",
         description="요청 파라미터가 응답에 그대로 반사되어 스크립트가 실행됨", icon="bi-code-slash"),
    dict(slug="xss-dom", difficulty="초급", title="XSS (DOM)",
         description="클라이언트 DOM 조작 과정에서 스크립트가 실행됨", icon="bi-braces"),
    dict(slug="xss-stored", difficulty="초급", title="XSS (Stored)",
         description="저장된 입력값이 다른 사용자 화면에서 스크립트로 실행됨", icon="bi-chat-square-text"),
    dict(slug="sql-injection", difficulty="중급", title="SQL Injection",
         description="쿼리 조작으로 DB 데이터를 유출하는 취약점", icon="bi-database"),
    dict(slug="csrf", difficulty="중급", title="CSRF",
         description="피해자 권한으로 위조 요청(비밀번호 변경 등)을 실행시키는 취약점", icon="bi-shuffle"),
    dict(slug="file-upload", difficulty="중급", title="File Upload",
         description="웹셸 등 악성 파일 업로드로 원격 코드 실행", icon="bi-file-earmark-arrow-up"),
    dict(slug="sql-injection-blind", difficulty="고급", title="SQL Injection (Blind)",
         description="참/거짓·시간지연 응답으로 데이터를 추론하는 기법", icon="bi-search"),
]


def _seed_catalog_courses():
    courses = {}
    for entry in CATALOG:
        course = Course.query.filter_by(slug=entry["slug"]).first()
        if not course:
            # 레거시 시드 데이터(슬러그 없이 생성된 동일 제목 과목)를 재사용
            course = Course.query.filter_by(title=entry["title"], slug=None).first()
        if course:
            course.slug = entry["slug"]
            course.difficulty = entry["difficulty"]
            course.description = entry["description"]
            course.icon = entry["icon"]
        else:
            course = Course(
                slug=entry["slug"],
                title=entry["title"],
                description=entry["description"],
                icon=entry["icon"],
                difficulty=entry["difficulty"],
            )
            db.session.add(course)
        courses[entry["slug"]] = course
    db.session.commit()
    return courses


def _seed_course_data(student, course):
    enrollment = Enrollment.query.filter_by(user_id=student.id, course_id=course.id).first()
    if enrollment:
        return

    enrollment = Enrollment(
        user_id=student.id,
        course_id=course.id,
        percent=50,
        badge_type="round",
        badge_label="2/4 완료",
    )
    db.session.add(enrollment)
    db.session.commit()

    db.session.add_all(
        [
            AttendanceSession(enrollment_id=enrollment.id, session_no=1, status="submitted"),
            AttendanceSession(enrollment_id=enrollment.id, session_no=2, status="submitted"),
            AttendanceSession(enrollment_id=enrollment.id, session_no=3, status="absent"),
            AttendanceSession(enrollment_id=enrollment.id, session_no=4, status="absent"),
        ]
    )
    db.session.commit()


with app.app_context():
    admin, admin_password = _seed_user(
        username="admin",
        role="admin",
        name="관리자",
        email="admin@secuquest.local",
        phone="01000000000",
    )
    student, student_password = _seed_user(
        username="student1",
        role="student",
        name="학습자1",
        email=os.environ["SEED_STUDENT_EMAIL"],
        phone=os.environ["SEED_STUDENT_PHONE"],
        password=os.environ.get("SEED_STUDENT_PASSWORD"),
    )
    courses = _seed_catalog_courses()
    _seed_course_data(student, courses["command-injection"])

    if admin_password:
        print(f"[seed] admin 계정 생성 — username=admin, password={admin_password}")
    if student_password:
        print(f"[seed] student1 계정 생성 — username=student1, password={student_password}")
    print("seed done")
