from datetime import datetime, date

from extensions import db


# =====================================================
# MEMBER INFORMATION MODEL
# =====================================================

class Information(db.Model):

    __tablename__ = "information"

    # =================================================
    # PRIMARY KEY
    # =================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =================================================
    # ACADEMIC INFORMATION
    # =================================================

    category = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    full_name = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    department = db.Column(
        db.String(150),
        nullable=False
    )

    batch = db.Column(
        db.String(50),
        index=True
    )

    session = db.Column(
        db.String(50),
        index=True
    )

    student_id = db.Column(
        db.String(50)
    )

    registration_no = db.Column(
        db.String(50)
    )

    # =================================================
    # CONTACT INFORMATION
    # =================================================

    phone = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        index=True
    )

    # =================================================
    # PERSONAL INFORMATION
    # =================================================

    gender = db.Column(
        db.String(20)
    )

    date_of_birth = db.Column(
        db.String(20)
    )

    blood_group = db.Column(
        db.String(10)
    )

    # =================================================
    # ADDRESS INFORMATION
    # =================================================

    present_address = db.Column(
        db.Text
    )

    permanent_address = db.Column(
        db.Text
    )

    district = db.Column(
        db.String(100),
        default="Gaibandha"
    )

    upazila = db.Column(
        db.String(100)
    )

    # =================================================
    # PROFESSIONAL INFORMATION
    # =================================================

    occupation = db.Column(
        db.String(100)
    )

    company = db.Column(
        db.String(150)
    )

    designation = db.Column(
        db.String(100)
    )

    # =================================================
    # SOCIAL MEDIA
    # =================================================

    facebook = db.Column(
        db.String(255)
    )

    linkedin = db.Column(
        db.String(255)
    )

    github = db.Column(
        db.String(255)
    )

    website = db.Column(
        db.String(255)
    )

    # =================================================
    # PROFILE PHOTO
    # =================================================

    photo = db.Column(
        db.String(255),
        default="default.png"
    )

    # =================================================
    # EXTRA INFORMATION
    # =================================================

    remarks = db.Column(
        db.Text
    )

    # =================================================
    # APPROVAL SYSTEM
    # =================================================

    status = db.Column(
        db.String(20),
        default="Pending",
        index=True
    )

    approved_by = db.Column(
        db.String(100)
    )

    approved_at = db.Column(
        db.DateTime
    )

    # =================================================
    # DATE INFORMATION
    # =================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # =================================================
    # REPRESENTATION
    # =================================================

    def __repr__(self):

        return f"<Member {self.full_name}>"


# =====================================================
# ADMIN MODEL
# =====================================================

class Admin(db.Model):

    __tablename__ = "admin"

    # =================================================
    # PRIMARY KEY
    # =================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =================================================
    # ADMIN INFORMATION
    # =================================================

    full_name = db.Column(
        db.String(100),
        nullable=False,
        default="Administrator"
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        index=True
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    # =================================================
    # ADMIN CONTACT INFORMATION
    # =================================================
    #
    # Public contact information displayed on the
    # JUians of Gaibandha website.
    #
    # These values can be updated whenever the
    # responsible administrator changes.
    # =================================================

    contact_email = db.Column(
        db.String(120)
    )

    contact_phone = db.Column(
        db.String(30)
    )

    facebook_url = db.Column(
        db.String(255)
    )

    # =================================================
    # YEARLY ADMINISTRATOR TERM
    # =================================================
    #
    # This section allows JUians of Gaibandha to keep
    # separate administrator records for each year.
    #
    # Example:
    #
    # 2026 Administrator
    # term_year    = 2026
    # term_start   = 2026-01-01
    # term_end     = 2026-12-31
    # is_current   = True
    #
    # When a new administrator takes responsibility,
    # the previous administrator will remain stored
    # as history instead of being deleted.
    # =================================================

    term_year = db.Column(
        db.Integer,
        index=True
    )

    term_start = db.Column(
        db.Date
    )

    term_end = db.Column(
        db.Date
    )

    is_current = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # =================================================
    # ROLE MANAGEMENT
    # =================================================

    role = db.Column(
        db.String(30),
        default="Admin"
    )

    # =================================================
    # ACTIVE STATUS
    # =================================================
    #
    # True:
    # Administrator is allowed to log in.
    #
    # False:
    # Administrator account is disabled.
    #
    # Normally only the current administrator should
    # remain active.
    # =================================================

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # =================================================
    # LOGIN INFORMATION
    # =================================================

    last_login = db.Column(
        db.DateTime
    )

    # =================================================
    # DATE INFORMATION
    # =================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # =================================================
    # ADMIN TERM HELPERS
    # =================================================

    @property
    def term_status(self):

        """
        Returns a readable administrator term status.
        """

        if self.is_current and self.is_active:
            return "Current"

        if self.is_current and not self.is_active:
            return "Current - Disabled"

        return "Previous"


    @property
    def term_label(self):

        """
        Returns a readable term label.

        Examples:
        2026
        01 Jan 2026 - 31 Dec 2026
        """

        if self.term_start and self.term_end:

            return (
                f"{self.term_start.strftime('%d %b %Y')} "
                f"- "
                f"{self.term_end.strftime('%d %b %Y')}"
            )

        if self.term_year:
            return str(self.term_year)

        return "Not Assigned"


    def set_yearly_term(self, year):

        """
        Assign a standard January to December
        yearly administrator term.
        """

        year = int(year)

        self.term_year = year

        self.term_start = date(
            year,
            1,
            1
        )

        self.term_end = date(
            year,
            12,
            31
        )


    def make_current(self):

        """
        Mark this administrator as the
        current active administrator.

        Deactivating the previous administrator
        should be handled inside the route using
        a database transaction.
        """

        self.is_current = True
        self.is_active = True


    def make_previous(self):

        """
        Mark this administrator as a
        previous administrator.
        """

        self.is_current = False
        self.is_active = False

    # =================================================
    # REPRESENTATION
    # =================================================

    def __repr__(self):

        return (
            f"<Admin "
            f"{self.username} "
            f"Year={self.term_year} "
            f"Current={self.is_current}>"
        )


# =====================================================
# RECENT EVENTS MODEL
# =====================================================
#
# This model manages the Recent Events section
# displayed on the homepage.
#
# Administrator will be able to:
#
# - Create event
# - Edit event
# - Delete event
# - Publish event
# - Unpublish event
# - Upload event image
#
# The homepage will display only published events.
# =====================================================

class Event(db.Model):

    __tablename__ = "events"

    # =================================================
    # PRIMARY KEY
    # =================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # =================================================
    # EVENT INFORMATION
    # =================================================

    title = db.Column(
        db.String(200),
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    # =================================================
    # EVENT DATE
    # =================================================
    #
    # Stored as a string so the admin can use flexible
    # display formats such as:
    #
    # 04 September 2026
    # Coming Soon
    # 15 October 2026
    #
    # This keeps compatibility with the existing
    # Recent Events design.
    # =================================================

    event_date = db.Column(
        db.String(100),
        nullable=False
    )

    # =================================================
    # EVENT LOCATION
    # =================================================

    location = db.Column(
        db.String(200)
    )

    # =================================================
    # EVENT IMAGE
    # =================================================
    #
    # Database stores only the uploaded filename.
    #
    # Example:
    #
    # abc123.jpg
    #
    # Actual file:
    #
    # static/uploads/abc123.jpg
    #
    # Default image is stored with its complete
    # static-relative path because it is already inside
    # the images directory.
    # =================================================

    image = db.Column(
        db.String(255),
        default="images/ju_campus.jpeg"
    )

    # =================================================
    # EVENT LINK
    # =================================================
    #
    # Optional external or internal URL.
    #
    # If empty, the homepage can simply show the
    # event without a Read More destination.
    # =================================================

    event_link = db.Column(
        db.String(500)
    )

    # =================================================
    # PUBLISH STATUS
    # =================================================
    #
    # True  = visible on homepage
    # False = hidden from homepage
    # =================================================

    is_published = db.Column(
        db.Boolean,
        default=True,
        index=True
    )

    # =================================================
    # DATE INFORMATION
    # =================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # =================================================
    # REPRESENTATION
    # =================================================

    def __repr__(self):

        return f"<Event {self.title}>"