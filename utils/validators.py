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

    if not email:
        return True

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return re.match(pattern, email) is not None


# =====================================================
# BANGLADESHI PHONE VALIDATION
# =====================================================

def valid_phone(phone):

    if not phone:
        return False

    pattern = r"^(?:\+8801|8801|01)[3-9]\d{8}$"

    return re.match(pattern, phone) is not None


# =====================================================
# PASSWORD VALIDATION
# =====================================================

def valid_password(password):

    if not password:
        return False

    if len(password) < 6:
        return False

    return True


# =====================================================
# USERNAME VALIDATION
# =====================================================

def valid_username(username):

    if not username:
        return False

    if len(username) < 4:
        return False

    pattern = r"^[A-Za-z0-9_]+$"

    return re.match(pattern, username) is not None


# =====================================================
# IMAGE VALIDATION
# =====================================================

def valid_image(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


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

    return category in categories


# =====================================================
# BLOOD GROUP VALIDATION
# =====================================================

def valid_blood_group(group):

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

    return group in blood_groups


# =====================================================
# GENDER VALIDATION
# =====================================================

def valid_gender(gender):

    genders = [

        "Male",

        "Female",

        "Other"

    ]

    return gender in genders


# =====================================================
# NAME VALIDATION
# =====================================================

def valid_name(name):

    if not required(name):
        return False

    return len(name.strip()) >= 3


# =====================================================
# SESSION VALIDATION
# =====================================================

def valid_session(session):

    if not session:
        return True

    return len(session.strip()) >= 4


# =====================================================
# BATCH VALIDATION
# =====================================================

def valid_batch(batch):

    if not batch:
        return True

    return len(batch.strip()) >= 2


# =====================================================
# FILE SIZE VALIDATION
# =====================================================

def valid_file_size(file, max_size=5 * 1024 * 1024):

    if not file:
        return True

    file.seek(0, 2)

    size = file.tell()

    file.seek(0)

    return size <= max_size


# =====================================================
# COMPLETE MEMBER FORM VALIDATION
# =====================================================

def validate_member_form(form):

    errors = []

    if not valid_name(form.get("full_name")):
        errors.append("Invalid Full Name")

    if not valid_phone(form.get("phone")):
        errors.append("Invalid Phone Number")

    if not valid_email(form.get("email")):
        errors.append("Invalid Email Address")

    if not valid_category(form.get("category")):
        errors.append("Invalid Category")

    return errors


# =====================================================
# LOGIN VALIDATION
# =====================================================

def validate_login(username, password):

    if not valid_username(username):
        return False

    if not required(password):
        return False

    return True