
# ============================================================
# JUians of Gaibandha
# Home Routes
# ============================================================

from flask import (
    Blueprint,
    render_template
)

from models import (
    Information,
    Event
)

from utils.helpers import (
    inject_global_data
)


# ============================================================
# BLUEPRINT
# ============================================================

home_bp = Blueprint(
    "home",
    __name__
)


# ============================================================
# CONTEXT PROCESSOR
# ============================================================

@home_bp.app_context_processor
def global_context():

    return inject_global_data()


# ============================================================
# HOME PAGE
# ============================================================

@home_bp.route("/")
def home():

    # ========================================================
    # MEMBER STATISTICS
    # ========================================================

    total_members = Information.query.count()

    total_alumni = Information.query.filter_by(
        category="Alumni"
    ).count()

    total_students = Information.query.filter_by(
        category="Running Student"
    ).count()

    total_teachers = Information.query.filter_by(
        category="Teacher"
    ).count()

    total_employees = Information.query.filter_by(
        category="Employee"
    ).count()


    # ========================================================
    # STATUS STATISTICS
    # ========================================================

    total_pending = Information.query.filter_by(
        status="Pending"
    ).count()

    total_approved = Information.query.filter_by(
        status="Approved"
    ).count()

    total_rejected = Information.query.filter_by(
        status="Rejected"
    ).count()


    # ========================================================
    # LATEST APPROVED MEMBERS
    # ========================================================

    latest_members = (

        Information.query

        .filter_by(
            status="Approved"
        )

        .order_by(
            Information.created_at.desc()
        )

        .limit(6)

        .all()

    )


    # ========================================================
    # RECENT EVENTS
    # ========================================================
    #
    # Only published events will appear on the
    # public homepage.
    #
    # Latest events are shown first.
    #
    # Maximum 6 events are loaded so the existing
    # Recent Events section remains clean.
    # ========================================================

    recent_events = (

        Event.query

        .filter_by(
            is_published=True
        )

        .order_by(
            Event.created_at.desc()
        )

        .limit(6)

        .all()

    )


    # ========================================================
    # HOME PAGE
    # ========================================================

    return render_template(

        "index.html",

        # ----------------------------------------------------
        # MEMBER STATISTICS
        # ----------------------------------------------------

        total_members=total_members,

        total_alumni=total_alumni,

        total_students=total_students,

        total_teachers=total_teachers,

        total_employees=total_employees,


        # ----------------------------------------------------
        # STATUS STATISTICS
        # ----------------------------------------------------

        total_pending=total_pending,

        total_approved=total_approved,

        total_rejected=total_rejected,


        # ----------------------------------------------------
        # LATEST MEMBERS
        # ----------------------------------------------------

        latest_members=latest_members,


        # ----------------------------------------------------
        # RECENT EVENTS
        # ----------------------------------------------------

        recent_events=recent_events,


        # ----------------------------------------------------
        # TEMPLATE COMPATIBILITY
        #
        # The existing sections/recent_events.html
        # currently uses:
        #
        #     {% if events %}
        #     {% for event in events %}
        #
        # Therefore, keep "events" as an alias of
        # "recent_events".
        #
        # This avoids changing the existing design/template.
        # ----------------------------------------------------

        events=recent_events

    )


# ============================================================
# ERROR 404
# ============================================================

@home_bp.app_errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


# ============================================================
# ERROR 500
# ============================================================

@home_bp.app_errorhandler(500)
def internal_error(error):

    from extensions import db

    db.session.rollback()

    return render_template(
        "500.html"
    ), 500
