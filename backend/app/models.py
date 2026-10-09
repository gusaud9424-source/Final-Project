from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "student", name="user_role"), nullable=False, default="student")
    nickname = db.Column(db.String(30), unique=True, nullable=True)
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


class PointLedger(db.Model):
    __tablename__ = "point_ledger"
    __table_args__ = (
        db.UniqueConstraint("user_id", "source", "ref", name="uq_point_ledger_user_source_ref"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # source 허용 값은 애플리케이션에서 검증(mission/attendance/practice/hint 등)
    source = db.Column(db.String(30), nullable=False)
    # 1회성 이벤트의 중복 지급 방지 키. NULL은 반복 지급이 의도적으로 허용된 이벤트를 뜻한다
    # (MariaDB UNIQUE 제약은 NULL끼리 충돌하지 않으므로 ref=NULL 행은 몇 개든 함께 존재할 수 있다).
    ref = db.Column(db.String(60), nullable=True)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class XpLedger(db.Model):
    __tablename__ = "xp_ledger"
    __table_args__ = (
        db.UniqueConstraint("user_id", "source", "ref", name="uq_xp_ledger_user_source_ref"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    source = db.Column(db.String(30), nullable=False)
    # ref=NULL은 반복 지급이 의도적으로 허용된 이벤트를 뜻한다(point_ledger.ref 참고)
    ref = db.Column(db.String(60), nullable=True)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class Reward(db.Model):
    """보물상자 보상. claimed_at=NULL이면 미수령, 수령 시 원장(xp/point_ledger)에 반영"""
    __tablename__ = "rewards"
    __table_args__ = (
        db.UniqueConstraint("user_id", "source", "ref", "type", name="uq_rewards_user_source_ref_type"),
        db.Index("ix_rewards_user_claimed", "user_id", "claimed_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.Enum("xp", "point", name="reward_type"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(30), nullable=False)
    # 1회성 이벤트 키(practice:<slug> / mission:<slug>). 수령 시 원장에 같은 source·ref로 기록된다
    ref = db.Column(db.String(60), nullable=False)
    reason = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    claimed_at = db.Column(db.DateTime, nullable=True)


class AuditLog(db.Model):
    """감사 로그: 누가 · 무엇을 · 누구에게 · 어디서 · 언제 (서버 로그가 지워져도 남도록 DB 보관)

    회원이 삭제돼도 기록은 남아야 하므로 users 외래키를 걸지 않고,
    아이디(username)를 기록 시점 값으로 함께 저장한다.
    """

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, nullable=True)  # 행위자 (FK 없음: 탈퇴 · 삭제 후에도 기록 유지)
    actor_username = db.Column(db.String(80), nullable=True)
    actor_role = db.Column(db.String(20), nullable=True)
    action = db.Column(db.String(40), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)  # 대상 회원 (본인 작업이면 NULL)
    target_username = db.Column(db.String(80), nullable=True)
    detail = db.Column(db.String(255), nullable=True)  # 바뀐 항목 이름 등 (개인정보 값은 넣지 않음)
    ip = db.Column(db.String(45), nullable=True)  # IPv6 최대 길이
    created_at = db.Column(db.DateTime, server_default=db.func.now(), index=True)

    __table_args__ = (db.Index("ix_audit_logs_action_created", "action", "created_at"),)
