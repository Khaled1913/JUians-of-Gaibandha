"""
JUians of Gaibandha
User Account Model

This model is intentionally kept separate from the existing
member and administrator models so the current system remains
backward-compatible while user login is introduced in stages.
"""

import json
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class UserAccount(db.Model):
    """Login account owned by a directory member."""

    __tablename__ = "user_accounts"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # A new account may exist before a member profile is submitted
    # or claimed, therefore member_id is nullable.
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

    member = db.relationship(
        "Information",
        foreign_keys=[member_id],
        backref=db.backref(
            "user_account",
            uselist=False,
        ),
    )

    def set_password(self, password):
        """Create a secure one-way password hash."""

        self.password_hash = generate_password_hash(
            str(password)
        )

    def check_password(self, password):
        """Safely verify a submitted password."""

        if not self.password_hash or password is None:
            return False

        return check_password_hash(
            self.password_hash,
            str(password),
        )

    @property
    def login_identifier(self):
        """Return the account's preferred login identifier."""

        return self.email or self.phone or ""

    def __repr__(self):
        return f"<UserAccount {self.id}: {self.login_identifier}>"


class MemberEditRequest(db.Model):
    """A user-submitted profile update waiting for admin review."""

    __tablename__ = "member_edit_requests"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "user_accounts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    member_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "information.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # JSON text preserves the proposed values without modifying the
    # approved public member record before administrator approval.
    proposed_data = db.Column(
        db.Text,
        nullable=False,
        default="{}",
    )

    proposed_photo = db.Column(
        db.String(500),
        nullable=True,
    )

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

    def set_proposed_data(self, values):
        """Serialize proposed member values as safe JSON text."""

        self.proposed_data = json.dumps(
            values or {},
            ensure_ascii=False,
        )

    def get_proposed_data(self):
        """Return proposed values as a dictionary."""

        try:
            value = json.loads(
                self.proposed_data or "{}"
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}

        return value if isinstance(value, dict) else {}

    def __repr__(self):
        return (
            f"<MemberEditRequest {self.id}: "
            f"member={self.member_id}, status={self.status}>"
        )


# ============================================================
# EXISTING PROFILE CLAIM REQUEST MODEL
# ============================================================

class ProfileClaimRequest(db.Model):
    """Request to connect an existing member profile to a user."""

    __tablename__ = "profile_claim_requests"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "user_accounts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    member_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "information.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False,
        index=True,
    )

    claimant_note = db.Column(
        db.Text,
        nullable=True,
    )

    admin_note = db.Column(
        db.Text,
        nullable=True,
    )

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

    user = db.relationship(
        "UserAccount",
        foreign_keys=[user_id],
        backref=db.backref(
            "claim_requests",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    member = db.relationship(
        "Information",
        foreign_keys=[member_id],
        backref=db.backref(
            "claim_requests",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    reviewer = db.relationship(
        "Admin",
        foreign_keys=[reviewed_by_id],
    )

    def __repr__(self):
        return (
            f"<ProfileClaimRequest {self.id}: "
            f"member={self.member_id}, status={self.status}>"
        )
