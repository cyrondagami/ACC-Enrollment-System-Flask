"""Student dashboard and enrollment workflow."""
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Enrollment, write_audit

student_bp = Blueprint("student", __name__, url_prefix="/student")

ALLOWED_SEMESTERS = {"1st Semester", "2nd Semester", "Summer"}
ALLOWED_STATUS_FOR_EDIT = {"DRAFT", "REJECTED"}


def validate_enrollment_form(form):
    """
    Validate enrollment input on the server.

    Returns a list of human-readable errors. Validation is repeated on
    the server because browser-side validation can be bypassed.
    """
    errors = []
    required = {
        "academic_year": "Academic year",
        "semester": "Semester",
        "program": "Program",
        "year_level": "Year level",
        "contact_number": "Contact number",
        "address": "Address",
    }

    for field, label in required.items():
        if not form.get(field, "").strip():
            errors.append(f"{label} is required.")

    if form.get("semester") not in ALLOWED_SEMESTERS:
        errors.append("Invalid semester.")

    if form.get("birth_date"):
        try:
            datetime.strptime(form["birth_date"], "%Y-%m-%d")
        except ValueError:
            errors.append("Birth date must be a valid date.")

    if len(form.get("contact_number", "").strip()) > 30:
        errors.append("Contact number is too long.")

    if len(form.get("address", "").strip()) > 255:
        errors.append("Address is too long.")

    return errors


def apply_form(enrollment, form):
    """Copy validated form values into an enrollment object."""
    enrollment.student_number = form.get("student_number", "").strip() or None
    enrollment.academic_year = form.get("academic_year", "").strip()
    enrollment.semester = form.get("semester", "").strip()
    enrollment.program = form.get("program", "").strip()
    enrollment.year_level = form.get("year_level", "").strip()
    enrollment.birth_date = (
        datetime.strptime(form["birth_date"], "%Y-%m-%d").date()
        if form.get("birth_date")
        else None
    )
    enrollment.contact_number = form.get("contact_number", "").strip()
    enrollment.address = form.get("address", "").strip()


@student_bp.route("")
@student_bp.route("/")
@login_required
def dashboard():
    """Show the student's enrollment applications."""
    enrollments = db.session.scalars(
        db.select(Enrollment)
        .where(Enrollment.student_id == current_user.id)
        .order_by(Enrollment.created_at.desc())
    ).all()

    return render_template("student/dashboard.html", enrollments=enrollments)


@student_bp.route("/enroll", methods=["GET", "POST"])
@login_required
def create_enrollment():
    """Create a new draft enrollment application."""
    if request.method == "POST":
        errors = validate_enrollment_form(request.form)

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            enrollment = Enrollment(student_id=current_user.id)
            apply_form(enrollment, request.form)
            db.session.add(enrollment)
            db.session.flush()
            write_audit(
                current_user.id,
                "CREATE_ENROLLMENT",
                "Enrollment",
                enrollment.id,
                "Created draft application",
            )
            try:
                db.session.commit()
                flash("Enrollment draft created.", "success")
                return redirect(url_for("student.view_enrollment", enrollment_id=enrollment.id))
            except IntegrityError:
                db.session.rollback()
                flash(
                    "You already have an enrollment application for this academic period.",
                    "danger",
                )

    return render_template("student/enrollment_form.html", enrollment=None)


@student_bp.route("/enrollment/<int:enrollment_id>")
@login_required
def view_enrollment(enrollment_id):
    """Display one enrollment owned by the logged-in student."""
    enrollment = db.session.get(Enrollment, enrollment_id)

    if not enrollment or enrollment.student_id != current_user.id:
        from flask import abort
        abort(404)

    return render_template("student/view_enrollment.html", enrollment=enrollment)


@student_bp.route("/enrollment/<int:enrollment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_enrollment(enrollment_id):
    """Edit a draft/rejected enrollment; submitted/approved records are locked."""
    enrollment = db.session.get(Enrollment, enrollment_id)

    if not enrollment or enrollment.student_id != current_user.id:
        from flask import abort
        abort(404)

    if enrollment.status not in ALLOWED_STATUS_FOR_EDIT:
        flash("This enrollment is locked and cannot be edited.", "warning")
        return redirect(url_for("student.view_enrollment", enrollment_id=enrollment.id))

    if request.method == "POST":
        errors = validate_enrollment_form(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            apply_form(enrollment, request.form)
            write_audit(
                current_user.id,
                "UPDATE_ENROLLMENT",
                "Enrollment",
                enrollment.id,
                "Updated application",
            )
            db.session.commit()
            flash("Enrollment updated.", "success")
            return redirect(url_for("student.view_enrollment", enrollment_id=enrollment.id))

    return render_template("student/enrollment_form.html", enrollment=enrollment)


@student_bp.post("/enrollment/<int:enrollment_id>/submit")
@login_required
def submit_enrollment(enrollment_id):
    """Submit a draft/rejected application for administrative review."""
    enrollment = db.session.get(Enrollment, enrollment_id)

    if not enrollment or enrollment.student_id != current_user.id:
        from flask import abort
        abort(404)

    if enrollment.status not in ALLOWED_STATUS_FOR_EDIT:
        flash("Only draft or rejected applications can be submitted.", "warning")
    else:
        enrollment.status = "SUBMITTED"
        enrollment.review_note = None
        enrollment.reviewed_by = None
        enrollment.reviewed_at = None
        write_audit(
            current_user.id,
            "SUBMIT_ENROLLMENT",
            "Enrollment",
            enrollment.id,
            "Submitted for review",
        )
        db.session.commit()
        flash("Enrollment submitted for review.", "success")

    return redirect(url_for("student.view_enrollment", enrollment_id=enrollment.id))
