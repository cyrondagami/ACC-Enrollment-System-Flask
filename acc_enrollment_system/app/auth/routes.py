"""Authentication routes: login, registration, and logout."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func

from ..extensions import db
from ..models import User, write_audit

auth_bp = Blueprint("auth", __name__, url_prefix="/")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a student account with server-side validation."""
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(full_name) < 2:
            flash("Please enter your complete name.", "danger")
        elif "@" not in email or len(email) > 255:
            flash("Please enter a valid email address.", "danger")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif db.session.scalar(
            db.select(User).where(func.lower(User.email) == email)
        ):
            flash("An account with that email already exists.", "danger")
        else:
            user = User(full_name=full_name, email=email, role="student")
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            write_audit(user.id, "REGISTER", "User", user.id, "Student registration")
            db.session.commit()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user and create a Flask-Login session."""
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.session.scalar(
            db.select(User).where(func.lower(User.email) == email)
        )

        if not user or not user.is_active or not user.check_password(password):
            # Do not reveal whether the email exists.
            flash("Invalid email or password.", "danger")
        else:
            login_user(user)
            write_audit(user.id, "LOGIN", "User", user.id, "Successful login")
            db.session.commit()

            next_url = request.args.get("next")
            # Only allow local paths; prevents open redirect attacks.
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)

            return redirect(url_for("student.dashboard"))

    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    """End the authenticated user's session."""
    if current_user.is_authenticated:
        write_audit(current_user.id, "LOGOUT", "User", current_user.id, "Logout")
        db.session.commit()
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
