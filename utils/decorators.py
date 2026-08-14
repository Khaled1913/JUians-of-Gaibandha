"""
=====================================================
JUians of Gaibandha Portal
Decorators
Version 1.0
Developer : Khaled Mahmud Jon
=====================================================
"""

from functools import wraps

from flask import (
    session,
    flash,
    redirect,
    url_for
)


# =====================================================
# LOGIN REQUIRED
# =====================================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "admin_id" not in session:

            flash(

                "Please login first.",

                "warning"

            )

            return redirect(

                url_for("auth.login")

            )

        return function(

            *args,

            **kwargs

        )

    return decorated_function


# =====================================================
# ADMIN REQUIRED
# =====================================================

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "admin_id" not in session:

            flash(

                "Administrator login required.",

                "danger"

            )

            return redirect(

                url_for("auth.login")

            )

        return function(

            *args,

            **kwargs

        )

    return decorated_function


# =====================================================
# SUPER ADMIN REQUIRED
# =====================================================

def super_admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "admin_id" not in session:

            flash(

                "Please login first.",

                "warning"

            )

            return redirect(

                url_for("auth.login")

            )

        if session.get("admin_role") != "Super Admin":

            flash(

                "You do not have permission to access this page.",

                "danger"

            )

            return redirect(

                url_for("admin.admin_dashboard")

            )

        return function(

            *args,

            **kwargs

        )

    return decorated_function