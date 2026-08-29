# ============================================================
# JUians of Gaibandha
# Home Routes
# ============================================================

from datetime import datetime

from flask import (
    Blueprint,
    render_template
)

from extensions import db

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
# DEFAULT EVENT IMAGE
# ============================================================

DEFAULT_EVENT_IMAGE = (
    "images/Event_1.1.jpeg"
)


# ============================================================
# EVENT DATE SORTING
# ============================================================

_BANGLA_DIGITS = str.maketrans(
    "০১২৩৪৫৬৭৮৯",
    "0123456789",
)

_BANGLA_MONTHS = {
    "জানুয়ারি": "January",
    "জানুয়ারি": "January",
    "ফেব্রুয়ারি": "February",
    "ফেব্রুয়ারি": "February",
    "মার্চ": "March",
    "এপ্রিল": "April",
    "মে": "May",
    "জুন": "June",
    "জুলাই": "July",
    "আগস্ট": "August",
    "সেপ্টেম্বর": "September",
    "অক্টোবর": "October",
    "নভেম্বর": "November",
    "ডিসেম্বর": "December",
}

_EVENT_DATE_FORMATS = (
    "%d %B %Y",
    "%d %B, %Y",
    "%d %b %Y",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d-%B-%Y",
)


def _event_sort_key(event):
    """Return a sortable date key; newest valid event date comes first."""

    value = str(
        event.event_date or ""
    ).strip().translate(
        _BANGLA_DIGITS
    )

    value = " ".join(
        value.split()
    )

    for bangla_month, english_month in _BANGLA_MONTHS.items():
        value = value.replace(
            bangla_month,
            english_month,
        )

    for date_format in _EVENT_DATE_FORMATS:

        try:
            parsed_date = datetime.strptime(
                value,
                date_format,
            )

            return (
                parsed_date,
                event.created_at or datetime.min,
            )

        except ValueError:
            continue

    return (
        datetime.min,
        event.created_at or datetime.min,
    )


# ============================================================
# EVENT IMAGE NORMALIZER
# ============================================================

def _normalize_event_image_path(
    image_path
):

    """
    Normalize stored event image paths.

    Supported database values:

    images/example.jpg
    uploads/example.jpg
    static/images/example.jpg
    static/uploads/example.jpg
    example.jpg
    """

    if not image_path:

        return (
            DEFAULT_EVENT_IMAGE
        )


    image_path = str(
        image_path
    ).strip()


    if not image_path:

        return (
            DEFAULT_EVENT_IMAGE
        )


    if image_path.startswith((
        "https://",
        "http://"
    )):

        return image_path


    image_path = (
        image_path.lstrip("/")
    )


    # --------------------------------------------------------
    # Already Correct
    # --------------------------------------------------------

    if image_path.startswith(
        "images/"
    ):

        return image_path


    if image_path.startswith(
        "uploads/"
    ):

        return image_path


    # --------------------------------------------------------
    # Remove static/ Prefix
    # --------------------------------------------------------

    if image_path.startswith(
        "static/images/"
    ):

        return image_path.replace(
            "static/",
            "",
            1
        )


    if image_path.startswith(
        "static/uploads/"
    ):

        return image_path.replace(
            "static/",
            "",
            1
        )


    # --------------------------------------------------------
    # Old Database Filename
    # --------------------------------------------------------

    return (
        f"uploads/{image_path}"
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
    # PUBLIC MEMBER STATISTICS
    # ========================================================
    #
    # Only approved members should appear in the
    # public directory statistics.
    # ========================================================

    total_members = (
        Information.query
        .filter_by(
            status="Approved"
        )
        .count()
    )


    total_alumni = (
        Information.query
        .filter_by(
            category="Alumni",
            status="Approved"
        )
        .count()
    )


    total_students = (
        Information.query
        .filter_by(
            category="Running Student",
            status="Approved"
        )
        .count()
    )


    total_teachers = (
        Information.query
        .filter_by(
            category="Teacher",
            status="Approved"
        )
        .count()
    )


    total_employees = (
        Information.query
        .filter_by(
            category="Employee",
            status="Approved"
        )
        .count()
    )


    # ========================================================
    # STATUS STATISTICS
    # ========================================================

    total_pending = (
        Information.query
        .filter_by(
            status="Pending"
        )
        .count()
    )


    total_approved = (
        Information.query
        .filter_by(
            status="Approved"
        )
        .count()
    )


    total_rejected = (
        Information.query
        .filter_by(
            status="Rejected"
        )
        .count()
    )


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
    # Maximum 5 events are loaded so the existing
    # Recent Events section remains clean.
    # ========================================================

    published_events = (
        Event.query
        .filter_by(
            is_published=True
        )
        .all()
    )

    recent_events = sorted(
        published_events,
        key=_event_sort_key,
        reverse=True,
    )[:5]
    # ========================================================
    # NORMALIZE EVENT IMAGE PATHS
    # ========================================================

    try:

        changed = False


        for event in recent_events:

            normalized_path = (
                _normalize_event_image_path(
                    event.image
                )
            )


            if (
                event.image
                != normalized_path
            ):

                event.image = (
                    normalized_path
                )

                changed = True


        if changed:

            db.session.commit()


    except Exception:

        db.session.rollback()


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
        # uses:
        #
        #     {% if events %}
        #     {% for event in events %}
        #
        # Keep "events" as an alias of recent_events.
        # ----------------------------------------------------

        events=recent_events

    )


# ============================================================
# ALL PUBLISHED EVENTS
# ============================================================

@home_bp.route("/events")
def all_events():

    events = (
        Event.query
        .filter_by(
            is_published=True
        )
        .all()
    )

    events = sorted(
        events,
        key=_event_sort_key,
        reverse=True,
    )

    for event in events:

        event.image = (
            _normalize_event_image_path(
                event.image
            )
        )

    return render_template(
        "events.html",
        events=events,
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

    db.session.rollback()

    return (
        "500 - Internal Server Error",
        500
    )


# ============================================================
# END OF FILE
# ============================================================
