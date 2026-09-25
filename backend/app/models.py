from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "student", name="user_role"), nullable=False, default="student")
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    enrollments = db.relationship("Enrollment", backref="user", lazy=True)


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(40))
    difficulty = db.Column(db.Enum("초급", "중급", "고급", name="course_difficulty"))
    instructor = db.Column(db.String(80))
    schedule = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    enrollments = db.relationship("Enrollment", backref="course", lazy=True)


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    percent = db.Column(db.Integer, nullable=False, default=0)
    badge_type = db.Column(db.String(20), nullable=False, default="round")
    badge_label = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    attendance_sessions = db.relationship(
        "AttendanceSession", backref="enrollment", lazy=True, order_by="AttendanceSession.session_no"
    )


class AttendanceSession(db.Model):
    __tablename__ = "attendance_sessions"
    __table_args__ = (
        db.UniqueConstraint("enrollment_id", "session_no", name="uq_attendance_enrollment_session"),
    )

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id"), nullable=False)
    session_no = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum("submitted", "absent", name="attendance_status"), nullable=False)


TASK_KEYS = ("concept", "practice", "defense")


class TaskProgress(db.Model):
    __tablename__ = "task_progress"
    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", "task_key", name="uq_task_progress_user_course_task"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    # 허용 값은 TASK_KEYS 상수로 애플리케이션에서 검증
    task_key = db.Column(db.String(20), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class VerificationCode(db.Model):
    __tablename__ = "verification_codes"
    __table_args__ = (
        db.Index("ix_verification_target_purpose", "target", "purpose"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    target = db.Column(db.String(120), nullable=False)
    purpose = db.Column(
        db.Enum("find_id", "reset_password_email", "reset_password_sms", name="verification_purpose"),
        nullable=False,
    )
    code_hash = db.Column(db.String(64), nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
