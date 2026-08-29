"""Decorators and helpers for member user accounts."""

from functools import wraps

from flask import flash, g, redirect, request, session, url_for

from extensions import db
from models_user import UserAccount


def get_logged_in_user():
    """Return the active user account stored in the session."""

    user_id = session.get("user_account_id")

    if not user_id:
        return None

    user = db.session.get(UserAccount, user_id)

    if not user or not user.is_active:
        session.pop("user_account_id", None)
        session.pop("user_logged_in", None)
        session.pop("user_name", None)
        return None

    return user


def user_login_required(view_function):
    """Allow access only to an authenticated active user account."""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        user = get_logged_in_user()

        if not user:
            flash("Please log in to access your account.", "warning")
            return redirect(
                url_for(
                    "user_auth.login",
                    next=request.path,
                )
            )

        g.user_account = user
        return view_function(*args, **kwargs)

    return wrapped_view

