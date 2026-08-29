"""
JUians of Gaibandha
User Account Models

This module keeps user accounts and profile edit requests
separate from the existing member and administrator models.
"""

import json
from datetime import datetime

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from extensions import db


# ============================================================
# USER ACCOUNT MODEL
# ============================================================

class UserAccount(db.Model):
    """Login account owned by a directory member."""

    __tablename__ = "user_accounts"

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # --------------------------------------------------------
    # LINKED DIRECTORY MEMBER
    # --------------------------------------------------------
    #
    # A user account may exist before a directory profile
    # is submitted or claimed. Therefore member_id is nullable.
    # --------------------------------------------------------

    member_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "information.id",
            ondelete="SET NULL",
        ),
        unique=True,
        nullable=True,
        index=True,
    )

    # --------------------------------------------------------
    # ACCOUNT INFORMATION
    # --------------------------------------------------------

    full_name = db.Column(
        db.String(100),
        nullable=False,
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True,
        index=True,
    )

    phone = db.Column(
        db.String(20),
        unique=True,
        nullable=True,
        index=True,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    # --------------------------------------------------------
    # ACCOUNT STATUS
    # --------------------------------------------------------

    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # LOGIN AND DATE INFORMATION
    # --------------------------------------------------------

    last_login = db.Column(
        db.DateTime,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # --------------------------------------------------------
    # MEMBER RELATIONSHIP
    # --------------------------------------------------------

    member = db.relationship(
        "Information",
        foreign_keys=[member_id],
        backref=db.backref(
            "user_account",
            uselist=False,
        ),
    )

    # --------------------------------------------------------
    # PASSWORD HELPERS
    # --------------------------------------------------------

    def set_password(self, password):
        """Create a secure one-way password hash."""

        self.password_hash = (
            generate_password_hash(
                str(password)
            )
        )

    def check_password(self, password):
        """Safely verify a submitted password."""

        if (
            not self.password_hash
            or password is None
        ):
            return False

        return check_password_hash(
            self.password_hash,
            str(password),
        )

    # --------------------------------------------------------
    # LOGIN IDENTIFIER
    # --------------------------------------------------------

    @property
    def login_identifier(self):
        """Return the preferred login identifier."""

        return (
            self.email
            or self.phone
            or ""
        )

    # --------------------------------------------------------
    # REPRESENTATION
    # --------------------------------------------------------

    def __repr__(self):

        return (
            f"<UserAccount "
            f"{self.id}: "
            f"{self.login_identifier}>"
        )


# ============================================================
# MEMBER EDIT REQUEST MODEL
# ============================================================

class MemberEditRequest(db.Model):
    """
    A user-submitted profile update waiting for Admin review.

    The approved member record is not modified immediately.
    Proposed changes remain here until an Administrator
    approves or rejects the request.
    """

    __tablename__ = "member_edit_requests"

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # --------------------------------------------------------
    # USER ACCOUNT
    # --------------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "user_accounts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # DIRECTORY MEMBER
    # --------------------------------------------------------

    member_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "information.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # PROPOSED INFORMATION
    # --------------------------------------------------------
    #
    # The proposed values are stored as JSON text.
    # This keeps the existing approved public member
    # information unchanged until Admin approval.
    # --------------------------------------------------------

    proposed_data = db.Column(
        db.Text,
        nullable=False,
        default="{}",
    )

    proposed_photo = db.Column(
        db.String(500),
        nullable=True,
    )

    # --------------------------------------------------------
    # REVIEW STATUS
    # --------------------------------------------------------

    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False,
        index=True,
    )

    admin_note = db.Column(
        db.Text,
        nullable=True,
    )

    # --------------------------------------------------------
    # REVIEWED BY ADMIN
    # --------------------------------------------------------

    reviewed_by_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "admin.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    # --------------------------------------------------------
    # DATE INFORMATION
    # --------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    user = db.relationship(
        "UserAccount",
        foreign_keys=[user_id],
        backref=db.backref(
            "edit_requests",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    member = db.relationship(
        "Information",
        foreign_keys=[member_id],
        backref=db.backref(
            "edit_requests",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    reviewer = db.relationship(
        "Admin",
        foreign_keys=[reviewed_by_id],
    )

    # --------------------------------------------------------
    # PROPOSED DATA HELPERS
    # --------------------------------------------------------

    def set_proposed_data(self, values):
        """Serialize proposed member values as JSON text."""

        self.proposed_data = json.dumps(
            values or {},
            ensure_ascii=False,
        )

    def get_proposed_data(self):
        """Return proposed values as a Python dictionary."""

        try:

            value = json.loads(
                self.proposed_data
                or "{}"
            )

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):

            return {}

        if isinstance(
            value,
            dict,
        ):

            return value

        return {}

    # --------------------------------------------------------
    # REPRESENTATION
    # --------------------------------------------------------

    def __repr__(self):

        return (
            f"<MemberEditRequest "
            f"{self.id}: "
            f"member={self.member_id}, "
            f"status={self.status}>"
        )