# ============================================================
# JUians of Gaibandha
# Premium Admin Routes
# ============================================================

from datetime import date

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request,
)

from sqlalchemy import or_, func

from werkzeug.security import generate_password_hash

from extensions import db
from models import Information, Admin, Event, EventImage
from utils.decorators import admin_required

from services.member_service import (
    get_member_statistics,
    approve_member,
    reject_member,
    delete_member,
    update_student_categories,
)

from services.upload_service import (
    upload_photo,
    replace_photo,
    upload_event_image,
    delete_photo,
)


# ============================================================
# BLUEPRINT
# ============================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
)


# ============================================================
# DEFAULT EVENT IMAGE
# ============================================================

DEFAULT_EVENT_IMAGE = "images/Event_1.1.jpeg"

MAX_EVENT_IMAGES = 4

EVENT_PLACEHOLDER_IMAGES = {
    DEFAULT_EVENT_IMAGE,
    "images/ju_campus.jpeg",
}


# ============================================================
# EVENT IMAGE NORMALIZER
# ============================================================

def _normalize_event_image_path(image_path):
    """
    Normalize event image path so templates can safely use:

        url_for("static", filename=event.image)

    Supported formats:

        images/example.jpg
        uploads/example.jpg
        example.jpg

    Empty values use the default event image.
    """

    if not image_path:
        return DEFAULT_EVENT_IMAGE

    image_path = str(image_path).strip()

    if not image_path:
        return DEFAULT_EVENT_IMAGE

    image_path = image_path.lstrip("/")

    if image_path.startswith("images/"):
        return image_path

    if image_path.startswith("uploads/"):
        return image_path

    if image_path.startswith("static/images/"):

        return image_path.replace(
            "static/",
            "",
            1,
        )

    if image_path.startswith("static/uploads/"):

        return image_path.replace(
            "static/",
            "",
            1,
        )

    return f"uploads/{image_path}"


def _selected_event_image_files():

    """Return non-empty multi-image uploads, including legacy form input."""

    files = [
        image
        for image in request.files.getlist("images")
        if image and image.filename
    ]

    legacy_image = request.files.get("image")

    if (
        legacy_image
        and legacy_image.filename
        and legacy_image not in files
    ):

        files.append(legacy_image)

    return files


def _upload_event_images(files):

    """Upload a validated collection and clean up if any item fails."""

    uploaded_paths = []

    try:

        for image in files:

            uploaded_path = upload_event_image(image)

            if not uploaded_path:

                raise ValueError(
                    "Please upload valid JPG, JPEG, PNG, GIF or WebP images under 10 MB each."
                )

            uploaded_paths.append(
                _normalize_event_image_path(uploaded_path)
            )

    except Exception:

        for uploaded_path in uploaded_paths:

            delete_photo(uploaded_path)

        raise

    return uploaded_paths


def _set_event_image_paths(event, image_paths):

    """Set the primary image and rebuild the ordered gallery."""

    image_paths = [
        _normalize_event_image_path(path)
        for path in image_paths
        if path
    ][:MAX_EVENT_IMAGES]

    event.image = (
        image_paths[0]
        if image_paths
        else DEFAULT_EVENT_IMAGE
    )

    event.gallery_images.clear()

    for position, image_path in enumerate(
        image_paths[1:],
        start=1,
    ):

        event.gallery_images.append(
            EventImage(
                image_path=image_path,
                position=position,
            )
        )


# ============================================================
# CURRENT ADMIN
# ============================================================

def _current_admin():

    admin_id = session.get(
        "admin_id"
    )

    if not admin_id:
        return None

    return db.session.get(
        Admin,
        admin_id,
    )


# ============================================================
# ADMIN TERM YEAR VALIDATOR
# ============================================================

def _parse_term_year(value):

    value = str(
        value or ""
    ).strip()

    if not value:
        return None

    try:

        year = int(value)

    except (TypeError, ValueError):

        return None

    if year < 2000 or year > 2100:
        return None

    return year


# ============================================================
# NORMALIZE CASE-INSENSITIVE VALUES
# ============================================================

def _normalize_identifier(value):

    return str(
        value or ""
    ).strip().lower()


# ============================================================
# ADMIN CONTEXT
# ============================================================

def _get_admin_context():

    try:

        update_student_categories()

    except Exception:

        db.session.rollback()

    try:

        statistics = (
            get_member_statistics()
            or {}
        )

    except Exception:

        statistics = {}

    pending_members = (
        Information.query
        .filter_by(
            status="Pending"
        )
        .order_by(
            Information.created_at.desc()
        )
        .all()
    )

    approved_members = (
        Information.query
        .filter_by(
            status="Approved"
        )
        .order_by(
            Information.created_at.desc()
        )
        .limit(10)
        .all()
    )

    members = (
        Information.query
        .order_by(
            Information.created_at.desc()
        )
        .all()
    )

    events = (
        Event.query
        .order_by(
            Event.created_at.desc()
        )
        .all()
    )

    try:

        changed = False

        for event in events:

            normalized_path = (
                _normalize_event_image_path(
                    event.image
                )
            )

            if event.image != normalized_path:

                event.image = (
                    normalized_path
                )

                changed = True

        if changed:

            db.session.commit()

    except Exception:

        db.session.rollback()

    published_events = (
        Event.query
        .filter_by(
            is_published=True
        )
        .order_by(
            Event.created_at.desc()
        )
        .limit(10)
        .all()
    )

    current_administrator = (
        Admin.query
        .filter_by(
            is_current=True
        )
        .order_by(
            Admin.id.desc()
        )
        .first()
    )

    return {

        "statistics": statistics,

        "total_members": statistics.get(
            "total_members",
            0,
        ),

        "total_alumni": statistics.get(
            "total_alumni",
            0,
        ),

        "total_students": statistics.get(
            "total_students",
            0,
        ),

        "total_teachers": statistics.get(
            "total_teachers",
            0,
        ),

        "total_employees": statistics.get(
            "total_employees",
            0,
        ),

        "pending": statistics.get(
            "pending",
            0,
        ),

        "approved": statistics.get(
            "approved",
            0,
        ),

        "rejected": statistics.get(
            "rejected",
            0,
        ),

        "members": members,

        "pending_members": (
            pending_members
        ),

        "approved_members": (
            approved_members
        ),

        "events": events,

        "published_events": (
            published_events
        ),

        "admin": _current_admin(),

        "current_administrator": (
            current_administrator
        ),
    }


# ============================================================
# DASHBOARD
# ============================================================

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():

    return render_template(
        "admin.html",
        **_get_admin_context(),
    )


# ============================================================
# PENDING REQUESTS
# ============================================================

@admin_bp.route("/pending")
@admin_required
def pending_members():

    try:

        update_student_categories()

    except Exception:

        db.session.rollback()

    members = (
        Information.query
        .filter_by(
            status="Pending"
        )
        .order_by(
            Information.created_at.desc()
        )
        .all()
    )

    statistics = (
        get_member_statistics()
        or {}
    )

    return render_template(

        "pending.html",

        members=members,

        pending_members=members,

        pending=statistics.get(
            "pending",
            0,
        ),

        approved=statistics.get(
            "approved",
            0,
        ),

        rejected=statistics.get(
            "rejected",
            0,
        ),

        admin=_current_admin(),
    )


# ============================================================
# APPROVE MEMBER
# ============================================================

@admin_bp.route(
    "/approve/<int:id>"
)
@admin_required
def approve(id):

    member = (
        Information.query
        .get_or_404(id)
    )

    try:

        approve_member(
            member
        )

        flash(
            "Member approved successfully.",
            "success",
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Approval failed: {exc}",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for(
            "admin.dashboard"
        )
    )


# ============================================================
# REJECT MEMBER
# ============================================================

@admin_bp.route(
    "/reject/<int:id>"
)
@admin_required
def reject(id):

    member = (
        Information.query
        .get_or_404(id)
    )

    try:

        reject_member(
            member
        )

        flash(
            "Member rejected successfully.",
            "warning",
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Rejection failed: {exc}",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for(
            "admin.pending_members"
        )
    )


# ============================================================
# DELETE MEMBER
# ============================================================

@admin_bp.route(
    "/delete/<int:id>"
)
@admin_required
def delete(id):

    member = (
        Information.query
        .get_or_404(id)
    )

    try:

        delete_member(
            member
        )

        flash(
            "Member deleted successfully.",
            "success",
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Delete failed: {exc}",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for(
            "admin.members"
        )
    )


# ============================================================
# ADMIN MEMBER DETAILS
# ============================================================

@admin_bp.route(
    "/member/<int:id>"
)
@admin_required
def member_details(id):

    try:

        update_student_categories()

    except Exception:

        db.session.rollback()

    member = (
        Information.query
        .get_or_404(id)
    )

    return render_template(

        "member_details.html",

        member=member,

        admin_view=True,

        admin=_current_admin(),
    )


# ============================================================
# EDIT MEMBER
# ============================================================

@admin_bp.route(
    "/member/<int:id>/edit",
    methods=["GET", "POST"],
)
@admin_required
def edit_member(id):

    try:

        update_student_categories()

    except Exception:

        db.session.rollback()

    member = (
        Information.query
        .get_or_404(id)
    )

    if request.method == "GET":

        return render_template(

            "admin_edit_member.html",

            member=member,

            admin=_current_admin(),
        )

    full_name = request.form.get(
        "full_name",
        "",
    ).strip()

    category = request.form.get(
        "category",
        "",
    ).strip()

    gender = request.form.get(
        "gender",
        "",
    ).strip()

    date_of_birth = request.form.get(
        "date_of_birth",
        "",
    ).strip()

    blood_group = request.form.get(
        "blood_group",
        "",
    ).strip()

    phone = request.form.get(
        "phone",
        "",
    ).strip()

    department = request.form.get(
        "department",
        "",
    ).strip()

    batch = request.form.get(
        "batch",
        "",
    ).strip()

    session_value = (
        request.form.get(
            "session",
            "",
        ).strip()
    )

    email = request.form.get(
        "email",
        "",
    ).strip()

    district = request.form.get(
        "district",
        "",
    ).strip()

    upazila = request.form.get(
        "upazila",
        "",
    ).strip()

    present_address = (
        request.form.get(
            "present_address",
            "",
        ).strip()
    )

    permanent_address = (
        request.form.get(
            "permanent_address",
            "",
        ).strip()
    )

    occupation = request.form.get(
        "occupation",
        "",
    ).strip()

    company = request.form.get(
        "company",
        "",
    ).strip()

    designation = request.form.get(
        "designation",
        "",
    ).strip()

    facebook = request.form.get(
        "facebook",
        "",
    ).strip()

    if not full_name:

        flash(
            "Full name is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_member",
                id=member.id,
            )
        )

    if not category:

        flash(
            "Category is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_member",
                id=member.id,
            )
        )

    if not department:

        flash(
            "Department is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_member",
                id=member.id,
            )
        )

    if not phone:

        flash(
            "Mobile number is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_member",
                id=member.id,
            )
        )

    allowed_categories = {
        "Alumni",
        "Running Student",
        "Teacher",
        "Employee",
    }

    if category not in allowed_categories:

        flash(
            "Invalid member category.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_member",
                id=member.id,
            )
        )

    if email:

        import re

        email_pattern = (
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        if not re.match(
            email_pattern,
            email,
        ):

            flash(
                "Please enter a valid email address.",
                "danger",
            )

            return redirect(
                url_for(
                    "admin.edit_member",
                    id=member.id,
                )
            )

    existing_phone = (
        Information.query
        .filter(
            Information.phone == phone,
            Information.id != member.id,
        )
        .first()
    )

    if existing_phone:

        flash(
            "This mobile number is already used by another member.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_member",
                id=member.id,
            )
        )

    if email:

        normalized_email = (
            _normalize_identifier(
                email
            )
        )

        existing_email = (
            Information.query
            .filter(
                func.lower(
                    Information.email
                ) == normalized_email,
                Information.id != member.id,
            )
            .first()
        )

        if existing_email:

            flash(
                "This email address is already used by another member.",
                "danger",
            )

            return redirect(
                url_for(
                    "admin.edit_member",
                    id=member.id,
                )
            )

    new_photo = (
        request.files.get(
            "photo"
        )
    )

    updated_photo = (
        member.photo
    )

    if (
        new_photo
        and new_photo.filename
    ):

        try:

            updated_photo = (
                replace_photo(
                    member.photo,
                    new_photo,
                )
            )

        except Exception as exc:

            flash(
                f"Photo update failed: {exc}",
                "danger",
            )

            return redirect(
                url_for(
                    "admin.edit_member",
                    id=member.id,
                )
            )

    try:

        member.full_name = (
            full_name
        )

        member.category = (
            category
        )

        member.gender = (
            gender or None
        )

        member.date_of_birth = (
            date_of_birth or None
        )

        member.blood_group = (
            blood_group or None
        )

        member.phone = (
            phone
        )

        member.department = (
            department
        )

        if hasattr(
            member,
            "batch",
        ):

            member.batch = (
                batch or None
            )

        if hasattr(
            member,
            "session",
        ):

            member.session = (
                session_value or None
            )

        member.email = (
            _normalize_identifier(email)
            if email
            else None
        )

        member.district = (
            district
            or "Gaibandha"
        )

        member.upazila = (
            upazila or None
        )

        member.present_address = (
            present_address or None
        )

        member.permanent_address = (
            permanent_address or None
        )

        member.occupation = (
            occupation or None
        )

        member.company = (
            company or None
        )

        member.designation = (
            designation or None
        )

        member.facebook = (
            facebook or None
        )

        member.photo = (
            updated_photo
        )

        db.session.commit()

        flash(
            "Member information updated successfully.",
            "success",
        )

        return redirect(
            url_for(
                "admin.member_details",
                id=member.id,
            )
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Member update failed: {exc}",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_member",
                id=member.id,
            )
        )


# ============================================================
# ALL MEMBERS
# ============================================================

@admin_bp.route("/members")
@admin_required
def members():

    try:

        update_student_categories()

    except Exception:

        db.session.rollback()

    keyword = request.args.get(
        "q",
        "",
    ).strip()

    category = request.args.get(
        "category",
        "",
    ).strip()

    status = request.args.get(
        "status",
        "",
    ).strip()

    query = Information.query

    if keyword:

        search = (
            f"%{keyword}%"
        )

        search_fields = [
            Information.full_name,
            Information.department,
            Information.phone,
            Information.email,
            Information.category,
        ]

        if hasattr(
            Information,
            "batch",
        ):

            search_fields.append(
                Information.batch
            )

        if hasattr(
            Information,
            "session",
        ):

            search_fields.append(
                Information.session
            )

        query = query.filter(
            or_(
                *[
                    field.ilike(
                        search
                    )
                    for field
                    in search_fields
                ]
            )
        )

    if category:

        query = query.filter_by(
            category=category
        )

    if status:

        query = query.filter_by(
            status=status
        )

    all_members = (
        query
        .order_by(
            Information.created_at.desc()
        )
        .all()
    )

    statistics = (
        get_member_statistics()
        or {}
    )

    return render_template(

        "admin_members.html",

        members=all_members,

        statistics=statistics,

        total_members=statistics.get(
            "total_members",
            0,
        ),

        total_alumni=statistics.get(
            "total_alumni",
            0,
        ),

        total_students=statistics.get(
            "total_students",
            0,
        ),

        total_teachers=statistics.get(
            "total_teachers",
            0,
        ),

        total_employees=statistics.get(
            "total_employees",
            0,
        ),

        pending=statistics.get(
            "pending",
            0,
        ),

        approved=statistics.get(
            "approved",
            0,
        ),

        rejected=statistics.get(
            "rejected",
            0,
        ),

        admin=_current_admin(),

        keyword=keyword,

        selected_category=category,

        selected_status=status,
    )


# ============================================================
# ALL EVENTS
# ============================================================

@admin_bp.route("/events")
@admin_required
def events():

    all_events = (
        Event.query
        .order_by(
            Event.created_at.desc()
        )
        .all()
    )

    try:

        changed = False

        for event in all_events:

            normalized_path = (
                _normalize_event_image_path(
                    event.image
                )
            )

            if event.image != normalized_path:

                event.image = (
                    normalized_path
                )

                changed = True

        if changed:

            db.session.commit()

    except Exception:

        db.session.rollback()

    return render_template(

        "admin_events.html",

        events=all_events,

        admin=_current_admin(),
    )


# ============================================================
# CREATE EVENT
# ============================================================

@admin_bp.route(
    "/events/add",
    methods=["GET", "POST"],
)
@admin_required
def create_event():

    if request.method == "GET":

        return render_template(

            "admin_event_form.html",

            event=None,

            admin=_current_admin(),
        )

    title = request.form.get(
        "title",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    event_date = request.form.get(
        "event_date",
        "",
    ).strip()

    location = request.form.get(
        "location",
        "",
    ).strip()

    event_link = request.form.get(
        "event_link",
        "",
    ).strip()

    is_published = (
        request.form.get(
            "is_published"
        )
        == "on"
    )

    if not title:

        flash(
            "Event title is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_event"
            )
        )

    if not description:

        flash(
            "Event description is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_event"
            )
        )

    if not event_date:

        flash(
            "Event date is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_event"
            )
        )

    image_files = (
        _selected_event_image_files()
    )

    if len(image_files) > MAX_EVENT_IMAGES:

        flash(
            f"You can upload a maximum of {MAX_EVENT_IMAGES} images for one event.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_event"
            )
        )

    try:

        uploaded_paths = (
            _upload_event_images(
                image_files
            )
        )

    except Exception as exc:

        flash(
            f"Event image upload failed: {exc}",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_event"
            )
        )

    try:

        event = Event(

            title=title,

            description=description,

            event_date=event_date,

            location=(
                location or None
            ),

            image=(
                uploaded_paths[0]
                if uploaded_paths
                else DEFAULT_EVENT_IMAGE
            ),

            event_link=(
                event_link or None
            ),

            is_published=(
                is_published
            ),
        )

        db.session.add(
            event
        )

        db.session.flush()

        _set_event_image_paths(
            event,
            uploaded_paths,
        )

        db.session.commit()

        flash(
            "Event created successfully.",
            "success",
        )

        return redirect(
            url_for(
                "admin.events"
            )
        )

    except Exception as exc:

        db.session.rollback()

        for uploaded_path in uploaded_paths:

            delete_photo(uploaded_path)

        flash(
            f"Event creation failed: {exc}",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_event"
            )
        )


# ============================================================
# EDIT EVENT
# ============================================================

@admin_bp.route(
    "/events/<int:id>/edit",
    methods=["GET", "POST"],
)
@admin_required
def edit_event(id):

    event = (
        Event.query
        .get_or_404(id)
    )

    if request.method == "GET":

        event.image = (
            _normalize_event_image_path(
                event.image
            )
        )

        return render_template(

            "admin_event_form.html",

            event=event,

            admin=_current_admin(),
        )

    title = request.form.get(
        "title",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    event_date = request.form.get(
        "event_date",
        "",
    ).strip()

    location = request.form.get(
        "location",
        "",
    ).strip()

    event_link = request.form.get(
        "event_link",
        "",
    ).strip()

    is_published = (
        request.form.get(
            "is_published"
        )
        == "on"
    )

    if not title:

        flash(
            "Event title is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_event",
                id=event.id,
            )
        )

    if not description:

        flash(
            "Event description is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_event",
                id=event.id,
            )
        )

    if not event_date:

        flash(
            "Event date is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_event",
                id=event.id,
            )
        )

    image_files = (
        _selected_event_image_files()
    )

    remove_primary = (
        request.form.get(
            "remove_primary_image"
        )
        == "on"
    )

    remove_gallery_ids = {
        int(image_id)
        for image_id in request.form.getlist(
            "remove_gallery_images"
        )
        if str(image_id).isdigit()
    }

    primary_path = (
        _normalize_event_image_path(
            event.image
        )
    )

    current_paths = [
        primary_path,
        *[
            _normalize_event_image_path(
                gallery_image.image_path
            )
            for gallery_image in event.gallery_images
        ],
    ]

    remaining_paths = []

    primary_is_placeholder = (
        primary_path
        in EVENT_PLACEHOLDER_IMAGES
    )

    if (
        not remove_primary
        and not (
            primary_is_placeholder
            and image_files
        )
    ):

        remaining_paths.append(
            primary_path
        )

    for gallery_image in event.gallery_images:

        if gallery_image.id not in remove_gallery_ids:

            remaining_paths.append(
                _normalize_event_image_path(
                    gallery_image.image_path
                )
            )

    if (
        len(remaining_paths)
        + len(image_files)
        > MAX_EVENT_IMAGES
    ):

        flash(
            f"An event can have a maximum of {MAX_EVENT_IMAGES} images. Remove an existing image before adding another.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_event",
                id=event.id,
            )
        )

    try:

        uploaded_paths = (
            _upload_event_images(
                image_files
            )
        )

    except Exception as exc:

        flash(
            f"Event image update failed: {exc}",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_event",
                id=event.id,
            )
        )

    final_paths = (
        remaining_paths
        + uploaded_paths
    )

    try:

        event.title = title

        event.description = (
            description
        )

        event.event_date = (
            event_date
        )

        event.location = (
            location or None
        )

        event.event_link = (
            event_link or None
        )

        _set_event_image_paths(
            event,
            final_paths,
        )

        event.is_published = (
            is_published
        )

        db.session.commit()

        for removed_path in set(
            current_paths
        ) - set(final_paths):

            delete_photo(removed_path)

        flash(
            "Event updated successfully.",
            "success",
        )

        return redirect(
            url_for(
                "admin.events"
            )
        )

    except Exception as exc:

        db.session.rollback()

        for uploaded_path in uploaded_paths:

            delete_photo(uploaded_path)

        flash(
            f"Event update failed: {exc}",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_event",
                id=event.id,
            )
        )


# ============================================================
# TOGGLE EVENT PUBLISH STATUS
# ============================================================

@admin_bp.route(
    "/events/<int:id>/toggle"
)
@admin_required
def toggle_event(id):

    event = (
        Event.query
        .get_or_404(id)
    )

    try:

        event.is_published = (
            not event.is_published
        )

        db.session.commit()

        if event.is_published:

            flash(
                "Event published successfully.",
                "success",
            )

        else:

            flash(
                "Event unpublished successfully.",
                "warning",
            )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Event status update failed: {exc}",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for(
            "admin.events"
        )
    )


# ============================================================
# DELETE EVENT
# ============================================================

@admin_bp.route(
    "/events/<int:id>/delete"
)
@admin_required
def delete_event(id):

    event = (
        Event.query
        .get_or_404(id)
    )

    event_image_paths = [
        event.image,
        *[
            gallery_image.image_path
            for gallery_image in event.gallery_images
        ],
    ]

    try:

        db.session.delete(
            event
        )

        db.session.commit()

        for image_path in event_image_paths:

            delete_photo(image_path)

        flash(
            "Event deleted successfully.",
            "success",
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Event deletion failed: {exc}",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for(
            "admin.events"
        )
    )


# ============================================================
# ADMIN PROFILE
# ============================================================

@admin_bp.route("/profile")
@admin_required
def profile():

    return render_template(

        "admin_profile.html",

        admin=_current_admin(),
    )


# ============================================================
# UPDATE ADMIN PROFILE
# ============================================================

@admin_bp.route(
    "/profile/update",
    methods=["POST"],
)
@admin_required
def update_profile():

    admin = (
        _current_admin()
    )

    if not admin:

        flash(
            "Administrator account not found.",
            "danger",
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )

    full_name = request.form.get(
        "full_name",
        "",
    ).strip()

    contact_email = (
        request.form.get(
            "contact_email",
            "",
        ).strip()
    )

    contact_phone = (
        request.form.get(
            "contact_phone",
            "",
        ).strip()
    )

    facebook_url = (
        request.form.get(
            "facebook_url",
            "",
        ).strip()
    )

    normalized_contact_email = (
        _normalize_identifier(
            contact_email
        )
        if contact_email
        else ""
    )

    if not full_name:

        flash(
            "Full name is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.profile"
            )
        )

    if contact_email:

        import re

        email_pattern = (
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        if not re.match(
            email_pattern,
            contact_email,
        ):

            flash(
                "Please enter a valid email address.",
                "danger",
            )

            return redirect(
                url_for(
                    "admin.profile"
                )
            )

    try:

        admin.full_name = (
            full_name
        )

        admin.contact_email = (
            normalized_contact_email
            or None
        )

        admin.contact_phone = (
            contact_phone
            or None
        )

        admin.facebook_url = (
            facebook_url
            or None
        )

        session["admin_name"] = (
            full_name
        )

        db.session.commit()

        flash(
            "Administrator contact information updated successfully.",
            "success",
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Profile update failed: {exc}",
            "danger",
        )

    return redirect(
        url_for(
            "admin.profile"
        )
    )


# ============================================================
# FLEXIBLE ADMINISTRATOR MANAGEMENT
# ============================================================


# ============================================================
# MANAGE ADMINISTRATORS
# ============================================================

@admin_bp.route(
    "/administrators"
)
@admin_required
def administrators():

    current_admin = (
        _current_admin()
    )

    current_administrator = (
        Admin.query
        .filter_by(
            is_current=True
        )
        .order_by(
            Admin.id.desc()
        )
        .first()
    )

    all_administrators = (
        Admin.query
        .order_by(
            Admin.is_current.desc(),
            Admin.term_year.desc(),
            Admin.created_at.desc(),
        )
        .all()
    )

    previous_administrators = [
        administrator
        for administrator
        in all_administrators
        if not administrator.is_current
    ]

    return render_template(

        "admin/admin_list.html",

        admin=current_admin,

        current_administrator=(
            current_administrator
        ),

        administrators=(
            all_administrators
        ),

        previous_administrators=(
            previous_administrators
        ),
    )


# ============================================================
# CREATE NEW ADMINISTRATOR
# ============================================================

@admin_bp.route(
    "/administrators/add",
    methods=["GET", "POST"],
)
@admin_required
def create_administrator():

    current_admin = (
        _current_admin()
    )

    if request.method == "GET":

        return render_template(

            "admin/create_admin.html",

            admin=current_admin,

            suggested_year=(
                date.today().year
            ),
        )

    # ========================================================
    # FORM DATA
    # ========================================================

    full_name = request.form.get(
        "full_name",
        "",
    ).strip()

    username = request.form.get(
        "username",
        "",
    ).strip()

    email = request.form.get(
        "email",
        "",
    ).strip()

    password = request.form.get(
        "password",
        "",
    )

    confirm_password = (
        request.form.get(
            "confirm_password",
            "",
        )
    )

    term_year = (
        _parse_term_year(
            request.form.get(
                "term_year"
            )
        )
        or date.today().year
    )

    contact_email = (
        request.form.get(
            "contact_email",
            "",
        ).strip()
    )

    contact_phone = (
        request.form.get(
            "contact_phone",
            "",
        ).strip()
    )

    facebook_url = (
        request.form.get(
            "facebook_url",
            "",
        ).strip()
    )

    normalized_username = (
        _normalize_identifier(
            username
        )
    )

    normalized_email = (
        _normalize_identifier(
            email
        )
    )

    normalized_contact_email = (
        _normalize_identifier(
            contact_email
        )
        if contact_email
        else ""
    )

    # ========================================================
    # REQUIRED VALIDATION
    # ========================================================

    if not full_name:

        flash(
            "Administrator full name is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    if not username:

        flash(
            "Administrator username is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    if not email:

        flash(
            "Administrator email is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    if len(password) < 6:

        flash(
            "Password must contain at least 6 characters.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    if password != confirm_password:

        flash(
            "Password and confirmation password do not match.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    # ========================================================
    # EMAIL VALIDATION
    # ========================================================

    import re

    email_pattern = (
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    if not re.match(
        email_pattern,
        email,
    ):

        flash(
            "Please enter a valid account email address.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    if (
        contact_email
        and not re.match(
            email_pattern,
            contact_email,
        )
    ):

        flash(
            "Please enter a valid contact email address.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    # ========================================================
    # DUPLICATE USERNAME
    # ========================================================

    existing_username = (
        Admin.query
        .filter(
            func.lower(
                Admin.username
            )
            ==
            normalized_username
        )
        .first()
    )

    if existing_username:

        flash(
            "This administrator username is already in use.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    # ========================================================
    # DUPLICATE EMAIL
    # ========================================================

    existing_email = (
        Admin.query
        .filter(
            func.lower(
                Admin.email
            )
            ==
            normalized_email
        )
        .first()
    )

    if existing_email:

        flash(
            "This administrator email is already in use.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )

    # ========================================================
    # CREATE ADMINISTRATOR
    # ========================================================

    try:

        new_admin = Admin(

            full_name=full_name,

            username=normalized_username,

            email=normalized_email,

            password=(
                generate_password_hash(
                    password
                )
            ),

            contact_email=(
                normalized_contact_email
                or None
            ),

            contact_phone=(
                contact_phone
                or None
            ),

            facebook_url=(
                facebook_url
                or None
            ),

            role="Admin",

            is_active=False,

            is_current=False,
        )

        new_admin.set_yearly_term(
            term_year
        )

        db.session.add(
            new_admin
        )

        db.session.commit()

        flash(
            (
                f"{full_name} was added successfully. "
                f"Reference term: {term_year}. "
                "The account is stored in administrator history "
                "and will remain inactive until you make it current."
            ),
            "success",
        )

        return redirect(
            url_for(
                "admin.administrators"
            )
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Administrator creation failed: {exc}",
            "danger",
        )

        return redirect(
            url_for(
                "admin.create_administrator"
            )
        )


# ============================================================
# EDIT ADMINISTRATOR
# ============================================================

@admin_bp.route(
    "/administrators/<int:id>/edit",
    methods=["GET", "POST"],
)
@admin_required
def edit_administrator(id):

    administrator = (
        Admin.query
        .get_or_404(id)
    )

    current_admin = (
        _current_admin()
    )

    if request.method == "GET":

        return render_template(

            "admin/edit_admin.html",

            administrator=(
                administrator
            ),

            admin=current_admin,
        )

    full_name = request.form.get(
        "full_name",
        "",
    ).strip()

    username = request.form.get(
        "username",
        "",
    ).strip()

    email = request.form.get(
        "email",
        "",
    ).strip()

    term_year = (
        _parse_term_year(
            request.form.get(
                "term_year"
            )
        )
        or date.today().year
    )

    contact_email = (
        request.form.get(
            "contact_email",
            "",
        ).strip()
    )

    contact_phone = (
        request.form.get(
            "contact_phone",
            "",
        ).strip()
    )

    facebook_url = (
        request.form.get(
            "facebook_url",
            "",
        ).strip()
    )

    normalized_username = (
        _normalize_identifier(
            username
        )
    )

    normalized_email = (
        _normalize_identifier(
            email
        )
    )

    normalized_contact_email = (
        _normalize_identifier(
            contact_email
        )
        if contact_email
        else ""
    )

    if not full_name:

        flash(
            "Administrator full name is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_administrator",
                id=administrator.id,
            )
        )

    if not username:

        flash(
            "Administrator username is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_administrator",
                id=administrator.id,
            )
        )

    if not email:

        flash(
            "Administrator email is required.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_administrator",
                id=administrator.id,
            )
        )

    import re

    email_pattern = (
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    if not re.match(
        email_pattern,
        email,
    ):

        flash(
            "Please enter a valid administrator email address.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_administrator",
                id=administrator.id,
            )
        )

    if (
        contact_email
        and not re.match(
            email_pattern,
            contact_email,
        )
    ):

        flash(
            "Please enter a valid contact email address.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_administrator",
                id=administrator.id,
            )
        )

    existing_username = (
        Admin.query
        .filter(
            func.lower(
                Admin.username
            )
            ==
            normalized_username,
            Admin.id
            != administrator.id,
        )
        .first()
    )

    if existing_username:

        flash(
            "This username belongs to another administrator.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_administrator",
                id=administrator.id,
            )
        )

    existing_email = (
        Admin.query
        .filter(
            func.lower(
                Admin.email
            )
            ==
            normalized_email,
            Admin.id
            != administrator.id,
        )
        .first()
    )

    if existing_email:

        flash(
            "This email belongs to another administrator.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_administrator",
                id=administrator.id,
            )
        )

    try:

        administrator.full_name = (
            full_name
        )

        administrator.username = (
            normalized_username
        )

        administrator.email = (
            normalized_email
        )

        administrator.contact_email = (
            normalized_contact_email
            or None
        )

        administrator.contact_phone = (
            contact_phone
            or None
        )

        administrator.facebook_url = (
            facebook_url
            or None
        )

        administrator.set_yearly_term(
            term_year
        )

        db.session.commit()

        if (
            current_admin
            and current_admin.id
            == administrator.id
        ):

            session["admin_name"] = (
                administrator.full_name
            )

            session["admin_role"] = (
                administrator.role
            )

        flash(
            "Administrator information updated successfully.",
            "success",
        )

        return redirect(
            url_for(
                "admin.administrators"
            )
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Administrator update failed: {exc}",
            "danger",
        )

        return redirect(
            url_for(
                "admin.edit_administrator",
                id=administrator.id,
            )
        )


# ============================================================
# MAKE CURRENT ADMINISTRATOR
# ============================================================

@admin_bp.route(
    "/administrators/<int:id>/make-current",
    methods=["POST"],
)
@admin_required
def make_current_administrator(id):

    new_admin = (
        Admin.query
        .get_or_404(id)
    )

    logged_in_admin = (
        _current_admin()
    )

    if (
        new_admin.is_current
        and new_admin.is_active
    ):

        flash(
            "This administrator is already the current administrator.",
            "warning",
        )

        return redirect(
            url_for(
                "admin.administrators"
            )
        )

    try:

        # ====================================================
        # ARCHIVE ALL CURRENT ADMINISTRATORS
        # ====================================================

        other_administrators = (
            Admin.query
            .filter(
                Admin.id
                != new_admin.id
            )
            .all()
        )

        for old_admin in other_administrators:

            if (
                old_admin.is_current
                or old_admin.is_active
            ):

                old_admin.make_previous()

        # ====================================================
        # ACTIVATE SELECTED ADMINISTRATOR
        # ====================================================
        #
        # Handover is manual and can happen at any time.
        # term_year is only a historical/reference value.
        # ====================================================

        if not new_admin.term_year:

            new_admin.set_yearly_term(
                date.today().year
            )

        new_admin.make_current()

        db.session.commit()

        # ====================================================
        # HANDOVER TO ANOTHER ADMIN
        # ====================================================
        #
        # If the logged-in administrator transferred
        # authority to another administrator, their current
        # session must end immediately because their account
        # has become a previous/inactive administrator.
        # ====================================================

        if (
            logged_in_admin
            and logged_in_admin.id
            != new_admin.id
        ):

            new_admin_name = (
                new_admin.full_name
            )

            new_admin_year = (
                new_admin.term_year
            )

            session.clear()

            flash(
                (
                    f"Administrator handover completed successfully. "
                    f"{new_admin_name} is now the current administrator. "
                    f"Reference term: {new_admin_year}. "
                    "The previous administrator record remains stored "
                    "in administrator history. Please log in using the "
                    "new current administrator account."
                ),
                "success",
            )

            return redirect(
                url_for(
                    "auth.login"
                )
            )

        flash(
            "Current administrator updated successfully.",
            "success",
        )

        return redirect(
            url_for(
                "admin.administrators"
            )
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            f"Administrator handover failed: {exc}",
            "danger",
        )

        return redirect(
            url_for(
                "admin.administrators"
            )
        )


# ============================================================
# LOGOUT
# ============================================================

@admin_bp.route("/logout")
@admin_required
def logout():

    session.clear()

    flash(
        "Logged out successfully.",
        "success",
    )

    return redirect(
        url_for(
            "auth.login"
        )
    )