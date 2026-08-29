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
from sqlalchemy import func

from extensions import db
from models import Information
from models_user import MemberEditRequest
from services.upload_service import (
    delete_photo,
    upload_photo,
)
from utils.user_decorators import (
    user_login_required,
)


user_dashboard_bp = Blueprint(
    "user_dashboard",
    __name__,
    url_prefix="/account",
)


# ============================================================
# USER DASHBOARD
# ============================================================

@user_dashboard_bp.route(
    "/dashboard"
)
@user_login_required
def dashboard():

    user = g.user_account

    member = user.member

    latest_request = (

        MemberEditRequest.query

        .filter_by(
            user_id=user.id
        )

        .order_by(
            MemberEditRequest
            .created_at
            .desc()
        )

        .first()

    )

    return render_template(

        "user/dashboard.html",

        user=user,

        member=member,

        latest_request=latest_request,

    )


# ============================================================
# EDIT LINKED MEMBER PROFILE
# ============================================================

@user_dashboard_bp.route(
    "/profile/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@user_login_required
def edit_profile():

    user = g.user_account

    member = user.member


    # --------------------------------------------------------
    # PROFILE MUST BE LINKED
    # --------------------------------------------------------

    if not member:

        flash(
            (
                "Link or submit a directory "
                "profile before editing."
            ),
            "warning",
        )

        return redirect(
            url_for(
                "user_dashboard.dashboard"
            )
        )


    # --------------------------------------------------------
    # EXISTING PENDING REQUEST
    # --------------------------------------------------------

    pending_request = (

        MemberEditRequest.query

        .filter_by(

            user_id=user.id,

            member_id=member.id,

            status="Pending",

        )

        .first()

    )


    # --------------------------------------------------------
    # DISPLAY EDIT FORM
    # --------------------------------------------------------

    if request.method == "GET":

        form_values = (

            pending_request
            .get_proposed_data()

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


    # --------------------------------------------------------
    # FORM VALUE HELPER
    # --------------------------------------------------------

    def form_value(
        field,
        fallback="",
    ):

        return str(

            request.form.get(
                field,
                fallback,
            )

            or ""

        ).strip()


    # --------------------------------------------------------
    # PROPOSED INFORMATION
    # --------------------------------------------------------

    proposed = {

        "full_name":
            form_value(
                "full_name"
            ),

        "category":
            form_value(
                "category"
            ),

        "gender":
            form_value(
                "gender"
            ),

        "date_of_birth":
            form_value(
                "date_of_birth"
            ),

        "blood_group":
            form_value(
                "blood_group"
            ),

        "phone":
            form_value(
                "phone"
            ),

        "email":
            form_value(
                "email"
            ).lower(),

        "department":
            form_value(
                "department"
            ),

        "batch":
            form_value(
                "batch"
            ),

        "session":
            form_value(
                "session"
            ),

        "district":
            form_value(
                "district",
                "Gaibandha",
            ),

        "present_village":
            form_value(
                "present_village"
            ),

        "present_union":
            form_value(
                "present_union"
            ),

        "present_upazila":
            form_value(
                "present_upazila"
            ),

        "present_address":
            form_value(
                "present_address"
            ),

        "permanent_village":
            form_value(
                "permanent_village"
            ),

        "permanent_union":
            form_value(
                "permanent_union"
            ),

        "permanent_upazila":
            form_value(
                "permanent_upazila"
            ),

        "permanent_address":
            form_value(
                "permanent_address"
            ),

        "occupation":
            form_value(
                "occupation"
            ),

        "company":
            form_value(
                "company"
            ),

        "designation":
            form_value(
                "designation"
            ),

        "facebook":
            form_value(
                "facebook"
            ),

        "linkedin":
            form_value(
                "linkedin"
            ),

        "github":
            form_value(
                "github"
            ),

        "website":
            form_value(
                "website"
            ),

    }


    # --------------------------------------------------------
    # REQUIRED FIELD VALIDATION
    # --------------------------------------------------------

    if not proposed["full_name"]:

        flash(
            "Full name is required.",
            "danger",
        )

        return redirect(
            url_for(
                "user_dashboard.edit_profile"
            )
        )


    allowed_categories = {

        "Alumni",

        "Running Student",

        "Teacher",

        "Employee",

    }


    if (
        proposed["category"]
        not in allowed_categories
    ):

        flash(
            "Please select a valid category.",
            "danger",
        )

        return redirect(
            url_for(
                "user_dashboard.edit_profile"
            )
        )


    if not proposed["department"]:

        flash(
            "Department is required.",
            "danger",
        )

        return redirect(
            url_for(
                "user_dashboard.edit_profile"
            )
        )


    if not proposed["phone"]:

        flash(
            "Phone number is required.",
            "danger",
        )

        return redirect(
            url_for(
                "user_dashboard.edit_profile"
            )
        )


    # --------------------------------------------------------
    # EMAIL VALIDATION
    # --------------------------------------------------------

    if (

        proposed["email"]

        and

        not re.match(

            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",

            proposed["email"],

        )

    ):

        flash(
            "Please enter a valid email address.",
            "danger",
        )

        return redirect(
            url_for(
                "user_dashboard.edit_profile"
            )
        )


    # --------------------------------------------------------
    # DUPLICATE PHONE VALIDATION
    # --------------------------------------------------------

    duplicate_phone = (

        Information.query

        .filter(

            Information.phone
            == proposed["phone"],

            Information.id
            != member.id,

        )

        .first()

    )


    if duplicate_phone:

        flash(
            (
                "This phone number belongs "
                "to another member."
            ),
            "danger",
        )

        return redirect(
            url_for(
                "user_dashboard.edit_profile"
            )
        )


    # --------------------------------------------------------
    # DUPLICATE EMAIL VALIDATION
    # --------------------------------------------------------

    if proposed["email"]:

        duplicate_email = (

            Information.query

            .filter(

                func.lower(
                    Information.email
                )
                == proposed["email"],

                Information.id
                != member.id,

            )

            .first()

        )


        if duplicate_email:

            flash(
                (
                    "This email belongs "
                    "to another member."
                ),
                "danger",
            )

            return redirect(
                url_for(
                    "user_dashboard.edit_profile"
                )
            )


    # --------------------------------------------------------
    # OPTIONAL NEW PHOTO
    # --------------------------------------------------------

    uploaded_photo = None

    new_photo = request.files.get(
        "photo"
    )


    if (

        new_photo

        and

        new_photo.filename

    ):

        uploaded_photo = upload_photo(
            new_photo
        )


        if (

            not uploaded_photo

            or

            uploaded_photo
            == "default.png"

        ):

            flash(
                (
                    "Please upload a valid "
                    "image under 10 MB."
                ),
                "danger",
            )

            return redirect(
                url_for(
                    "user_dashboard.edit_profile"
                )
            )


    # --------------------------------------------------------
    # CREATE OR UPDATE PENDING REQUEST
    # --------------------------------------------------------

    edit_request = (

        pending_request

        or

        MemberEditRequest(

            user_id=user.id,

            member_id=member.id,

            status="Pending",

        )

    )


    # --------------------------------------------------------
    # REPLACE PENDING PHOTO
    # --------------------------------------------------------

    if uploaded_photo:

        if edit_request.proposed_photo:

            delete_photo(
                edit_request.proposed_photo
            )

        edit_request.proposed_photo = (
            uploaded_photo
        )


    # --------------------------------------------------------
    # STORE PROPOSED INFORMATION
    # --------------------------------------------------------

    edit_request.set_proposed_data(
        proposed
    )

    edit_request.status = "Pending"

    edit_request.admin_note = None

    edit_request.reviewed_by_id = None

    edit_request.reviewed_at = None


    # --------------------------------------------------------
    # SAVE REQUEST
    # --------------------------------------------------------

    try:

        db.session.add(
            edit_request
        )

        db.session.commit()


    except Exception as exc:

        db.session.rollback()


        if uploaded_photo:

            delete_photo(
                uploaded_photo
            )


        print(
            f"Member edit request failed: {exc}"
        )


        flash(
            (
                "Your update request "
                "could not be saved."
            ),
            "danger",
        )

        return redirect(
            url_for(
                "user_dashboard.edit_profile"
            )
        )


    flash(
        (
            "Your changes were submitted "
            "for administrator approval."
        ),
        "success",
    )


    return redirect(
        url_for(
            "user_dashboard.dashboard"
        )
    )