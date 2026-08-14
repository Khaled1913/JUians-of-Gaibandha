
# ============================================================
# JUians of Gaibandha
# Utility Helper Functions
# ============================================================


from datetime import datetime

from flask import session

from models import Admin


# ============================================================
# CURRENT YEAR
# ============================================================

def current_year():

    return datetime.now().year


# ============================================================
# CURRENT DATE
# ============================================================

def current_date():

    return datetime.now().strftime(

        "%d %B %Y"

    )


# ============================================================
# CURRENT DATE & TIME
# ============================================================

def current_datetime():

    return datetime.now().strftime(

        "%d %B %Y %I:%M %p"

    )


# ============================================================
# GET CURRENT ADMIN
# ============================================================

def current_admin():

    admin_id = session.get(

        "admin_id"

    )

    if not admin_id:

        return None

    return Admin.query.get(

        admin_id

    )


# ============================================================
# GET ACTIVE ADMIN
#
# Used for public website visitors.
# This does NOT depend on login session.
# ============================================================

def active_admin():

    return (
        Admin.query
        .filter_by(
            is_active=True
        )
        .order_by(
            Admin.id.asc()
        )
        .first()
    )


# ============================================================
# CHECK LOGIN
# ============================================================

def is_logged_in():

    return "admin_id" in session


# ============================================================
# GET ADMIN NAME
# ============================================================

def admin_name():

    admin = current_admin()

    if admin:

        return admin.full_name or session.get(
            "admin_name",
            ""
        )

    admin = active_admin()

    if admin:

        return admin.full_name or ""

    return session.get(

        "admin_name",

        ""

    )


# ============================================================
# GET ADMIN ROLE
# ============================================================

def admin_role():

    admin = current_admin()

    if admin:

        return admin.role or session.get(
            "admin_role",
            ""
        )

    admin = active_admin()

    if admin:

        return admin.role or ""

    return session.get(

        "admin_role",

        ""

    )


# ============================================================
# GET ADMIN CONTACT EMAIL
# ============================================================

def admin_contact_email():

    admin = current_admin()

    if not admin:

        admin = active_admin()

    if admin:

        return (

            admin.contact_email

            or ""

        )

    return ""


# ============================================================
# GET ADMIN CONTACT PHONE
# ============================================================

def admin_contact_phone():

    admin = current_admin()

    if not admin:

        admin = active_admin()

    if admin:

        return (

            admin.contact_phone

            or ""

        )

    return ""


# ============================================================
# GET ADMIN FACEBOOK URL
# ============================================================

def admin_facebook_url():

    admin = current_admin()

    if not admin:

        admin = active_admin()

    if admin:

        return (

            admin.facebook_url

            or ""

        )

    return ""


# ============================================================
# GET ADMIN CONTACT INFORMATION
# ============================================================

def admin_contact():

    # --------------------------------------------------------
    # First try logged-in administrator
    # --------------------------------------------------------

    admin = current_admin()


    # --------------------------------------------------------
    # If visitor is not logged in,
    # get the active administrator
    # --------------------------------------------------------

    if not admin:

        admin = active_admin()


    # --------------------------------------------------------
    # No active administrator found
    # --------------------------------------------------------

    if not admin:

        return {

            "name": "",

            "email": "",

            "phone": "",

            "facebook": ""

        }


    # --------------------------------------------------------
    # Return current administrator contact
    # --------------------------------------------------------

    return {

        "name": (

            admin.full_name

            or ""

        ),

        "email": (

            admin.contact_email

            or ""

        ),

        "phone": (

            admin.contact_phone

            or ""

        ),

        "facebook": (

            admin.facebook_url

            or ""

        )

    }


# ============================================================
# DEFAULT PROFILE PHOTO
# ============================================================

def default_photo():

    return "default.png"


# ============================================================
# MEMBER CATEGORIES
# ============================================================

def member_categories():

    return [

        "Running Student",

        "Alumni",

        "Teacher",

        "Employee"

    ]


# ============================================================
# BLOOD GROUPS
# ============================================================

def blood_groups():

    return [

        "A+",

        "A-",

        "B+",

        "B-",

        "AB+",

        "AB-",

        "O+",

        "O-"

    ]


# ============================================================
# GENDER LIST
# ============================================================

def gender_list():

    return [

        "Male",

        "Female",

        "Other"

    ]


# ============================================================
# DISTRICT NAME
# ============================================================

def district_name():

    return "Gaibandha"


# ============================================================
# FORMAT PHONE
# ============================================================

def format_phone(phone):

    if not phone:

        return ""

    return phone.strip()


# ============================================================
# FORMAT TEXT
# ============================================================

def clean_text(text):

    if not text:

        return ""

    return text.strip()


# ============================================================
# TEMPLATE GLOBAL DATA
# ============================================================

def inject_global_data():

    contact = admin_contact()

    return {

        # ----------------------------------------------------
        # SYSTEM
        # ----------------------------------------------------

        "current_year": current_year(),


        # ----------------------------------------------------
        # CURRENT ADMIN OBJECT
        # ----------------------------------------------------

        "current_admin": current_admin(),


        # ----------------------------------------------------
        # ADMIN BASIC INFORMATION
        # ----------------------------------------------------

        "admin_name": admin_name(),

        "admin_role": admin_role(),


        # ----------------------------------------------------
        # ADMIN CONTACT INFORMATION
        # ----------------------------------------------------

        "admin_contact": contact,

        "admin_contact_name": contact.get(

            "name",

            ""

        ),

        "admin_contact_email": contact.get(

            "email",

            ""

        ),

        "admin_contact_phone": contact.get(

            "phone",

            ""

        ),

        "admin_facebook_url": contact.get(

            "facebook",

            ""

        ),


        # ----------------------------------------------------
        # MEMBER DATA
        # ----------------------------------------------------

        "categories": member_categories(),

        "blood_groups": blood_groups(),

        "genders": gender_list(),

        "district": district_name()

    }

