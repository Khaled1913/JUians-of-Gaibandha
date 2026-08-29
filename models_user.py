"""
JUians of Gaibandha
User Account Model

This model is intentionally kept separate from the existing
member and administrator models so the current system remains
backward-compatible while user login is introduced in stages.
"""

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

