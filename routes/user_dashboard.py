"""Dashboard and self-service routes for directory users."""

import re

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import func, or_

from extensions import db
from models import Information
from models_user import (
    MemberEditRequest,
    ProfileClaimRequest,
    UserAccount,
)
from services.upload_service import (
    delete_photo,
    upload_photo,
)
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

    latest_request = (
        MemberEditRequest.query
        .filter_by(user_id=user.id)
        .order_by(MemberEditRequest.created_at.desc())
        .first()
    )

    latest_claim = (
        ProfileClaimRequest.query
        .filter_by(user_id=user.id)
        .order_by(ProfileClaimRequest.created_at.desc())
        .first()
    )

    return render_template(
        "user/dashboard.html",
        user=user,
        member=member,
        latest_request=latest_request,
        latest_claim=latest_claim,
    )


def _phone_variants(phone):
    """Return common local and international BD phone forms."""

    digits = re.sub(r"\D", "", str(phone or ""))

    if not digits:
        return set()

    variants = {digits, f"+{digits}"}

    if digits.startswith("8801"):
        local = f"0{digits[3:]}"
        variants.add(local)

    elif digits.startswith("01"):
        international = f"880{digits[1:]}"
        variants.update({international, f"+{international}"})

    return variants


def _matching_claim_profiles(user):
    """Find profiles matching the account email or phone."""

    conditions = []

    if user.email:
        conditions.append(
            func.lower(Information.email) == user.email.lower()
        )

    phone_values = _phone_variants(user.phone)

    if phone_values:
        conditions.append(Information.phone.in_(phone_values))

    if not conditions:
        return []

    return (
        Information.query
        .filter(or_(*conditions))
        .order_by(Information.full_name.asc())
        .all()
    )


@user_dashboard_bp.route(
    "/profile/claim",
    methods=["GET", "POST"],
)
@user_login_required
def claim_profile():
    user = g.user_account

    if user.member_id:
        flash("Your account already has a linked profile.", "info")
        return redirect(url_for("user_dashboard.dashboard"))

    pending_claim = ProfileClaimRequest.query.filter_by(
        user_id=user.id,
        status="Pending",
    ).first()

    matches = _matching_claim_profiles(user)

    linked_member_ids = {
        row.member_id
        for row in UserAccount.query
        .filter(UserAccount.member_id.isnot(None))
        .all()
    }

    matches = [
        member
        for member in matches
        if member.id not in linked_member_ids
    ]

    if request.method == "GET":
        return render_template(
            "user/claim_profile.html",
            user=user,
            matches=matches,
            pending_claim=pending_claim,
        )

    if pending_claim:
        flash("You already have a pending profile claim.", "warning")
        return redirect(url_for("user_dashboard.claim_profile"))

    try:
        member_id = int(request.form.get("member_id", ""))
    except (TypeError, ValueError):
        member_id = None

    selected_member = next(
        (member for member in matches if member.id == member_id),
        None,
    )

    if not selected_member:
        flash("Please select a valid matching profile.", "danger")
        return redirect(url_for("user_dashboard.claim_profile"))

    existing_owner = UserAccount.query.filter_by(
        member_id=selected_member.id
    ).first()

    if existing_owner:
        flash("This profile is already linked to an account.", "danger")
        return redirect(url_for("user_dashboard.claim_profile"))

    claim = ProfileClaimRequest(
        user_id=user.id,
        member_id=selected_member.id,
        status="Pending",
        claimant_note=str(
            request.form.get("claimant_note", "") or ""
        ).strip()[:1000] or None,
    )

    try:
        db.session.add(claim)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        print(f"Profile claim request failed: {exc}")
        flash("Your claim request could not be submitted.", "danger")
        return redirect(url_for("user_dashboard.claim_profile"))

    flash(
        "Profile claim submitted for administrator approval.",
        "success",
    )
    return redirect(url_for("user_dashboard.dashboard"))


@user_dashboard_bp.route(
    "/profile/edit",
    methods=["GET", "POST"],
)
@user_login_required
def edit_profile():
    user = g.user_account
    member = user.member

    if not member:
        flash(
            "Link or submit a directory profile before editing.",
            "warning",
        )
        return redirect(url_for("user_dashboard.dashboard"))

    pending_request = MemberEditRequest.query.filter_by(
        user_id=user.id,
        member_id=member.id,
        status="Pending",
    ).first()

    if request.method == "GET":
        form_values = (
            pending_request.get_proposed_data()
            if pending_request
            else {}
        )

        return render_template(
            "user/edit_profile.html",
            user=user,
            member=member,
            pending_request=pending_request,
            form_values=form_values,
        )

    def form_value(field, fallback=""):
        return str(
            request.form.get(field, fallback) or ""
        ).strip()

    proposed = {
        "full_name": form_value("full_name"),
        "category": form_value("category"),
        "gender": form_value("gender"),
        "date_of_birth": form_value("date_of_birth"),
        "blood_group": form_value("blood_group"),
        "phone": form_value("phone"),
        "email": form_value("email").lower(),
        "department": form_value("department"),
        "batch": form_value("batch"),
        "session": form_value("session"),
        "district": form_value("district", "Gaibandha"),
        "present_village": form_value("present_village"),
        "present_union": form_value("present_union"),
        "present_upazila": form_value("present_upazila"),
        "present_address": form_value("present_address"),
        "permanent_village": form_value("permanent_village"),
        "permanent_union": form_value("permanent_union"),
        "permanent_upazila": form_value("permanent_upazila"),
        "permanent_address": form_value("permanent_address"),
        "occupation": form_value("occupation"),
        "company": form_value("company"),
        "designation": form_value("designation"),
        "facebook": form_value("facebook"),
        "linkedin": form_value("linkedin"),
        "github": form_value("github"),
        "website": form_value("website"),
    }

    if not proposed["full_name"]:
        flash("Full name is required.", "danger")
        return redirect(url_for("user_dashboard.edit_profile"))

    if proposed["category"] not in {
        "Alumni",
        "Running Student",
        "Teacher",
        "Employee",
    }:
        flash("Please select a valid category.", "danger")
        return redirect(url_for("user_dashboard.edit_profile"))

    if not proposed["department"]:
        flash("Department is required.", "danger")
        return redirect(url_for("user_dashboard.edit_profile"))

    if not proposed["phone"]:
        flash("Phone number is required.", "danger")
        return redirect(url_for("user_dashboard.edit_profile"))

    if proposed["email"] and not re.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        proposed["email"],
    ):
        flash("Please enter a valid email address.", "danger")
        return redirect(url_for("user_dashboard.edit_profile"))

    duplicate_phone = Information.query.filter(
        Information.phone == proposed["phone"],
        Information.id != member.id,
    ).first()

    if duplicate_phone:
        flash("This phone number belongs to another member.", "danger")
        return redirect(url_for("user_dashboard.edit_profile"))

    if proposed["email"]:
        duplicate_email = Information.query.filter(
            func.lower(Information.email) == proposed["email"],
            Information.id != member.id,
        ).first()

        if duplicate_email:
            flash("This email belongs to another member.", "danger")
            return redirect(url_for("user_dashboard.edit_profile"))

    uploaded_photo = None
    new_photo = request.files.get("photo")

    if new_photo and new_photo.filename:
        uploaded_photo = upload_photo(new_photo)

        if not uploaded_photo or uploaded_photo == "default.png":
            flash(
                "Please upload a valid image under 10 MB.",
                "danger",
            )
            return redirect(url_for("user_dashboard.edit_profile"))

    edit_request = pending_request or MemberEditRequest(
        user_id=user.id,
        member_id=member.id,
        status="Pending",
    )

    if uploaded_photo:
        if edit_request.proposed_photo:
            delete_photo(edit_request.proposed_photo)
        edit_request.proposed_photo = uploaded_photo

    edit_request.set_proposed_data(proposed)
    edit_request.status = "Pending"
    edit_request.admin_note = None
    edit_request.reviewed_by_id = None
    edit_request.reviewed_at = None

    try:
        db.session.add(edit_request)
        db.session.commit()

    except Exception as exc:
        db.session.rollback()

        if uploaded_photo:
            delete_photo(uploaded_photo)

        print(f"Member edit request failed: {exc}")
        flash("Your update request could not be saved.", "danger")
        return redirect(url_for("user_dashboard.edit_profile"))

    flash(
        "Your changes were submitted for administrator approval.",
        "success",
    )
    return redirect(url_for("user_dashboard.dashboard"))
