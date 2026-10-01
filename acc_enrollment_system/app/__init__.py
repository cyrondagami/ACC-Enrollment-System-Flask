"""Application factory for the ACC Enrollment System."""
from flask import Flask, redirect, url_for
from .config import Config
from .extensions import db, login_manager, csrf


def create_app(config_class=Config):
    """Create and configure a Flask application instance."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Keep SQLite files in Flask's instance directory.
    import os
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints so each feature stays modular.
    from .auth.routes import auth_bp
    from .student.routes import student_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    with app.app_context():
        db.create_all()

    return app