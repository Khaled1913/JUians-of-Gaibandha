"""User registration, login and logout routes."""

import re
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func, or_

from extensions import db
from models_user import UserAccount


user_auth_bp = Blueprint(
    "user_auth",
    __name__,
    url_prefix="/account",
)


EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def _normalize_email(value):
    return str(value or "").strip().lower()


def _normalize_phone(value):
    """Normalize common Bangladeshi phone-number formatting."""

    value = str(value or "").strip()

    if not value:
        return ""

    leading_plus = value.startswith("+")
    digits = re.sub(r"\D", "", value)

    if digits.startswith("880"):
        return f"+{digits}"

    if leading_plus:
        return f"+{digits}"

    return digits


def _safe_next_url(value):
    """Allow only local redirect paths."""

    value = str(value or "").strip()

    if value.startswith("/") and not value.startswith("//"):
        return value

    return None


def _current_user():
    user_id = session.get("user_account_id")

    if not user_id:
        return None

    user = db.session.get(
        UserAccount,
        user_id,
    )

    if not user or not user.is_active:
        session.pop("user_account_id", None)
        session.pop("user_logged_in", None)
        session.pop("user_name", None)

        return None

    return user


@user_auth_bp.app_context_processor
def inject_user_account():
    return {
        "current_user_account": _current_user(),
    }


@user_auth_bp.route(
    "/register",
    methods=["GET", "POST"],
)
def register():
    if _current_user():
        flash(
            "You are already logged in.",
            "info",
        )

        return redirect(
            url_for("user_dashboard.dashboard")
        )

    if request.method == "GET":
        return render_template(
            "user/register.html"
        )

    full_name = str(
        request.form.get(
            "full_name",
            "",
        )
    ).strip()

    email = _normalize_email(
        request.form.get("email")
    )

    phone = _normalize_phone(
        request.form.get("phone")
    )

    password = str(
        request.form.get(
            "password",
            "",
        )
    )

    confirm_password = str(
        request.form.get(
            "confirm_password",
            "",
        )
    )

    accepted_terms = (
        request.form.get("accepted_terms")
        == "yes"
    )

    if not full_name:
        flash(
            "Full name is required.",
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 400

    if len(full_name) > 100:
        flash(
            "Full name is too long.",
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 400

    if (
        not email
        or not EMAIL_PATTERN.match(email)
    ):
        flash(
            "Please enter a valid email address.",
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 400

    if (
        not phone
        or len(phone) < 10
        or len(phone) > 16
    ):
        flash(
            "Please enter a valid phone number.",
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 400

    if len(password) < 8:
        flash(
            "Password must contain at least 8 characters.",
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 400

    if password != confirm_password:
        flash(
            "Password confirmation does not match.",
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 400

    if not accepted_terms:
        flash(
            "You must agree to the account terms.",
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 400

    duplicate = UserAccount.query.filter(
        or_(
            func.lower(
                UserAccount.email
            ) == email,
            UserAccount.phone == phone,
        )
    ).first()

    if duplicate:
        flash(
            (
                "An account already exists with "
                "this email or phone number."
            ),
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 409

    user = UserAccount(
        full_name=full_name,
        email=email,
        phone=phone,
        is_verified=False,
        is_active=True,
    )

    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()

    except Exception as exc:
        db.session.rollback()

        print(
            f"User registration failed: {exc}"
        )

        flash(
            (
                "Account creation failed. "
                "Please try again."
            ),
            "danger",
        )

        return render_template(
            "user/register.html"
        ), 500

    flash(
        (
            "Account created successfully. "
            "You can now log in."
        ),
        "success",
    )

    return redirect(
        url_for("user_auth.login")
    )


@user_auth_bp.route(
    "/login",
    methods=["GET", "POST"],
)
def login():
    if _current_user():
        flash(
            "You are already logged in.",
            "info",
        )

        return redirect(
            url_for("user_dashboard.dashboard")
        )

    next_url = _safe_next_url(
        request.args.get("next")
        or request.form.get("next")
    )

    if request.method == "GET":
        return render_template(
            "user/login.html",
            next_url=next_url,
        )

    identifier = str(
        request.form.get(
            "identifier",
            "",
        )
    ).strip()

    password = str(
        request.form.get(
            "password",
            "",
        )
    )

    if not identifier or not password:
        flash(
            (
                "Email/phone and password "
                "are required."
            ),
            "danger",
        )

        return render_template(
            "user/login.html",
            next_url=next_url,
        ), 400

    email_identifier = _normalize_email(
        identifier
    )

    phone_identifier = _normalize_phone(
        identifier
    )

    user = UserAccount.query.filter(
        or_(
            func.lower(
                UserAccount.email
            ) == email_identifier,
            UserAccount.phone
            == phone_identifier,
        )
    ).first()

    if (
        not user
        or not user.check_password(password)
    ):
        flash(
            (
                "Invalid email/phone "
                "or password."
            ),
            "danger",
        )

        return render_template(
            "user/login.html",
            next_url=next_url,
        ), 401

    if not user.is_active:
        flash(
            (
                "This account is "
                "currently disabled."
            ),
            "danger",
        )

        return render_template(
            "user/login.html",
            next_url=next_url,
        ), 403

    # Remove only old user-account session values.
    # Administrator session values remain unchanged.
    session.pop(
        "user_account_id",
        None,
    )

    session.pop(
        "user_logged_in",
        None,
    )

    session.pop(
        "user_name",
        None,
    )

    session["user_account_id"] = user.id
    session["user_logged_in"] = True
    session["user_name"] = user.full_name
    session.permanent = True

    user.last_login = datetime.utcnow()

    try:
        db.session.commit()

    except Exception as exc:
        db.session.rollback()

        print(
            f"User last-login update failed: {exc}"
        )

    flash(
        f"Welcome, {user.full_name}!",
        "success",
    )

    return redirect(
        next_url
        or url_for(
            "user_dashboard.dashboard"
        )
    )


@user_auth_bp.route(
    "/logout",
    methods=["GET", "POST"],
)
def logout():
    session.pop(
        "user_account_id",
        None,
    )

    session.pop(
        "user_logged_in",
        None,
    )

    session.pop(
        "user_name",
        None,
    )

    flash(
        (
            "You have been logged "
            "out successfully."
        ),
        "success",
    )

    return redirect(
        url_for("home.home")
    )