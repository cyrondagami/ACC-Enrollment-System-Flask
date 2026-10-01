
"""Database models for users, enrollment applications, and audit events."""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db, login_manager


def utcnow():
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """System account with one of the supported RBAC roles."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(30),
        nullable=False,
        default="student",
        index=True
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )

    # IMPORTANT:
    # Enrollment has TWO foreign keys pointing to users.id:
    # student_id and reviewed_by.
    # We explicitly tell SQLAlchemy that this relationship
    # uses student_id.
    enrollments = db.relationship(
        "Enrollment",
        foreign_keys="Enrollment.student_id",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        """Hash and store a password; never store plaintext passwords."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password against the stored secure hash."""
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    """Load a user from the database for Flask-Login sessions."""
    return db.session.get(User, int(user_id))


class Enrollment(db.Model):
    """Student enrollment application and its review state."""

    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    student_number = db.Column(
        db.String(50),
        nullable=True,
        index=True
    )

    academic_year = db.Column(
        db.String(20),
        nullable=False
    )

    semester = db.Column(
        db.String(30),
        nullable=False
    )

    program = db.Column(
        db.String(100),
        nullable=False
    )

    year_level = db.Column(
        db.String(30),
        nullable=False
    )

    birth_date = db.Column(
        db.Date,
        nullable=True
    )

    contact_number = db.Column(
        db.String(30),
        nullable=False
    )

    address = db.Column(
        db.String(255),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="DRAFT",
        index=True
    )

    review_note = db.Column(
        db.Text,
        nullable=True
    )

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    reviewed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False
    )

    # Relationship to the student who owns the enrollment.
    student = db.relationship(
        "User",
        foreign_keys=[student_id],
        back_populates="enrollments",
    )

    # Relationship to the admin/user who reviewed the enrollment.
    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "academic_year",
            "semester",
            name="uq_student_academic_period",
        ),
    )


class AuditLog(db.Model):
    """Immutable-ish record of important administrative actions."""

    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    target_type = db.Column(
        db.String(50),
        nullable=False
    )

    target_id = db.Column(
        db.Integer,
        nullable=True
    )

    details = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )

    actor = db.relationship(
        "User",
        foreign_keys=[actor_id]
    )


def write_audit(
    actor_id,
    action,
    target_type,
    target_id=None,
    details=None
):
    """Create an audit record for a security/business-sensitive action."""

    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )

    db.session.add(entry)

