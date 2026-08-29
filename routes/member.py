# =====================================================
# routes/member.py
# JUians of Gaibandha Portal
# Member Routes
# Automatic Alumni
# Member Verification
# Role-aware Security
# Public Privacy Protection
# Structured Address Support
# Reliable Member Photo Serving
# =====================================================


import os


from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    session,
    current_app,
    send_from_directory
)


from models import Information


from extensions import db


from services.upload_service import (
    upload_photo,
    UPLOAD_FOLDER
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


from utils.user_decorators import (
    get_logged_in_user
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
# GAIBANDHA UPAZILA VALUES
# =====================================================

GAIBANDHA_UPAZILAS = {

    "Gaibandha Sadar",

    "Sadullapur",

    "Sundarganj",

    "Saghata",

    "Fulchhari",

    "Gobindaganj",

    "Palashbari"

}


# =====================================================
# SAFE PUBLIC MEMBER FIELDS
# =====================================================
#
# IMPORTANT:
#
# Public visitors can see only these fields.
#
# Sensitive information is intentionally protected.
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
    Check whether current logged-in admin has
    one of the supplied roles.
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
# VALIDATE UPAZILA
# =====================================================

def validate_gaibandha_upazila(
    upazila
):

    """
    Validate an optional Gaibandha upazila.
    """

    if not upazila:

        return True


    return (
        upazila
        in GAIBANDHA_UPAZILAS
    )


# =====================================================
# PUBLIC MEMBER SERIALIZATION
# =====================================================

def serialize_public_member(
    member
):

    """
    Convert approved member into a
    privacy-safe dictionary.
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
    # Keep Running Student Categories Updated
    # -------------------------------------------------

    try:

        update_student_categories()

    except Exception:

        db.session.rollback()


    # Logged-in users receive ownership of the new profile
    # after a successful submission.
    logged_in_user = get_logged_in_user()


    # =================================================
    # POST REQUEST
    # =================================================

    if request.method == "POST":


        if (
            logged_in_user
            and logged_in_user.member_id
        ):

            flash(
                "Your account already has a linked directory profile.",
                "warning"
            )

            return redirect(
                url_for(
                    "user_dashboard.dashboard"
                )
            )


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
        # ADDRESS FORM VALUES
        # =================================================

        present_village = clean_form_value(
            "present_village"
        )


        present_union = clean_form_value(
            "present_union"
        )


        present_upazila = clean_form_value(
            "present_upazila"
        )


        present_address = clean_form_value(
            "present_address"
        )


        permanent_village = clean_form_value(
            "permanent_village"
        )


        permanent_union = clean_form_value(
            "permanent_union"
        )


        permanent_upazila = clean_form_value(
            "permanent_upazila"
        )


        permanent_address = clean_form_value(
            "permanent_address"
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
        # PRESENT UPAZILA VALIDATION
        # =================================================

        if not validate_gaibandha_upazila(
            present_upazila
        ):

            flash(
                "Invalid present address upazila.",
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )


        # =================================================
        # PERMANENT UPAZILA VALIDATION
        # =================================================

        if not validate_gaibandha_upazila(
            permanent_upazila
        ):

            flash(
                "Invalid permanent address upazila.",
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
                    "or WEBP image under 10 MB."
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "member.submit"
                )
            )


        # =================================================
        # LEGACY UPAZILA COMPATIBILITY
        # =================================================

        legacy_upazila = (
            permanent_upazila
            or
            present_upazila
        )


        # =================================================
        # CREATE MEMBER
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


            upazila=legacy_upazila,


            # ---------------------------------------------
            # PRESENT ADDRESS
            # ---------------------------------------------

            present_village=(
                present_village
            ),


            present_union=(
                present_union
            ),


            present_upazila=(
                present_upazila
            ),


            present_address=(
                present_address
            ),


            # ---------------------------------------------
            # PERMANENT ADDRESS
            # ---------------------------------------------

            permanent_village=(
                permanent_village
            ),


            permanent_union=(
                permanent_union
            ),


            permanent_upazila=(
                permanent_upazila
            ),


            permanent_address=(
                permanent_address
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

            if logged_in_user:

                db.session.add(
                    member
                )

                db.session.flush()

                logged_in_user.member_id = (
                    member.id
                )

                db.session.commit()

            else:

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


            if logged_in_user:

                return redirect(
                    url_for(
                        "user_dashboard.dashboard"
                    )
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
# This route serves profile photos only for
# APPROVED members.
#
# Supported database values:
#
#     abc123.jpg
#     uploads/abc123.jpg
#     static/uploads/abc123.jpg
#     images/default_user.png
#
# If the image no longer exists, the default
# profile image is returned instead.
# =====================================================

@member_bp.route(
    "/photo/<int:id>"
)
def member_photo(id):

    # -------------------------------------------------
    # APPROVED MEMBER ONLY
    # -------------------------------------------------

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


    # -------------------------------------------------
    # DEFAULT IMAGE HELPER
    # -------------------------------------------------

    default_image = os.path.join(

        current_app.static_folder,

        "images",

        "default_user.png"

    )


    # -------------------------------------------------
    # NO PHOTO
    # -------------------------------------------------

    if not member.photo:

        if os.path.isfile(
            default_image
        ):

            return send_from_directory(

                os.path.dirname(
                    default_image
                ),

                os.path.basename(
                    default_image
                )

            )


        abort(
            404
        )


    # -------------------------------------------------
    # NORMALIZE STORED PHOTO VALUE
    # -------------------------------------------------

    photo_name = str(
        member.photo
    ).replace(
        "\\",
        "/"
    ).strip()


    # -------------------------------------------------
    # CLOUDINARY / REMOTE PHOTO
    # -------------------------------------------------

    if photo_name.startswith((
        "https://",
        "http://"
    )):

        return redirect(
            photo_name,
            code=302,
        )


    photo_name = (
        photo_name.lstrip("/")
    )


    # -------------------------------------------------
    # DEFAULT DATABASE VALUES
    # -------------------------------------------------

    if photo_name in {

        "default.png",

        "default_user.png",

        "images/default.png",

        "images/default_user.png"

    }:

        if os.path.isfile(
            default_image
        ):

            return send_from_directory(

                os.path.dirname(
                    default_image
                ),

                os.path.basename(
                    default_image
                )

            )


        abort(
            404
        )


    # -------------------------------------------------
    # STATIC IMAGE
    # -------------------------------------------------
    #
    # Example:
    #
    # images/member.jpg
    # -------------------------------------------------

    if photo_name.startswith(
        "images/"
    ):

        static_image_path = os.path.abspath(

            os.path.join(

                current_app.static_folder,

                photo_name

            )

        )


        if os.path.isfile(
            static_image_path
        ):

            return send_from_directory(

                os.path.dirname(
                    static_image_path
                ),

                os.path.basename(
                    static_image_path
                )

            )


    # -------------------------------------------------
    # NORMALIZE UPLOAD FILE NAME
    # -------------------------------------------------

    if photo_name.startswith(
        "static/uploads/"
    ):

        photo_name = photo_name.replace(

            "static/uploads/",

            "",

            1

        )


    elif photo_name.startswith(
        "uploads/"
    ):

        photo_name = photo_name.replace(

            "uploads/",

            "",

            1

        )


    # -------------------------------------------------
    # SECURITY
    #
    # Only use basename.
    # Prevent path traversal.
    # -------------------------------------------------

    photo_name = os.path.basename(
        photo_name
    )


    if not photo_name:

        if os.path.isfile(
            default_image
        ):

            return send_from_directory(

                os.path.dirname(
                    default_image
                ),

                os.path.basename(
                    default_image
                )

            )


        abort(
            404
        )


    # -------------------------------------------------
    # BUILD ACTUAL UPLOAD PATH
    # -------------------------------------------------

    actual_upload_folder = os.path.abspath(
        UPLOAD_FOLDER
    )


    photo_path = os.path.abspath(

        os.path.join(

            actual_upload_folder,

            photo_name

        )

    )


    # -------------------------------------------------
    # SECURITY CHECK
    # -------------------------------------------------

    try:

        common_path = os.path.commonpath(

            [

                actual_upload_folder,

                photo_path

            ]

        )


    except ValueError:

        common_path = None


    if (
        common_path
        ==
        actual_upload_folder
        and
        os.path.isfile(
            photo_path
        )
    ):

        return send_from_directory(

            actual_upload_folder,

            photo_name

        )


    # -------------------------------------------------
    # FALLBACK:
    # STANDARD STATIC/UPLOADS DIRECTORY
    # -------------------------------------------------
    #
    # Useful when UPLOAD_FOLDER was changed by
    # environment configuration but older files are
    # still inside static/uploads.
    # -------------------------------------------------

    static_upload_folder = os.path.abspath(

        os.path.join(

            current_app.static_folder,

            "uploads"

        )

    )


    static_photo_path = os.path.abspath(

        os.path.join(

            static_upload_folder,

            photo_name

        )

    )


    if os.path.isfile(
        static_photo_path
    ):

        return send_from_directory(

            static_upload_folder,

            photo_name

        )


    # -------------------------------------------------
    # IMAGE FILE NOT FOUND
    # -------------------------------------------------
    #
    # Do not show broken image.
    # Return default profile image.
    # -------------------------------------------------

    if os.path.isfile(
        default_image
    ):

        return send_from_directory(

            os.path.dirname(
                default_image
            ),

            os.path.basename(
                default_image
            )

        )


    abort(
        404
    )


# =====================================================
# END OF FILE
# =====================================================
