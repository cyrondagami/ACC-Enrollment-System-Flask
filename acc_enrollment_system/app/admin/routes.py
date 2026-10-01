"""Administrative enrollment and user management routes."""
from datetime import datetime, timezone
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..decorators import roles_required
from ..extensions import db
from ..models import AuditLog, Enrollment, User, write_audit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("")
@admin_bp.get("/")
@login_required
@roles_required("admin", "super_admin")
def dashboard():
    """Show enrollment statistics and recent applications."""
    stats = {
        "total": db.session.scalar(db.select(func.count(Enrollment.id))) or 0,
        "submitted": db.session.scalar(
            db.select(func.count(Enrollment.id)).where(Enrollment.status == "SUBMITTED")
        ) or 0,
        "approved": db.session.scalar(
            db.select(func.count(Enrollment.id)).where(Enrollment.status == "APPROVED")
        ) or 0,
        "rejected": db.session.scalar(
            db.select(func.count(Enrollment.id)).where(Enrollment.status == "REJECTED")
        ) or 0,
    }

    enrollments = db.session.scalars(
        db.select(Enrollment).order_by(Enrollment.created_at.desc()).limit(20)
    ).all()

    return render_template("admin/dashboard.html", stats=stats, enrollments=enrollments)


@admin_bp.get("/enrollments")
@login_required
@roles_required("admin", "super_admin")
def enrollments():
    """List enrollment applications, optionally filtered by status."""
    status = request.args.get("status", "").upper()
    query = db.select(Enrollment).order_by(Enrollment.created_at.desc())

    if status in {"DRAFT", "SUBMITTED", "APPROVED", "REJECTED"}:
        query = query.where(Enrollment.status == status)

    records = db.session.scalars(query).all()
    return render_template("admin/enrollments.html", enrollments=records, status=status)


@admin_bp.route("/enrollment/<int:enrollment_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin", "super_admin")
def review_enrollment(enrollment_id):
    """Review a submitted application and approve or reject it."""
    enrollment = db.session.get(Enrollment, enrollment_id)
    if not enrollment:
        abort(404)

    if request.method == "POST":
        action = request.form.get("action")
        note = request.form.get("review_note", "").strip()

        if enrollment.status != "SUBMITTED":
            flash("Only submitted applications can be reviewed.", "warning")
        elif action not in {"approve", "reject"}:
            flash("Invalid review action.", "danger")
        elif action == "reject" and not note:
            flash("A rejection reason is required.", "danger")
        else:
            enrollment.status = "APPROVED" if action == "approve" else "REJECTED"
            enrollment.review_note = note or None
            enrollment.reviewed_by = current_user.id
            enrollment.reviewed_at = datetime.now(timezone.utc)

            write_audit(
                current_user.id,
                "REVIEW_ENROLLMENT",
                "Enrollment",
                enrollment.id,
                f"Status changed to {enrollment.status}",
            )
            db.session.commit()
            flash(f"Application {enrollment.status.lower()}.", "success")
            return redirect(url_for("admin.review_enrollment", enrollment_id=enrollment.id))

    return render_template("admin/review_enrollment.html", enrollment=enrollment)


@admin_bp.get("/users")
@login_required
@roles_required("super_admin")
def users():
    """List system accounts; restricted to the super administrator."""
    records = db.session.scalars(
        db.select(User).order_by(User.created_at.desc())
    ).all()
    return render_template("admin/users.html", users=records)


@admin_bp.post("/users/<int:user_id>/toggle")
@login_required
@roles_required("super_admin")
def toggle_user(user_id):
    """Activate/deactivate a user while preventing self-deactivation."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.users"))

    user.is_active = not user.is_active
    write_audit(
        current_user.id,
        "TOGGLE_USER",
        "User",
        user.id,
        f"is_active={user.is_active}",
    )
    db.session.commit()
    flash("User status updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.post("/users/<int:user_id>/role")
@login_required
@roles_required("super_admin")
def change_role(user_id):
    """Change a user's RBAC role with strict server-side allowlisting."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    new_role = request.form.get("role")
    if new_role not in {"student", "admin", "super_admin"}:
        flash("Invalid role.", "danger")
        return redirect(url_for("admin.users"))

    if user.id == current_user.id and new_role != "super_admin":
        flash("You cannot remove your own super-admin role.", "danger")
        return redirect(url_for("admin.users"))

    user.role = new_role
    write_audit(
        current_user.id,
        "CHANGE_ROLE",
        "User",
        user.id,
        f"role={new_role}",
    )
    db.session.commit()
    flash("User role updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.get("/audit")
@login_required
@roles_required("super_admin")
def audit():
    """Display recent audit events to the super administrator."""
    logs = db.session.scalars(
        db.select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)
    ).all()
    return render_template("admin/audit.html", logs=logs)
