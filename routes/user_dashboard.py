"""Dashboard routes for authenticated directory users."""

from flask import Blueprint, g, render_template

from utils.user_decorators import user_login_required


user_dashboard_bp = Blueprint(
    "user_dashboard",
    __name__,
    url_prefix="/account",
)


@user_dashboard_bp.route("/dashboard")
@user_login_required
def dashboard():
    user = g.user_account
    member = user.member

    return render_template(
        "user/dashboard.html",
        user=user,
        member=member,
    )
