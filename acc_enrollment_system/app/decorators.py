"""Reusable authorization decorators."""
from functools import wraps
from flask import abort
from flask_login import current_user


def roles_required(*roles):
    """
    Restrict a route to one or more roles.

    Authentication is handled separately by @login_required.
    This decorator checks the authenticated user's role.
    """
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
