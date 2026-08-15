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
    update_student_categories,
    normalize_session
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
#
# Public visitors can see only these fields.
#
# We deliberately do NOT expose:
#
# phone
# email
# gender
# date_of_birth
# blood_group
# present_address
# permanent_address
# facebook
#
# Personal/private fields remain protected.
#
# Administrator routes access the actual Information
# model directly and therefore can see full information.
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

    "approved_at"

)


# =====================================================
# ADMIN ROLE HELPER
# =====================================================

def get_current_admin_role():

    """
    Read the currently logged-in admin role
    from the session.

    This helper does NOT grant access by itself.

    Expected session values:

        admin_role
        role
    """

    role = session.get(
        "admin_role"
    )


    if not role:

        role = session.get(
            "role"
        )


    if not role:

        return None


    return str(
        role
    ).strip()


# =====================================================
# ROLE CHECK
# =====================================================

def has_admin_role(
    *allowed_roles
):

    """
    Check whether current logged-in admin has one
    of the supplied roles.

    Example:

        has_admin_role(
            "Admin",
            "Super Admin"
        )
    """

    current_role = (
        get_current_admin_role()
    )


    if not current_role:

        return False


    normalized_current = (
        current_role.lower()
    )


    normalized_allowed = {

        str(
            role
        ).strip().lower()

        for role
        in allowed_roles

    }


    return (
        normalized_current
        in normalized_allowed
    )


# =====================================================
# CLEAN FORM VALUE
# =====================================================

def clean_form_value(
    field_name,
    default=None
):

    """
    Return stripped form data.

    Empty values become None unless
    another default value is provided.
    """

    value = request.form.get(
        field_name,
        ""
    )


    if value is None:

        return default


    value = str(
        value
    ).strip()


    if not value:

        return default


    return value


# =====================================================
# NORMALIZE EMAIL
# =====================================================

def normalize_email(
    email
):

    if not email:

        return None


    email = str(
        email
    ).strip().lower()


    if not email:

        return None


    return email


# =====================================================
# PUBLIC MEMBER SERIALIZATION
# =====================================================

def serialize_public_member(
    member
):

    """
    Convert approved member into a
    privacy-safe dictionary.

    This prevents sensitive database fields
    from accidentally being exposed through
    public templates.
    """

    if member is None:

        return None


    status = str(
        member.status
        or ""
    ).strip().lower()


    if status != "approved":

        return None


    return {

        field:
            getattr(
                member,
                field,
                None
            )

        for field
        in PUBLIC_MEMBER_FIELDS

    }


# =====================================================
# PUBLIC MEMBER ACCESS
# =====================================================

def get_public_member(
    member_id
):

    """
    Return only an approved member.

    Pending and Rejected members are never
    returned publicly.

    Automatic Running Student -> Alumni
    conversion is performed before lookup.
    """

    update_student_categories()


    member = (

        Information.query

        .filter(

            Information.id
            == member_id,

            Information.status
            == "Approved"

        )

        .first()

    )


    if member is None:

        return None


    return (
        serialize_public_member(
            member
        )
    )


# =====================================================
# SUBMIT INFORMATION
# =====================================================

@member_bp.route(
    "/submit",
    methods=[
        "GET",
        "POST"
    ]
)
def submit():

    # -------------------------------------------------
    # Keep Approved Running Student Categories Updated
    # -------------------------------------------------

    try:

        update_student_categories()

    except Exception:

        db.session.rollback()


    # =================================================
    # POST REQUEST
    # =================================================

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
        # BASIC FORM VALUES
        # =================================================

        full_name = clean_form_value(
            "full_name"
        )


        category = clean_form_value(
            "category"
        )


        department = clean_form_value(
            "department"
        )


        phone = clean_form_value(
            "phone"
        )


        email = normalize_email(
            clean_form_value(
                "email"
            )
        )


        member_session = clean_form_value(
            "session"
        )


        # =================================================
        # REQUIRED VALUES
        # =================================================

        if not full_name:

            flash(
                "Full name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )


        if not category:

            flash(
                "Member category is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )


        if not department:

            flash(
                "Department is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )


        if not phone:

            flash(
                "Phone number is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )


        # =================================================
        # CATEGORY VALIDATION
        # =================================================

        if (
            category
            not in PUBLIC_CATEGORIES
        ):

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
        # PHONE DUPLICATE CHECK
        # =================================================

        if phone_exists(
            phone
        ):

            flash(
                (
                    "This phone number is already "
                    "registered."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )


        # =================================================
        # EMAIL DUPLICATE CHECK
        # =================================================

        if (

            email

            and

            email_exists(
                email
            )

        ):

            flash(
                (
                    "This email address is already "
                    "registered."
                ),
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

        if (

            category
            == "Running Student"

            and

            member_session

        ):

            start_year, end_year = (
                normalize_session(
                    member_session
                )
            )


            if (
                start_year is None
                or
                end_year is None
            ):

                flash(
                    (
                        "Invalid session format. "
                        "Please use format like "
                        "2020-2021."
                    ),
                    "danger"
                )

                return redirect(
                    url_for(
                        "member.submit"
                    )
                )


            # ---------------------------------------------
            # Store Standard Session Format
            # ---------------------------------------------

            member_session = (
                f"{start_year}-"
                f"{end_year}"
            )


        # =================================================
        # PHOTO
        # =================================================

        photo = request.files.get(
            "photo"
        )


        photo_filename = (
            upload_photo(
                photo
            )
        )


        if (

            photo

            and

            getattr(
                photo,
                "filename",
                ""
            )

            and

            photo_filename is None

        ):

            flash(
                (
                    "Invalid image. Please upload "
                    "a valid JPG, JPEG, PNG, GIF "
                    "or WEBP image under 5 MB."
                ),
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
        #
        # IMPORTANT:
        #
        # Only fields that actually exist in the
        # Member Registration / Submit Information
        # form are saved here.
        #
        # student_id
        # registration_no
        # linkedin
        # github
        # website
        # remarks
        #
        # are intentionally NOT collected here.
        # =================================================

        member = Information(


            # ---------------------------------------------
            # PERSONAL INFORMATION
            # ---------------------------------------------

            full_name=full_name,


            category=category,


            gender=clean_form_value(
                "gender"
            ),


            date_of_birth=clean_form_value(
                "date_of_birth"
            ),


            blood_group=clean_form_value(
                "blood_group"
            ),


            phone=phone,


            # ---------------------------------------------
            # ACADEMIC INFORMATION
            # ---------------------------------------------

            department=department,


            batch=clean_form_value(
                "batch"
            ),


            session=member_session,


            # ---------------------------------------------
            # CONTACT INFORMATION
            # ---------------------------------------------

            email=email,


            district=clean_form_value(
                "district",
                "Gaibandha"
            ),


            upazila=clean_form_value(
                "upazila"
            ),


            # ---------------------------------------------
            # ADDRESS INFORMATION
            # ---------------------------------------------

            present_address=(
                clean_form_value(
                    "present_address"
                )
            ),


            permanent_address=(
                clean_form_value(
                    "permanent_address"
                )
            ),


            # ---------------------------------------------
            # PROFESSIONAL INFORMATION
            # ---------------------------------------------

            occupation=clean_form_value(
                "occupation"
            ),


            company=clean_form_value(
                "company"
            ),


            designation=clean_form_value(
                "designation"
            ),


            # ---------------------------------------------
            # SOCIAL MEDIA
            # ---------------------------------------------

            facebook=clean_form_value(
                "facebook"
            ),


            # ---------------------------------------------
            # PROFILE PHOTO
            # ---------------------------------------------

            photo=(
                photo_filename
                or "default.png"
            ),


            # ---------------------------------------------
            # APPROVAL STATUS
            # ---------------------------------------------

            status="Pending"

        )


        # =================================================
        # SAVE MEMBER
        # =================================================

        try:

            create_member(
                member
            )


            flash(
                (
                    "Information submitted successfully. "
                    "Your submission is waiting for "
                    "administrator approval."
                ),
                "success"
            )


            return redirect(
                url_for(
                    "member.submit"
                )
            )


        except Exception as exc:

            db.session.rollback()


            print(
                f"Member submission error: {exc}"
            )


            flash(
                (
                    "Something went wrong while submitting "
                    "your information. Please try again."
                ),
                "danger"
            )


            return redirect(
                url_for(
                    "member.submit"
                )
            )


    # =================================================
    # GET REQUEST
    # =================================================

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


    members = (
        get_category_members(
            "Alumni"
        )
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


    members = (
        get_category_members(
            "Running Student"
        )
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


    members = (
        get_category_members(
            "Teacher"
        )
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


    members = (
        get_category_members(
            "Employee"
        )
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


    category = str(
        category
        or ""
    ).strip()


    if (
        category
        not in PUBLIC_CATEGORIES
    ):

        abort(
            404
        )


    members = (
        get_category_members(
            category
        )
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

    member = (
        get_public_member(
            id
        )
    )


    if member is None:

        flash(
            (
                "Member not found or not "
                "publicly available."
            ),
            "warning"
        )


        return redirect(
            url_for(
                "home.home"
            )
        )


    return render_template(

        "member_details.html",

        member=member,

        admin_view=False

    )


# =====================================================
# PROFILE
# =====================================================

@member_bp.route(
    "/profile/<int:id>"
)
def member_profile(id):

    member = (
        get_public_member(
            id
        )
    )


    if member is None:

        flash(
            (
                "Member not found or not "
                "publicly available."
            ),
            "warning"
        )


        return redirect(
            url_for(
                "home.home"
            )
        )


    return render_template(

        "member_details.html",

        member=member,

        admin_view=False

    )


# =====================================================
# VIEW MEMBER
# =====================================================

@member_bp.route(
    "/view/<int:id>"
)
def view_member(id):

    member = (
        get_public_member(
            id
        )
    )


    if member is None:

        flash(
            (
                "Member not found or not "
                "publicly available."
            ),
            "warning"
        )


        return redirect(
            url_for(
                "home.home"
            )
        )


    return render_template(

        "member_details.html",

        member=member,

        admin_view=False

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

            Information.id
            == id,

            Information.status
            == "Approved"

        )

        .first()

    )


    if member is None:

        abort(
            404
        )


    if not member.photo:

        abort(
            404
        )


    photo_name = str(
        member.photo
    ).replace(
        "\\",
        "/"
    ).strip()


    # -------------------------------------------------
    # Existing uploads/... Path
    # -------------------------------------------------

    if photo_name.startswith(
        "uploads/"
    ):

        static_path = (
            photo_name
        )


    # -------------------------------------------------
    # Existing static/uploads/... Path
    # -------------------------------------------------

    elif photo_name.startswith(
        "static/uploads/"
    ):

        static_path = (
            photo_name.replace(
                "static/",
                "",
                1
            )
        )


    # -------------------------------------------------
    # Default Static Image
    # -------------------------------------------------

    elif photo_name.startswith(
        "images/"
    ):

        static_path = (
            photo_name
        )


    # -------------------------------------------------
    # Standard Uploaded Filename
    # -------------------------------------------------

    else:

        static_path = (
            f"uploads/{photo_name}"
        )


    return redirect(

        url_for(

            "static",

            filename=static_path

        )

    )


# =====================================================
# END OF FILE
# =====================================================
