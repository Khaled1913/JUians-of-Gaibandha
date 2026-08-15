"""
============================================================
JUians of Gaibandha
Authentication Routes
============================================================
"""

from datetime import datetime, date
import secrets

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from sqlalchemy import (
    or_,
    func
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from extensions import db
from models import Admin
from utils.validators import validate_login


# ============================================================
# BLUEPRINT
# ============================================================

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


# ============================================================
# HELPER
# GET LOGGED-IN ADMIN
# ============================================================

def _session_admin():

    admin_id = session.get(
        "admin_id"
    )

    if not admin_id:
        return None

    return db.session.get(
        Admin,
        admin_id
    )


# ============================================================
# HELPER
# CURRENT ADMIN ACCOUNT CHECK
# ============================================================

def _is_current_active_admin(admin):

    if admin is None:
        return False

    return bool(
        admin.is_active
        and admin.is_current
    )


# ============================================================
# HELPER
# NORMALIZE LOGIN IDENTIFIER
# ============================================================
#
# PostgreSQL string comparison is case-sensitive.
#
# This helper ensures:
#
# Khaled
# khaled
# KHALED
#
# can all refer to the same administrator username.
#
# It also applies to email addresses.
# ============================================================

def _normalize_identifier(value):

    return (
        value
        or ""
    ).strip().lower()


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # --------------------------------------------------------
    # Already Logged In
    # --------------------------------------------------------

    if session.get("admin_id"):

        existing_admin = (
            _session_admin()
        )

        if _is_current_active_admin(
            existing_admin
        ):

            return redirect(
                url_for(
                    "admin.dashboard"
                )
            )

        # ----------------------------------------------------
        # Invalid / Previous Session
        # ----------------------------------------------------

        session.clear()

    # --------------------------------------------------------
    # POST REQUEST
    # --------------------------------------------------------

    if request.method == "POST":

        username_or_email = (
            request.form.get(
                "username",
                ""
            ).strip()
        )

        password = request.form.get(
            "password",
            ""
        )

        # ----------------------------------------------------
        # Basic Validation
        # ----------------------------------------------------

        error = validate_login(
            username_or_email,
            password
        )

        if error:

            flash(
                error,
                "danger"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        # ----------------------------------------------------
        # Normalize Identifier
        # ----------------------------------------------------

        normalized_identifier = (
            _normalize_identifier(
                username_or_email
            )
        )

        # ====================================================
        # FIND ADMIN
        #
        # Login supported by:
        #
        # 1. Username
        # 2. Email
        #
        # Comparison is case-insensitive.
        # ====================================================

        admin = (
            Admin.query
            .filter(
                or_(
                    func.lower(
                        Admin.username
                    )
                    == normalized_identifier,

                    func.lower(
                        Admin.email
                    )
                    == normalized_identifier
                )
            )
            .first()
        )

        # ----------------------------------------------------
        # Admin Not Found
        # ----------------------------------------------------

        if admin is None:

            flash(
                "Invalid username or password.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        # ----------------------------------------------------
        # Password Verification
        # ----------------------------------------------------

        try:

            password_valid = (
                check_password_hash(
                    admin.password,
                    password
                )
            )

        except Exception:

            password_valid = False

        if not password_valid:

            flash(
                "Invalid username or password.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        # ----------------------------------------------------
        # Account Disabled
        # ----------------------------------------------------

        if not admin.is_active:

            flash(
                (
                    "This administrator account is no longer active. "
                    "Only the current administrator can access "
                    "the administration portal."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        # ----------------------------------------------------
        # Previous Administrator
        # ----------------------------------------------------

        if not admin.is_current:

            flash(
                (
                    "Your administrator term has ended. "
                    "Only the current administrator can log in."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        # ====================================================
        # LOGIN SUCCESS
        # ====================================================

        try:

            # ------------------------------------------------
            # Update Last Login
            # ------------------------------------------------

            admin.last_login = (
                datetime.utcnow()
            )

            db.session.commit()

        except Exception as exc:

            db.session.rollback()

            print(
                f"Last login update error: {exc}"
            )

        # ----------------------------------------------------
        # Clear Previous Session
        # ----------------------------------------------------

        session.clear()

        # ----------------------------------------------------
        # Enable Permanent Session
        # ----------------------------------------------------

        session.permanent = True

        # ----------------------------------------------------
        # Create Admin Session
        # ----------------------------------------------------

        session["logged_in"] = True

        session["admin_id"] = (
            admin.id
        )

        session["admin_username"] = (
            admin.username
        )

        session["admin_name"] = (
            admin.full_name
        )

        session["admin_role"] = (
            admin.role
        )

        session["admin_term_year"] = (
            admin.term_year
        )

        # ----------------------------------------------------
        # Success Message
        # ----------------------------------------------------

        if admin.term_year:

            flash(
                (
                    f"Login successful. Welcome back, "
                    f"{admin.full_name}. "
                    f"You are the current administrator "
                    f"for {admin.term_year}."
                ),
                "success"
            )

        else:

            flash(
                (
                    f"Login successful. "
                    f"Welcome back, "
                    f"{admin.full_name}!"
                ),
                "success"
            )

        # ----------------------------------------------------
        # Redirect To Admin Dashboard
        # ----------------------------------------------------

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # ========================================================
    # GET REQUEST
    # ========================================================

    return render_template(
        "auth/login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route(
    "/logout"
)
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for(
            "auth.login"
        )
    )


# ============================================================
# CREATE FIRST ADMIN
# ============================================================
#
# IMPORTANT:
#
# This route is intended primarily for first-time
# database setup.
#
# If the database contains no administrator,
# the first administrator can be created here.
#
# Once an administrator exists, additional
# administrators must be managed through:
#
#     admin.create_administrator
#
# ============================================================

@auth_bp.route(
    "/create-admin",
    methods=["GET", "POST"]
)
def create_admin():

    admin_count = (
        Admin.query.count()
    )

    # --------------------------------------------------------
    # Existing Admin System
    # --------------------------------------------------------

    if admin_count > 0:

        current_session_admin = (
            _session_admin()
        )

        # ----------------------------------------------------
        # Not Logged In
        # ----------------------------------------------------

        if not current_session_admin:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        # ----------------------------------------------------
        # Session Admin Is Not Current
        # ----------------------------------------------------

        if not _is_current_active_admin(
            current_session_admin
        ):

            session.clear()

            flash(
                (
                    "Your administrator session "
                    "is no longer active."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        # ----------------------------------------------------
        # Use Yearly Administrator Management
        # ----------------------------------------------------

        flash(
            (
                "Use the Manage Administrators section "
                "to add a new yearly administrator."
            ),
            "info"
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    # ========================================================
    # POST — FIRST ADMIN ONLY
    # ========================================================

    if request.method == "POST":

        full_name = (
            request.form.get(
                "full_name",
                ""
            ).strip()
        )

        username = (
            request.form.get(
                "username",
                ""
            ).strip()
        )

        email = (
            request.form.get(
                "email",
                ""
            ).strip()
        )

        password = (
            request.form.get(
                "password",
                ""
            )
        )

        confirm_password = (
            request.form.get(
                "confirm_password",
                ""
            )
        )

        # ----------------------------------------------------
        # Full Name
        # ----------------------------------------------------

        if not full_name:

            flash(
                "Full name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

        # ----------------------------------------------------
        # Username
        # ----------------------------------------------------

        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

        # ----------------------------------------------------
        # Email
        # ----------------------------------------------------

        if not email:

            flash(
                "Email is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

        # ----------------------------------------------------
        # Password
        # ----------------------------------------------------

        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

        # ----------------------------------------------------
        # Password Length
        # ----------------------------------------------------

        if len(password) < 6:

            flash(
                (
                    "Password must be at least "
                    "6 characters."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

        # ----------------------------------------------------
        # Confirm Password
        # ----------------------------------------------------

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

        # ----------------------------------------------------
        # Normalize Username / Email
        # ----------------------------------------------------

        normalized_username = (
            _normalize_identifier(
                username
            )
        )

        normalized_email = (
            _normalize_identifier(
                email
            )
        )

        # ----------------------------------------------------
        # Duplicate Username
        # ----------------------------------------------------

        existing_username = (
            Admin.query
            .filter(
                func.lower(
                    Admin.username
                )
                == normalized_username
            )
            .first()
        )

        if existing_username:

            flash(
                "Username already exists.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

        # ----------------------------------------------------
        # Duplicate Email
        # ----------------------------------------------------

        existing_email = (
            Admin.query
            .filter(
                func.lower(
                    Admin.email
                )
                == normalized_email
            )
            .first()
        )

        if existing_email:

            flash(
                "Email already exists.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

        # ====================================================
        # CREATE INITIAL CURRENT ADMIN
        # ====================================================

        current_year = (
            date.today().year
        )

        new_admin = Admin(

            full_name=full_name,

            username=normalized_username,

            email=normalized_email,

            password=(
                generate_password_hash(
                    password
                )
            ),

            role="Admin",

            is_active=True,

            is_current=True
        )

        new_admin.set_yearly_term(
            current_year
        )

        # ----------------------------------------------------
        # Save Admin
        # ----------------------------------------------------

        try:

            db.session.add(
                new_admin
            )

            db.session.commit()

            flash(
                (
                    f"Administrator created successfully "
                    f"for {current_year}. "
                    "You can now login."
                ),
                "success"
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        except Exception as exc:

            db.session.rollback()

            print(
                f"Admin creation error: {exc}"
            )

            flash(
                (
                    "Failed to create administrator. "
                    "Please try again."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "auth.create_admin"
                )
            )

    # ========================================================
    # GET
    # ========================================================

    return render_template(
        "auth/create_admin.html"
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@auth_bp.route(
    "/change-password",
    methods=["GET", "POST"]
)
def change_password():

    # --------------------------------------------------------
    # Login Check
    # --------------------------------------------------------

    if not session.get(
        "admin_id"
    ):

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # Get Current Admin
    # --------------------------------------------------------

    admin = (
        _session_admin()
    )

    if admin is None:

        session.clear()

        flash(
            "Administrator account not found.",
            "danger"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # Current Administrator Validation
    # --------------------------------------------------------

    if not admin.is_current:

        session.clear()

        flash(
            (
                "Your administrator term has ended. "
                "Password changes are available only "
                "to the current administrator."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if not admin.is_active:

        session.clear()

        flash(
            (
                "Your administrator account "
                "has been disabled."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        current_password = (
            request.form.get(
                "current_password",
                ""
            )
        )

        new_password = (
            request.form.get(
                "new_password",
                ""
            )
        )

        confirm_password = (
            request.form.get(
                "confirm_password",
                ""
            )
        )

        # ----------------------------------------------------
        # Current Password
        # ----------------------------------------------------

        try:

            current_valid = (
                check_password_hash(
                    admin.password,
                    current_password
                )
            )

        except Exception:

            current_valid = False

        if not current_valid:

            flash(
                "Current password is incorrect.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.change_password"
                )
            )

        # ----------------------------------------------------
        # New Password Length
        # ----------------------------------------------------

        if len(new_password) < 6:

            flash(
                (
                    "Password must be at least "
                    "6 characters."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "auth.change_password"
                )
            )

        # ----------------------------------------------------
        # Confirm Password
        # ----------------------------------------------------

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.change_password"
                )
            )

        # ----------------------------------------------------
        # Same Password
        # ----------------------------------------------------

        try:

            same_password = (
                check_password_hash(
                    admin.password,
                    new_password
                )
            )

        except Exception:

            same_password = False

        if same_password:

            flash(
                (
                    "New password cannot be the same "
                    "as the current password."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "auth.change_password"
                )
            )

        # ----------------------------------------------------
        # Update Password
        # ----------------------------------------------------

        admin.password = (
            generate_password_hash(
                new_password
            )
        )

        admin.updated_at = (
            datetime.utcnow()
        )

        try:

            db.session.commit()

        except Exception as exc:

            db.session.rollback()

            print(
                f"Password change error: {exc}"
            )

            flash(
                "Failed to change password.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.change_password"
                )
            )

        flash(
            "Password changed successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # ========================================================
    # GET
    # ========================================================

    return render_template(
        "auth/change_password.html",
        admin=admin
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        username_or_email = (
            request.form.get(
                "username",
                ""
            ).strip()
        )

        if not username_or_email:

            flash(
                (
                    "Username or email "
                    "is required."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "auth.forgot_password"
                )
            )

        # ----------------------------------------------------
        # Normalize Identifier
        # ----------------------------------------------------

        normalized_identifier = (
            _normalize_identifier(
                username_or_email
            )
        )

        # ----------------------------------------------------
        # Find Admin
        # ----------------------------------------------------

        admin = (
            Admin.query
            .filter(
                or_(
                    func.lower(
                        Admin.username
                    )
                    == normalized_identifier,

                    func.lower(
                        Admin.email
                    )
                    == normalized_identifier
                )
            )
            .first()
        )

        if admin is None:

            flash(
                "Administrator account not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.forgot_password"
                )
            )

        # ----------------------------------------------------
        # Current Administrator Check
        # ----------------------------------------------------

        if not admin.is_current:

            flash(
                (
                    "Password recovery is available only "
                    "for the current administrator."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "auth.forgot_password"
                )
            )

        # ----------------------------------------------------
        # Active Check
        # ----------------------------------------------------

        if not admin.is_active:

            flash(
                (
                    "This administrator account "
                    "is disabled."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "auth.forgot_password"
                )
            )

        # ----------------------------------------------------
        # Generate Reset Token
        # ----------------------------------------------------

        token = (
            secrets.token_urlsafe(
                32
            )
        )

        session["reset_token"] = (
            token
        )

        session["reset_admin_id"] = (
            admin.id
        )

        flash(
            (
                "Password reset request "
                "created successfully."
            ),
            "success"
        )

        return redirect(
            url_for(
                "auth.reset_password",
                token=token
            )
        )

    # ========================================================
    # GET
    # ========================================================

    return render_template(
        "auth/forgot_password.html"
    )


# ============================================================
# RESET PASSWORD
# ============================================================

@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    saved_token = (
        session.get(
            "reset_token"
        )
    )

    admin_id = (
        session.get(
            "reset_admin_id"
        )
    )

    # --------------------------------------------------------
    # Validate Token
    # --------------------------------------------------------

    if (
        not saved_token
        or
        not secrets.compare_digest(
            token,
            saved_token
        )
    ):

        flash(
            "Invalid or expired reset link.",
            "danger"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # Get Admin
    # --------------------------------------------------------

    admin = db.session.get(
        Admin,
        admin_id
    )

    if admin is None:

        session.pop(
            "reset_token",
            None
        )

        session.pop(
            "reset_admin_id",
            None
        )

        flash(
            "Administrator account not found.",
            "danger"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # Current Administrator Check
    # --------------------------------------------------------

    if (
        not admin.is_current
        or
        not admin.is_active
    ):

        session.pop(
            "reset_token",
            None
        )

        session.pop(
            "reset_admin_id",
            None
        )

        flash(
            (
                "This administrator account is no longer "
                "authorized to reset its password."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        password = (
            request.form.get(
                "password",
                ""
            )
        )

        confirm_password = (
            request.form.get(
                "confirm_password",
                ""
            )
        )

        # ----------------------------------------------------
        # Password Length
        # ----------------------------------------------------

        if len(password) < 6:

            flash(
                (
                    "Password must be at least "
                    "6 characters."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        # ----------------------------------------------------
        # Password Match
        # ----------------------------------------------------

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        # ----------------------------------------------------
        # Same Password Protection
        # ----------------------------------------------------

        try:

            same_password = (
                check_password_hash(
                    admin.password,
                    password
                )
            )

        except Exception:

            same_password = False

        if same_password:

            flash(
                (
                    "New password cannot be the same "
                    "as your current password."
                ),
                "warning"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        # ----------------------------------------------------
        # Update Password
        # ----------------------------------------------------

        admin.password = (
            generate_password_hash(
                password
            )
        )

        admin.updated_at = (
            datetime.utcnow()
        )

        try:

            db.session.commit()

        except Exception as exc:

            db.session.rollback()

            print(
                f"Password reset error: {exc}"
            )

            flash(
                "Failed to reset password.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        # ----------------------------------------------------
        # Remove Reset Session
        # ----------------------------------------------------

        session.pop(
            "reset_token",
            None
        )

        session.pop(
            "reset_admin_id",
            None
        )

        flash(
            "Password reset successful.",
            "success"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # ========================================================
    # GET
    # ========================================================

    return render_template(
        "auth/reset_password.html",
        token=token,
        admin=admin
    )


# ============================================================
# ADMIN PROFILE
# ============================================================

@auth_bp.route(
    "/profile"
)
def profile():

    # --------------------------------------------------------
    # Login Check
    # --------------------------------------------------------

    if not session.get(
        "admin_id"
    ):

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # Get Admin
    # --------------------------------------------------------

    admin = (
        _session_admin()
    )

    if admin is None:

        session.clear()

        flash(
            "Administrator account not found.",
            "danger"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # Current / Active Validation
    # --------------------------------------------------------

    if not _is_current_active_admin(
        admin
    ):

        session.clear()

        flash(
            (
                "Your administrator session "
                "is no longer active."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    return render_template(
        "auth/profile.html",
        admin=admin
    )


# ============================================================
# CURRENT ADMIN
# ============================================================

@auth_bp.route(
    "/me"
)
def current_admin():

    admin_id = (
        session.get(
            "admin_id"
        )
    )

    if not admin_id:

        return {
            "logged_in": False
        }

    admin = db.session.get(
        Admin,
        admin_id
    )

    if admin is None:

        session.clear()

        return {
            "logged_in": False
        }

    # --------------------------------------------------------
    # Current / Active Check
    # --------------------------------------------------------

    if not _is_current_active_admin(
        admin
    ):

        session.clear()

        return {

            "logged_in": False,

            "reason": (
                "Administrator term inactive"
            )
        }

    return {

        "logged_in": True,

        "id": admin.id,

        "full_name": (
            admin.full_name
        ),

        "username": (
            admin.username
        ),

        "email": (
            admin.email
        ),

        "role": (
            admin.role
        ),

        "is_active": (
            admin.is_active
        ),

        "is_current": (
            admin.is_current
        ),

        "term_year": (
            admin.term_year
        ),

        "term_start": (
            admin.term_start.isoformat()
            if admin.term_start
            else None
        ),

        "term_end": (
            admin.term_end.isoformat()
            if admin.term_end
            else None
        )
    }


# ============================================================
# ADMIN SESSION VALIDATION
# ============================================================
#
# This runs before every request.
#
# It protects the project if:
#
# - Administrator record is deleted
# - Administrator becomes inactive
# - Administrator is replaced during yearly handover
#
# ============================================================

@auth_bp.before_app_request
def check_admin_session():

    admin_id = (
        session.get(
            "admin_id"
        )
    )

    if not admin_id:
        return

    admin = db.session.get(
        Admin,
        admin_id
    )

    # --------------------------------------------------------
    # Admin Deleted
    # --------------------------------------------------------

    if admin is None:

        session.clear()

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # Admin Disabled
    # --------------------------------------------------------

    if not admin.is_active:

        session.clear()

        flash(
            (
                "Your administrator account "
                "has been disabled."
            ),
            "danger"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    # --------------------------------------------------------
    # Administrator Term Ended
    # --------------------------------------------------------

    if not admin.is_current:

        session.clear()

        flash(
            (
                "Your administrator term has ended. "
                "Please contact the current administrator "
                "if you believe this is an error."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )


# ============================================================
# ADMIN CONTEXT PROCESSOR
# ============================================================

@auth_bp.app_context_processor
def inject_admin():

    return {

        "current_admin": {

            "id": session.get(
                "admin_id"
            ),

            "username": session.get(
                "admin_username"
            ),

            "name": session.get(
                "admin_name"
            ),

            "role": session.get(
                "admin_role"
            ),

            "term_year": session.get(
                "admin_term_year"
            ),

            "logged_in": session.get(
                "logged_in",
                False
            )

        }

    }


# ============================================================
# END OF FILE
# ============================================================