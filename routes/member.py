
# =====================================================
# routes/member.py
# JUians of Gaibandha Portal
# Member Routes
# Automatic Alumni
# Member Verification
# Role-aware Security
# Public Privacy Protection
# =====================================================


from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    session
)


from models import Information


from extensions import db


from services.upload_service import (
    upload_photo
)


from services.member_service import (
    create_member,
    phone_exists,
    email_exists,
    get_category_members,
    get_member,
    update_student_categories
)


from utils.validators import (
    validate_member_form
)


# =====================================================
# BLUEPRINT
# =====================================================

member_bp = Blueprint(
    "member",
    __name__
)


# =====================================================
# PUBLIC CATEGORY VALUES
# =====================================================

PUBLIC_CATEGORIES = {
    "Alumni",
    "Running Student",
    "Teacher",
    "Employee"
}


# =====================================================
# SAFE PUBLIC MEMBER FIELDS
# =====================================================
#
# IMPORTANT:
# -----------------------------------------------------
# We deliberately do NOT expose:
#
# phone
# email
# date_of_birth
# blood_group
# student_id
# registration_no
# present_address
# permanent_address
# facebook
# linkedin
# github
# website
# remarks
#
# These remain in database but are not sent to public
# profile templates.
# =====================================================

PUBLIC_MEMBER_FIELDS = (
    "id",
    "category",
    "full_name",
    "department",
    "batch",
    "session",
    "district",
    "upazila",
    "occupation",
    "company",
    "designation",
    "photo",
    "status",
    "approved_by",
    "approved_at"
)


# =====================================================
# ADMIN ROLE HELPER
# =====================================================

def get_current_admin_role():
    """
    Read the currently logged-in admin role from session.

    This helper does NOT grant access by itself.
    It is only used for role-aware checks.

    Expected session values:
        admin_role
        role

    Compatible with existing login implementations.
    """

    role = session.get("admin_role")

    if not role:
        role = session.get("role")

    if not role:
        return None

    return str(role).strip()


# =====================================================
# ROLE CHECK
# =====================================================

def has_admin_role(*allowed_roles):
    """
    Check whether current logged-in admin has one
    of the supplied roles.

    Example:

        has_admin_role(
            "Admin",
            "Super Admin"
        )
    """

    current_role = get_current_admin_role()

    if not current_role:
        return False

    normalized_current = current_role.lower()

    normalized_allowed = {
        str(role).strip().lower()
        for role in allowed_roles
    }

    return normalized_current in normalized_allowed


# =====================================================
# PUBLIC MEMBER SERIALIZATION
# =====================================================

def serialize_public_member(member):
    """
    Convert approved member into a privacy-safe dictionary.

    This prevents sensitive database fields from being
    accidentally exposed to public templates/API logic.
    """

    if member is None:
        return None

    if str(member.status).strip().lower() != "approved":
        return None

    return {
        field: getattr(member, field, None)
        for field in PUBLIC_MEMBER_FIELDS
    }


# =====================================================
# PUBLIC MEMBER ACCESS
# =====================================================

def get_public_member(member_id):
    """
    Return only an approved member.

    Pending and Rejected members are never returned.

    Automatic Running Student -> Alumni migration is
    performed before the lookup.
    """

    update_student_categories()

    member = (
        Information.query
        .filter(
            Information.id == member_id,
            Information.status == "Approved"
        )
        .first()
    )

    if member is None:
        return None

    return serialize_public_member(member)


# =====================================================
# SUBMIT INFORMATION
# =====================================================

@member_bp.route(
    "/submit",
    methods=["GET", "POST"]
)
def submit():

    update_student_categories()

    if request.method == "POST":

        # =================================================
        # VALIDATION
        # =================================================

        errors = validate_member_form(
            request.form
        )

        if errors:

            for error in errors:

                flash(
                    error,
                    "danger"
                )

            return redirect(
                url_for(
                    "member.submit"
                )
            )

        # =================================================
        # PHONE
        # =================================================

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        if phone_exists(phone):

            flash(
                "Phone Number Already Registered!",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )

        # =================================================
        # EMAIL
        # =================================================

        email = request.form.get(
            "email",
            ""
        ).strip()

        if email and email_exists(email):

            flash(
                "Email Already Registered!",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )

        # =================================================
        # PHOTO
        # =================================================

        photo = request.files.get(
            "photo"
        )

        photo_filename = upload_photo(
            photo
        )

        if (
            photo
            and photo.filename
            and photo_filename is None
        ):

            flash(
                "Invalid image format.",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )

        # =================================================
        # FORM VALUES
        # =================================================

        category = request.form.get(
            "category",
            ""
        ).strip()

        member_session = request.form.get(
            "session",
            ""
        ).strip()

        # =================================================
        # CATEGORY VALIDATION
        # =================================================

        if category not in PUBLIC_CATEGORIES:

            flash(
                "Invalid member category.",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )

        # =================================================
        # RUNNING STUDENT SESSION VALIDATION
        # =================================================

        if category == "Running Student":

            if member_session:

                try:

                    normalized_session = (
                        member_session
                        .replace(
                            " ",
                            ""
                        )
                        .replace(
                            "/",
                            "-"
                        )
                        .replace(
                            "_",
                            "-"
                        )
                    )

                    session_parts = (
                        normalized_session.split("-")
                    )

                    if len(session_parts) != 2:
                        raise ValueError

                    start_year = int(
                        session_parts[0]
                    )

                    end_year = int(
                        session_parts[1]
                    )

                    if (
                        end_year
                        != start_year + 1
                    ):
                        raise ValueError

                    if start_year < 1900:
                        raise ValueError

                except (
                    ValueError,
                    TypeError
                ):

                    flash(
                        "Invalid session format. Please use format like 2020-2021.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "member.submit"
                        )
                    )

        # =================================================
        # CREATE MEMBER
        # =================================================

        member = Information(

            category=category,

            full_name=request.form.get(
                "full_name"
            ),

            department=request.form.get(
                "department"
            ),

            batch=request.form.get(
                "batch"
            ),

            session=member_session,

            student_id=request.form.get(
                "student_id"
            ),

            registration_no=request.form.get(
                "registration_no"
            ),

            phone=phone,

            email=email,

            gender=request.form.get(
                "gender"
            ),

            date_of_birth=request.form.get(
                "date_of_birth"
            ),

            blood_group=request.form.get(
                "blood_group"
            ),

            present_address=request.form.get(
                "present_address"
            ),

            permanent_address=request.form.get(
                "permanent_address"
            ),

            district=request.form.get(
                "district"
            ),

            upazila=request.form.get(
                "upazila"
            ),

            occupation=request.form.get(
                "occupation"
            ),

            company=request.form.get(
                "company"
            ),

            designation=request.form.get(
                "designation"
            ),

            facebook=request.form.get(
                "facebook"
            ),

            linkedin=request.form.get(
                "linkedin"
            ),

            github=request.form.get(
                "github"
            ),

            website=request.form.get(
                "website"
            ),

            remarks=request.form.get(
                "remarks"
            ),

            photo=photo_filename,

            status="Pending"

        )

        # =================================================
        # SAVE
        # =================================================

        try:

            create_member(
                member
            )

            flash(
                "Information Submitted Successfully. Waiting For Admin Approval.",
                "success"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )

        except Exception:

            db.session.rollback()

            flash(
                "Something went wrong. Please try again.",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )

    return render_template(
        "submit.html"
    )


# =====================================================
# ALUMNI DIRECTORY
# =====================================================

@member_bp.route(
    "/alumni"
)
def alumni():

    update_student_categories()

    members = get_category_members(
        "Alumni"
    )

    return render_template(
        "category.html",
        title="Alumni",
        members=members
    )


# =====================================================
# RUNNING STUDENTS
# =====================================================

@member_bp.route(
    "/students"
)
def students():

    update_student_categories()

    members = get_category_members(
        "Running Student"
    )

    return render_template(
        "category.html",
        title="Running Students",
        members=members
    )


# =====================================================
# TEACHERS
# =====================================================

@member_bp.route(
    "/teachers"
)
def teachers():

    update_student_categories()

    members = get_category_members(
        "Teacher"
    )

    return render_template(
        "category.html",
        title="Teachers",
        members=members
    )


# =====================================================
# EMPLOYEES
# =====================================================

@member_bp.route(
    "/employees"
)
def employees():

    update_student_categories()

    members = get_category_members(
        "Employee"
    )

    return render_template(
        "category.html",
        title="Employees",
        members=members
    )


# =====================================================
# CATEGORY PAGE
# =====================================================

@member_bp.route(
    "/category/<string:category>"
)
def category(category):

    update_student_categories()

    if category not in PUBLIC_CATEGORIES:

        abort(404)

    members = get_category_members(
        category
    )

    return render_template(
        "category.html",
        title=category,
        members=members
    )


# =====================================================
# MEMBER DETAILS
# =====================================================

@member_bp.route(
    "/member/<int:id>"
)
def member_details(id):

    member = get_public_member(
        id
    )

    if member is None:

        flash(
            "Member not found or not publicly available.",
            "warning"
        )

        return redirect(
            url_for(
                "home.home"
            )
        )

    return render_template(
        "member_details.html",
        member=member
    )


# =====================================================
# PROFILE
# =====================================================

@member_bp.route(
    "/profile/<int:id>"
)
def member_profile(id):

    member = get_public_member(
        id
    )

    if member is None:

        flash(
            "Member not found or not publicly available.",
            "warning"
        )

        return redirect(
            url_for(
                "home.home"
            )
        )

    return render_template(
        "member_details.html",
        member=member
    )


# =====================================================
# VIEW MEMBER
# =====================================================

@member_bp.route(
    "/view/<int:id>"
)
def view_member(id):

    member = get_public_member(
        id
    )

    if member is None:

        flash(
            "Member not found or not publicly available.",
            "warning"
        )

        return redirect(
            url_for(
                "home.home"
            )
        )

    return render_template(
        "member_details.html",
        member=member
    )


# =====================================================
# MEMBER PHOTO
# =====================================================
#
# Only APPROVED members can expose photos.
# =====================================================

@member_bp.route(
    "/photo/<int:id>"
)
def member_photo(id):

    member = (
        Information.query
        .filter(
            Information.id == id,
            Information.status == "Approved"
        )
        .first()
    )

    if member is None:
        abort(404)

    if not member.photo:
        abort(404)

    return redirect(
        url_for(
            "static",
            filename=f"uploads/{member.photo}"
        )
    )

