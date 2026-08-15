"""
=====================================================
JUians of Gaibandha Portal
Validators
Version 1.0
Developer : Khaled Mahmud Jon
=====================================================
"""

import re

from services.upload_service import ALLOWED_EXTENSIONS


# =====================================================
# REQUIRED FIELD VALIDATION
# =====================================================

def required(value):

    if value is None:
        return False

    if str(value).strip() == "":
        return False

    return True


# =====================================================
# EMAIL VALIDATION
# =====================================================

def valid_email(email):

    # -------------------------------------------------
    # Email is optional for member registration.
    # -------------------------------------------------

    if not email:
        return True


    email = str(
        email
    ).strip()


    pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}$"
    )


    return (
        re.fullmatch(
            pattern,
            email
        )
        is not None
    )


# =====================================================
# BANGLADESHI PHONE VALIDATION
# =====================================================

def valid_phone(phone):

    if not phone:
        return False


    phone = str(
        phone
    ).strip()


    pattern = (
        r"^(?:\+8801|8801|01)"
        r"[3-9]\d{8}$"
    )


    return (
        re.fullmatch(
            pattern,
            phone
        )
        is not None
    )


# =====================================================
# PASSWORD VALIDATION
# =====================================================

def valid_password(password):

    if not password:
        return False


    if len(
        str(password)
    ) < 6:

        return False


    return True


# =====================================================
# USERNAME VALIDATION
# =====================================================

def valid_username(username):

    if not username:
        return False


    username = str(
        username
    ).strip()


    if len(username) < 4:
        return False


    pattern = (
        r"^[A-Za-z0-9_]+$"
    )


    return (
        re.fullmatch(
            pattern,
            username
        )
        is not None
    )


# =====================================================
# LOGIN IDENTIFIER VALIDATION
# =====================================================
#
# Administrator login supports:
#
# 1. Username
# 2. Email
#
# Therefore this validator must support both.
# =====================================================

def valid_login_identifier(
    value
):

    if not value:

        return False


    value = str(
        value
    ).strip()


    if not value:

        return False


    # -------------------------------------------------
    # Email Login
    # -------------------------------------------------

    if "@" in value:

        return valid_email(
            value
        )


    # -------------------------------------------------
    # Username Login
    # -------------------------------------------------

    return valid_username(
        value
    )


# =====================================================
# IMAGE VALIDATION
# =====================================================

def valid_image(filename):

    if not filename:
        return False


    filename = str(
        filename
    ).strip()


    if "." not in filename:
        return False


    extension = (
        filename
        .rsplit(
            ".",
            1
        )[1]
        .lower()
    )


    return (
        extension
        in ALLOWED_EXTENSIONS
    )


# =====================================================
# MEMBER CATEGORY VALIDATION
# =====================================================

def valid_category(category):

    categories = [

        "Running Student",

        "Alumni",

        "Teacher",

        "Employee"

    ]


    if not category:

        return False


    category = str(
        category
    ).strip()


    return (
        category
        in categories
    )


# =====================================================
# BLOOD GROUP VALIDATION
# =====================================================

def valid_blood_group(group):

    # -------------------------------------------------
    # Blood group is optional.
    # -------------------------------------------------

    if not group:

        return True


    blood_groups = [

        "A+",

        "A-",

        "B+",

        "B-",

        "AB+",

        "AB-",

        "O+",

        "O-"

    ]


    group = str(
        group
    ).strip()


    return (
        group
        in blood_groups
    )


# =====================================================
# GENDER VALIDATION
# =====================================================

def valid_gender(gender):

    # -------------------------------------------------
    # Gender is optional.
    # -------------------------------------------------

    if not gender:

        return True


    genders = [

        "Male",

        "Female",

        "Other"

    ]


    gender = str(
        gender
    ).strip()


    return (
        gender
        in genders
    )


# =====================================================
# NAME VALIDATION
# =====================================================

def valid_name(name):

    if not required(
        name
    ):

        return False


    name = str(
        name
    ).strip()


    if len(name) < 3:

        return False


    return True


# =====================================================
# DEPARTMENT VALIDATION
# =====================================================

def valid_department(
    department
):

    if not required(
        department
    ):

        return False


    department = str(
        department
    ).strip()


    return (
        len(department)
        >= 2
    )


# =====================================================
# SESSION VALIDATION
# =====================================================

def valid_session(session):

    # -------------------------------------------------
    # Session is optional.
    # -------------------------------------------------

    if not session:

        return True


    try:

        value = str(
            session
        ).strip()


        if not value:

            return True


        value = (

            value

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


        parts = (
            value.split(
                "-"
            )
        )


        if len(parts) != 2:

            return False


        start_year = int(
            parts[0]
        )


        end_year = int(
            parts[1]
        )


        if (
            start_year < 1900
            or
            start_year > 2100
        ):

            return False


        if (
            end_year
            != start_year + 1
        ):

            return False


        return True


    except (
        ValueError,
        TypeError,
        AttributeError
    ):

        return False


# =====================================================
# BATCH VALIDATION
# =====================================================

def valid_batch(batch):

    # -------------------------------------------------
    # Batch is optional.
    # -------------------------------------------------

    if not batch:

        return True


    batch = str(
        batch
    ).strip()


    if not batch:

        return True


    return (
        len(batch)
        >= 1
    )


# =====================================================
# FILE SIZE VALIDATION
# =====================================================

def valid_file_size(
    file,
    max_size=5 * 1024 * 1024
):

    if not file:

        return True


    try:

        # -------------------------------------------------
        # Werkzeug FileStorage
        # -------------------------------------------------

        stream = getattr(
            file,
            "stream",
            file
        )


        current_position = (
            stream.tell()
        )


        stream.seek(
            0,
            2
        )


        size = (
            stream.tell()
        )


        stream.seek(
            current_position
        )


        return (
            0 <= size <= max_size
        )


    except Exception:

        return False


# =====================================================
# COMPLETE MEMBER FORM VALIDATION
# =====================================================

def validate_member_form(form):

    errors = []


    # -------------------------------------------------
    # FULL NAME
    # -------------------------------------------------

    if not valid_name(
        form.get(
            "full_name"
        )
    ):

        errors.append(
            "Please enter a valid full name."
        )


    # -------------------------------------------------
    # CATEGORY
    # -------------------------------------------------

    if not valid_category(
        form.get(
            "category"
        )
    ):

        errors.append(
            "Please select a valid member category."
        )


    # -------------------------------------------------
    # DEPARTMENT
    # -------------------------------------------------

    if not valid_department(
        form.get(
            "department"
        )
    ):

        errors.append(
            "Department is required."
        )


    # -------------------------------------------------
    # PHONE
    # -------------------------------------------------

    if not valid_phone(
        form.get(
            "phone"
        )
    ):

        errors.append(
            (
                "Please enter a valid Bangladeshi "
                "mobile number."
            )
        )


    # -------------------------------------------------
    # EMAIL
    # -------------------------------------------------

    if not valid_email(
        form.get(
            "email"
        )
    ):

        errors.append(
            "Please enter a valid email address."
        )


    # -------------------------------------------------
    # GENDER
    # -------------------------------------------------

    if not valid_gender(
        form.get(
            "gender"
        )
    ):

        errors.append(
            "Please select a valid gender."
        )


    # -------------------------------------------------
    # BLOOD GROUP
    # -------------------------------------------------

    if not valid_blood_group(
        form.get(
            "blood_group"
        )
    ):

        errors.append(
            "Please select a valid blood group."
        )


    # -------------------------------------------------
    # BATCH
    # -------------------------------------------------

    if not valid_batch(
        form.get(
            "batch"
        )
    ):

        errors.append(
            "Please enter a valid batch."
        )


    # -------------------------------------------------
    # SESSION
    # -------------------------------------------------

    session_value = (
        form.get(
            "session"
        )
    )


    category = (
        form.get(
            "category",
            ""
        )
    )


    if (
        category
        == "Running Student"
        and
        session_value
        and
        not valid_session(
            session_value
        )
    ):

        errors.append(
            (
                "Invalid session format. "
                "Please use format like "
                "2020-2021."
            )
        )


    return errors


# =====================================================
# LOGIN VALIDATION
# =====================================================
#
# IMPORTANT:
#
# routes/auth.py expects:
#
#     error = validate_login(...)
#
#     if error:
#         flash(error, "danger")
#
# Therefore:
#
#     None        = valid
#     string      = validation error
#
# Do NOT return True/False here.
# =====================================================

def validate_login(
    username,
    password
):

    username = str(
        username
        or ""
    ).strip()


    # -------------------------------------------------
    # USERNAME / EMAIL REQUIRED
    # -------------------------------------------------

    if not username:

        return (
            "Username or email is required."
        )


    # -------------------------------------------------
    # USERNAME / EMAIL FORMAT
    # -------------------------------------------------

    if not valid_login_identifier(
        username
    ):

        return (
            "Please enter a valid username or email address."
        )


    # -------------------------------------------------
    # PASSWORD REQUIRED
    # -------------------------------------------------

    if not required(
        password
    ):

        return (
            "Password is required."
        )


    # -------------------------------------------------
    # VALID
    # -------------------------------------------------

    return None


# =====================================================
# END OF FILE
# =====================================================
