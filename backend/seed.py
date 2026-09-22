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


def _seed_user(username, role, name, email, phone):
    user = User.query.filter_by(username=username).first()
    if user:
        return user, None

    password = secrets.token_urlsafe(9)
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
    return user, password


def _seed_course_data(student):
    course = Course.query.filter_by(title="Command Injection").first()
    if not course:
        course = Course(
            title="Command Injection",
            description="입력값 검증 우회로 시스템 명령을 실행하는 취약점 실습",
            icon="bi-terminal",
            instructor="김보안",
            schedule="월·10:00",
        )
        db.session.add(course)
        db.session.commit()

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
    )
    _seed_course_data(student)

    if admin_password:
        print(f"[seed] admin 계정 생성 — username=admin, password={admin_password}")
    if student_password:
        print(f"[seed] student1 계정 생성 — username=student1, password={student_password}")
    print("seed done")
