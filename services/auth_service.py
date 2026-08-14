"""
=====================================================
JUians of Gaibandha Portal
Authentication Service
Version 1.0
Developer : Khaled Mahmud Jon
=====================================================
"""

from flask import session
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from extensions import db
from models import Admin


# =====================================================
# HASH PASSWORD
# =====================================================

def hash_password(password):
    """
    Generate secure password hash.
    """

    return generate_password_hash(password)


# =====================================================
# VERIFY PASSWORD
# =====================================================

def verify_password(password_hash, password):
    """
    Verify password.
    """

    return check_password_hash(
        password_hash,
        password
    )


# =====================================================
# GET ADMIN BY USERNAME
# =====================================================

def get_admin(username):

    return Admin.query.filter_by(
        username=username
    ).first()


# =====================================================
# LOGIN ADMIN
# =====================================================

def login_admin(username, password):

    admin = get_admin(username)

    if admin is None:
        return None

    if not admin.is_active:
        return None

    if not verify_password(
        admin.password,
        password
    ):
        return None

    session["admin_id"] = admin.id
    session["admin_name"] = admin.full_name
    session["admin_role"] = admin.role

    return admin


# =====================================================
# LOGOUT ADMIN
# =====================================================

def logout_admin():

    session.clear()


# =====================================================
# CHECK LOGIN
# =====================================================

def is_logged_in():

    return "admin_id" in session


# =====================================================
# CURRENT ADMIN
# =====================================================

def current_admin():

    admin_id = session.get(
        "admin_id"
    )

    if not admin_id:
        return None

    return Admin.query.get(
        admin_id
    )


# =====================================================
# CREATE ADMIN
# =====================================================

def create_admin(
    full_name,
    username,
    email,
    password,
    role="Administrator"
):

    existing = Admin.query.filter_by(
        username=username
    ).first()

    if existing:
        return None

    admin = Admin(

        full_name=full_name,

        username=username,

        email=email,

        password=hash_password(
            password
        ),

        role=role

    )

    db.session.add(admin)

    db.session.commit()

    return admin


# =====================================================
# CHANGE PASSWORD
# =====================================================

def change_password(
    admin,
    new_password
):

    admin.password = hash_password(
        new_password
    )

    db.session.commit()


# =====================================================
# UPDATE PROFILE
# =====================================================

def update_profile(
    admin,
    full_name,
    email
):

    admin.full_name = full_name

    admin.email = email

    db.session.commit()


# =====================================================
# REMEMBER ME
# =====================================================

def remember_login(remember):

    session.permanent = remember


# =====================================================
# REMOVE SESSION
# =====================================================

def destroy_session():

    session.clear()