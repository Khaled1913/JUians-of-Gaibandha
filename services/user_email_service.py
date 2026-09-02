"""Secure transactional email helpers for JUians user accounts."""

import os
import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


VERIFY_EMAIL_SALT = "juians-user-email-verification-v1"
RESET_PASSWORD_SALT = "juians-user-password-reset-v1"


def _env_flag(name, default=False):
    """Read a boolean environment variable."""

    value = os.environ.get(name)

    if value is None:
        return default

    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def email_is_configured():
    """Return whether the minimum SMTP settings are available."""

    return all(
        os.environ.get(name)
        for name in (
            "SMTP_HOST",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "SMTP_FROM_EMAIL",
        )
    )


def _serializer():
    """Create a signer using the Flask application's secret key."""

    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )


def generate_user_token(user, purpose):
    """Generate a signed token bound to a user and purpose."""

    if purpose == "verify-email":
        salt = VERIFY_EMAIL_SALT
    elif purpose == "reset-password":
        salt = RESET_PASSWORD_SALT
    else:
        raise ValueError("Unsupported user-token purpose.")

    return _serializer().dumps(
        {
            "user_id": user.id,
            "email": str(user.email or "").lower(),
            "purpose": purpose,
            # Changing the password invalidates older reset links.
            "password_marker": str(user.password_hash or "")[-20:],
        },
        salt=salt,
    )


def read_user_token(token, purpose, max_age):
    """Validate and decode a signed expiring user token."""

    if purpose == "verify-email":
        salt = VERIFY_EMAIL_SALT
    elif purpose == "reset-password":
        salt = RESET_PASSWORD_SALT
    else:
        return None, "invalid"

    try:
        data = _serializer().loads(
            str(token or ""),
            salt=salt,
            max_age=max_age,
        )

    except SignatureExpired:
        return None, "expired"

    except (BadSignature, TypeError, ValueError):
        return None, "invalid"

    if not isinstance(data, dict) or data.get("purpose") != purpose:
        return None, "invalid"

    return data, None


def send_email(to_email, subject, text_body, html_body=None):
    """Send one email through environment-configured SMTP."""

    if not email_is_configured():
        raise RuntimeError(
            "SMTP is not configured. Add the required Render environment variables."
        )

    host = os.environ["SMTP_HOST"].strip()
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ["SMTP_USERNAME"].strip()
    password = os.environ["SMTP_PASSWORD"]
    from_email = os.environ["SMTP_FROM_EMAIL"].strip()
    from_name = os.environ.get(
        "SMTP_FROM_NAME",
        "JUians of Gaibandha",
    ).strip()

    use_ssl = _env_flag("SMTP_USE_SSL", default=(port == 465))
    use_tls = _env_flag("SMTP_USE_TLS", default=not use_ssl)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = str(to_email).strip()
    message.set_content(text_body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()

    if use_ssl:
        with smtplib.SMTP_SSL(
            host,
            port,
            timeout=20,
            context=context,
        ) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)

        return

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()

        if use_tls:
            smtp.starttls(context=context)
            smtp.ehlo()

        smtp.login(username, password)
        smtp.send_message(message)


def send_verification_email(user, verification_url):
    """Send a user-account email verification message."""

    send_email(
        user.email,
        "Verify your JUians account email",
        (
            f"Hello {user.full_name},\n\n"
            "Verify your JUians of Gaibandha account by opening this link:\n"
            f"{verification_url}\n\n"
            "This link expires in 24 hours. If you did not create this "
            "account, you can ignore this email."
        ),
        f"""
        <div style="font-family:Arial,sans-serif;max-width:620px;margin:auto;color:#173f35">
            <h2 style="color:#00775e">Verify your JUians account</h2>
            <p>Hello {user.full_name},</p>
            <p>Confirm your email address to secure your member account.</p>
            <p style="margin:28px 0">
                <a href="{verification_url}" style="background:#008b6d;color:#fff;padding:13px 20px;border-radius:8px;text-decoration:none;font-weight:bold">Verify Email Address</a>
            </p>
            <p>This link expires in 24 hours.</p>
            <p style="color:#6b7f78">If you did not create this account, ignore this email.</p>
        </div>
        """,
    )


def send_password_reset_email(user, reset_url):
    """Send a password-reset message without exposing account existence."""

    send_email(
        user.email,
        "Reset your JUians account password",
        (
            f"Hello {user.full_name},\n\n"
            "Reset your JUians of Gaibandha account password using this link:\n"
            f"{reset_url}\n\n"
            "This link expires in 30 minutes. If you did not request a "
            "password reset, ignore this email."
        ),
        f"""
        <div style="font-family:Arial,sans-serif;max-width:620px;margin:auto;color:#173f35">
            <h2 style="color:#00775e">Reset your password</h2>
            <p>Hello {user.full_name},</p>
            <p>Use the secure button below to choose a new password.</p>
            <p style="margin:28px 0">
                <a href="{reset_url}" style="background:#008b6d;color:#fff;padding:13px 20px;border-radius:8px;text-decoration:none;font-weight:bold">Reset Password</a>
            </p>
            <p>This link expires in 30 minutes and becomes invalid after your password changes.</p>
            <p style="color:#6b7f78">If you did not request this, ignore this email.</p>
        </div>
        """,
    )
