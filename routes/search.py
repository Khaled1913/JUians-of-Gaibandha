
# =====================================================
# routes/search.py
# JUians of Gaibandha Portal
# Secure Member Search Routes
# =====================================================

from flask import (
    Blueprint,
    render_template,
    request
)

from sqlalchemy import or_

from models import Information


# =====================================================
# BLUEPRINT
# =====================================================

search_bp = Blueprint(
    "search",
    __name__,
    url_prefix="/search"
)


# =====================================================
# PUBLIC SEARCH FILTER
# =====================================================
# IMPORTANT:
# -----------------------------------------------------
# Only APPROVED members are searchable publicly.
#
# Sensitive fields such as:
#   - phone
#   - email
#   - registration_no
#   - student_id
#   - present_address
#   - permanent_address
#   - date_of_birth
#   - blood_group
#   - social media
#
# are NOT used for public search.
#
# This prevents someone from discovering members by
# entering private information into the search box.
# =====================================================

PUBLIC_STATUS = "Approved"


# =====================================================
# GLOBAL SEARCH
# =====================================================

@search_bp.route(
    "/",
    methods=["GET"]
)
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    department = request.args.get(
        "department",
        ""
    ).strip()

    session_year = request.args.get(
        "session",
        ""
    ).strip()

    members = []


    # =================================================
    # SEARCH / FILTER
    # =================================================

    if query or category or department or session_year:

        filters = []


        # =============================================
        # KEYWORD SEARCH
        # =============================================
        # Public searchable information:
        #
        # Name
        # Department
        # Batch
        # Session
        # Occupation
        # Company
        # Designation
        # Upazila
        # District
        #
        # PRIVATE DATA IS NOT SEARCHABLE.
        # =============================================

        if query:

            keyword = f"%{query}%"

            filters.append(

                or_(

                    Information.full_name.ilike(
                        keyword
                    ),

                    Information.department.ilike(
                        keyword
                    ),

                    Information.batch.ilike(
                        keyword
                    ),

                    Information.session.ilike(
                        keyword
                    ),

                    Information.occupation.ilike(
                        keyword
                    ),

                    Information.company.ilike(
                        keyword
                    ),

                    Information.designation.ilike(
                        keyword
                    ),

                    Information.upazila.ilike(
                        keyword
                    ),

                    Information.district.ilike(
                        keyword
                    )

                )

            )


        # =============================================
        # CATEGORY FILTER
        # =============================================

        if category:

            filters.append(

                Information.category.ilike(
                    category
                )

            )


        # =============================================
        # DEPARTMENT FILTER
        # =============================================

        if department:

            filters.append(

                Information.department.ilike(
                    f"%{department}%"
                )

            )


        # =============================================
        # SESSION FILTER
        # =============================================

        if session_year:

            filters.append(

                Information.session.ilike(
                    f"%{session_year}%"
                )

            )


        # =============================================
        # APPROVED MEMBERS ONLY
        # =============================================

        filters.append(

            Information.status.ilike(
                PUBLIC_STATUS
            )

        )


        # =============================================
        # DATABASE SEARCH
        # =============================================

        members = (

            Information.query

            .filter(
                *filters
            )

            .order_by(
                Information.created_at.desc()
            )

            .all()

        )


    # =================================================
    # RESULT PAGE
    # =================================================

    return render_template(

        "search/results.html",

        # Main result variable
        results=members,

        # Backward compatibility
        members=members,

        query=query,

        category=category,

        department=department,

        session=session_year

    )


# =====================================================
# QUICK NAME SEARCH
# =====================================================

@search_bp.route(
    "/name"
)
def search_by_name():

    name = request.args.get(
        "name",
        ""
    ).strip()

    members = []


    if name:

        members = (

            Information.query

            .filter(

                Information.full_name.ilike(
                    f"%{name}%"
                ),

                Information.status.ilike(
                    PUBLIC_STATUS
                )

            )

            .order_by(
                Information.created_at.desc()
            )

            .all()

        )


    return render_template(

        "search/results.html",

        results=members,

        members=members,

        query=name

    )


# =====================================================
# CATEGORY SEARCH
# =====================================================

@search_bp.route(
    "/category/<string:category>"
)
def search_by_category(category):

    members = (

        Information.query

        .filter(

            Information.category.ilike(
                category
            ),

            Information.status.ilike(
                PUBLIC_STATUS
            )

        )

        .order_by(
            Information.created_at.desc()
        )

        .all()

    )


    return render_template(

        "search/results.html",

        results=members,

        members=members,

        category=category,

        query=""

    )


# =====================================================
# DEPARTMENT SEARCH
# =====================================================

@search_bp.route(
    "/department/<path:department>"
)
def search_by_department(department):

    members = (

        Information.query

        .filter(

            Information.department.ilike(
                f"%{department}%"
            ),

            Information.status.ilike(
                PUBLIC_STATUS
            )

        )

        .order_by(
            Information.created_at.desc()
        )

        .all()

    )


    return render_template(

        "search/results.html",

        results=members,

        members=members,

        department=department,

        query=""

    )


# =====================================================
# SESSION / BATCH SEARCH
# =====================================================

@search_bp.route(
    "/session/<string:session_year>"
)
def search_by_session(session_year):

    members = (

        Information.query

        .filter(

            Information.session.ilike(
                f"%{session_year}%"
            ),

            Information.status.ilike(
                PUBLIC_STATUS
            )

        )

        .order_by(
            Information.created_at.desc()
        )

        .all()

    )


    return render_template(

        "search/results.html",

        results=members,

        members=members,

        session=session_year,

        query=""

    )
