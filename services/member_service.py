
# ============================================================
# JUians of Gaibandha
# Member Service
# Automatic Alumni + Verification + Privacy Support
# ============================================================

from datetime import datetime

from sqlalchemy import or_

from extensions import db
from models import Information


# ============================================================
# ACADEMIC YEAR
# ============================================================

def get_current_academic_year():
    current_year = datetime.now().year
    return f"{current_year}-{current_year + 1}"


# ============================================================
# CURRENT ACADEMIC START YEAR
# ============================================================

def get_current_academic_start_year():
    return datetime.now().year


# ============================================================
# NORMALIZE SESSION
# ============================================================

def normalize_session(session):
    """
    Normalize supported session formats.

    Supported:
        2020-2021
        2020 / 2021
        2020_2021
        2020 - 2021

    Returns:
        (start_year, end_year)
        or
        (None, None)
    """

    if not session:
        return None, None

    try:
        value = str(session).strip()

        if not value:
            return None, None

        value = (
            value
            .replace(" ", "")
            .replace("/", "-")
            .replace("_", "-")
        )

        parts = value.split("-")

        if len(parts) != 2:
            return None, None

        start_year = int(parts[0])
        end_year = int(parts[1])

        if start_year < 1900:
            return None, None

        if end_year != start_year + 1:
            return None, None

        return start_year, end_year

    except (ValueError, TypeError, AttributeError):
        return None, None


# ============================================================
# CHECK SESSION AGE
# ============================================================

def should_be_alumni(session):
    """
    Automatic Alumni rule:

        Current year - session start year >= 7

    Example in 2026:

        2019-2020 -> Alumni
        2020-2021 -> Alumni
        2021-2022 -> Running Student
        2022-2023 -> Running Student

    Invalid / N/A sessions are ignored.
    """

    start_year, end_year = normalize_session(session)

    if start_year is None:
        return False

    current_start_year = get_current_academic_start_year()

    return (
        current_start_year - start_year
    ) >= 7


# ============================================================
# AUTOMATIC RUNNING STUDENT -> ALUMNI
# ============================================================

def update_student_categories():
    """
    Convert only APPROVED Running Students to Alumni
    when their academic session is old enough.

    Pending and Rejected members are NEVER modified.

    Existing Alumni, Teachers and Employees are NEVER
    modified by this function.
    """

    students = (
        Information.query
        .filter(
            Information.category == "Running Student",
            Information.status == "Approved"
        )
        .all()
    )

    updated = False

    for member in students:

        if should_be_alumni(member.session):

            member.category = "Alumni"

            updated = True

    if updated:

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise


# ============================================================
# CREATE MEMBER
# ============================================================

def create_member(member):

    db.session.add(member)
    db.session.commit()

    return member


# ============================================================
# UPDATE MEMBER
# ============================================================

def update_member(member):

    if member is None:
        return None

    try:
        db.session.commit()

        return member

    except Exception:
        db.session.rollback()
        raise


# ============================================================
# DELETE MEMBER
# ============================================================

def delete_member(member):

    if member is None:
        return False

    try:

        db.session.delete(member)
        db.session.commit()

        return True

    except Exception:
        db.session.rollback()
        raise


# ============================================================
# GET MEMBER BY ID
# ============================================================

def get_member(member_id):

    update_student_categories()

    return db.session.get(
        Information,
        member_id
    )


# ============================================================
# GET ALL MEMBERS
# ============================================================

def get_all_members():

    update_student_categories()

    return (
        Information.query
        .order_by(
            Information.created_at.desc()
        )
        .all()
    )


# ============================================================
# GET LATEST APPROVED MEMBERS
# ============================================================

def get_latest_members(limit=6):

    update_student_categories()

    return (
        Information.query
        .filter(
            Information.status == "Approved"
        )
        .order_by(
            Information.created_at.desc()
        )
        .limit(limit)
        .all()
    )


# ============================================================
# GET CATEGORY MEMBERS
# ============================================================

def get_category_members(category):

    update_student_categories()

    return (
        Information.query
        .filter(
            Information.category == category,
            Information.status == "Approved"
        )
        .order_by(
            Information.created_at.desc()
        )
        .all()
    )


# ============================================================
# SEARCH MEMBERS
# ============================================================

def search_members(keyword):

    update_student_categories()

    if not keyword:
        return []

    keyword = str(keyword).strip()

    if not keyword:
        return []

    search = f"%{keyword}%"

    return (
        Information.query
        .filter(
            Information.status == "Approved",
            or_(
                Information.full_name.ilike(search),
                Information.department.ilike(search),
                Information.category.ilike(search),
                Information.phone.ilike(search),
                Information.batch.ilike(search),
                Information.session.ilike(search),
                Information.district.ilike(search)
            )
        )
        .order_by(
            Information.created_at.desc()
        )
        .all()
    )


# ============================================================
# APPROVE MEMBER
# ============================================================

def approve_member(
    member,
    approved_by=None
):
    """
    Approve a member.

    approved_by:
        Admin username/name performing approval.

    After approval, the automatic Alumni rule is checked.
    """

    if member is None:
        return None

    member.status = "Approved"

    if approved_by:
        member.approved_by = str(approved_by).strip()

    member.approved_at = datetime.utcnow()

    try:

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    # --------------------------------------------------------
    # Immediately check Alumni status.
    # --------------------------------------------------------

    if (
        member.category == "Running Student"
        and should_be_alumni(member.session)
    ):

        member.category = "Alumni"

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    return member


# ============================================================
# REJECT MEMBER
# ============================================================

def reject_member(
    member,
    rejected_by=None
):
    """
    Reject a member.

    Rejection does not expose the member publicly.
    """

    if member is None:
        return None

    member.status = "Rejected"

    # --------------------------------------------------------
    # Keep approval metadata clean.
    # --------------------------------------------------------

    member.approved_by = None
    member.approved_at = None

    try:

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return member


# ============================================================
# PENDING MEMBERS
# ============================================================

def get_pending_members(limit=None):

    query = (
        Information.query
        .filter(
            Information.status == "Pending"
        )
        .order_by(
            Information.created_at.desc()
        )
    )

    if limit:
        query = query.limit(limit)

    return query.all()


# ============================================================
# APPROVED MEMBERS
# ============================================================

def get_approved_members(limit=None):

    update_student_categories()

    query = (
        Information.query
        .filter(
            Information.status == "Approved"
        )
        .order_by(
            Information.created_at.desc()
        )
    )

    if limit:
        query = query.limit(limit)

    return query.all()


# ============================================================
# REJECTED MEMBERS
# ============================================================

def get_rejected_members(limit=None):

    query = (
        Information.query
        .filter(
            Information.status == "Rejected"
        )
        .order_by(
            Information.created_at.desc()
        )
    )

    if limit:
        query = query.limit(limit)

    return query.all()


# ============================================================
# MEMBER STATISTICS
# ============================================================

def get_statistics():

    update_student_categories()

    return {

        "total_members":
            Information.query.count(),

        "total_alumni":
            Information.query.filter_by(
                category="Alumni"
            ).count(),

        "total_students":
            Information.query.filter_by(
                category="Running Student"
            ).count(),

        "total_teachers":
            Information.query.filter_by(
                category="Teacher"
            ).count(),

        "total_employees":
            Information.query.filter_by(
                category="Employee"
            ).count(),

        "pending":
            Information.query.filter_by(
                status="Pending"
            ).count(),

        "approved":
            Information.query.filter_by(
                status="Approved"
            ).count(),

        "rejected":
            Information.query.filter_by(
                status="Rejected"
            ).count()
    }


# ============================================================
# API COMPATIBILITY
# ============================================================

def get_member_statistics():

    return get_statistics()


# ============================================================
# CHECK PHONE EXISTS
# ============================================================

def phone_exists(phone):

    if not phone:
        return None

    return (
        Information.query
        .filter_by(
            phone=phone
        )
        .first()
    )


# ============================================================
# CHECK EMAIL EXISTS
# ============================================================

def email_exists(email):

    if not email:
        return None

    return (
        Information.query
        .filter_by(
            email=email
        )
        .first()
    )
