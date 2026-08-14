from datetime import date

from app import app
from extensions import db

from sqlalchemy import inspect


# =====================================================
# ADMIN DATABASE COLUMN MIGRATION
# =====================================================
#
# This script safely updates the existing admin table.
#
# It adds:
#
# Contact Information
# - contact_email
# - contact_phone
# - facebook_url
#
# Yearly Administrator Management
# - term_year
# - term_start
# - term_end
# - is_current
#
# Existing administrator data will NOT be deleted.
#
# Existing active administrator will be assigned as
# the current administrator for 2026 if no current
# administrator has been configured yet.
# =====================================================


with app.app_context():

    print("")
    print("==============================================")
    print("JUians of Gaibandha")
    print("Admin Database Migration")
    print("==============================================")
    print("")


    # =================================================
    # GET EXISTING ADMIN TABLE COLUMNS
    # =================================================

    inspector = inspect(db.engine)

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("admin")
    }


    # =================================================
    # HELPER FUNCTION
    # =================================================

    def add_column_if_missing(
        column_name,
        column_definition
    ):

        if column_name in existing_columns:

            print(
                f"[SKIPPED] {column_name} already exists."
            )

            return


        db.session.execute(
            db.text(
                f"""
                ALTER TABLE admin
                ADD COLUMN {column_name}
                {column_definition}
                """
            )
        )


        existing_columns.add(
            column_name
        )


        print(
            f"[ADDED] {column_name}"
        )


    # =================================================
    # CONTACT INFORMATION COLUMNS
    # =================================================

    print("Checking contact information columns...")
    print("")


    add_column_if_missing(
        "contact_email",
        "VARCHAR(120)"
    )


    add_column_if_missing(
        "contact_phone",
        "VARCHAR(30)"
    )


    add_column_if_missing(
        "facebook_url",
        "VARCHAR(255)"
    )


    # =================================================
    # YEARLY ADMINISTRATOR COLUMNS
    # =================================================

    print("")
    print("Checking yearly administrator columns...")
    print("")


    add_column_if_missing(
        "term_year",
        "INTEGER"
    )


    add_column_if_missing(
        "term_start",
        "DATE"
    )


    add_column_if_missing(
        "term_end",
        "DATE"
    )


    add_column_if_missing(
        "is_current",
        "BOOLEAN DEFAULT 0"
    )


    # =================================================
    # COMMIT STRUCTURE CHANGES
    # =================================================

    db.session.commit()


    print("")
    print(
        "Admin table structure updated successfully."
    )


    # =================================================
    # INITIALIZE EXISTING ADMINISTRATOR
    # =================================================
    #
    # If the project already contains an active admin
    # but no administrator has been marked as current,
    # the existing active admin will become the current
    # administrator for 2026.
    #
    # This prevents the current login from breaking.
    # =================================================

    print("")
    print("Checking current administrator...")
    print("")


    current_admin = db.session.execute(
        db.text(
            """
            SELECT id
            FROM admin
            WHERE is_current = 1
            LIMIT 1
            """
        )
    ).fetchone()


    if current_admin:

        print(
            "[SKIPPED] A current administrator "
            "is already configured."
        )


    else:

        existing_admin = db.session.execute(
            db.text(
                """
                SELECT id, full_name, username
                FROM admin
                WHERE is_active = 1
                ORDER BY id ASC
                LIMIT 1
                """
            )
        ).fetchone()


        if existing_admin:

            admin_id = existing_admin.id


            term_year = 2026

            term_start = date(
                term_year,
                1,
                1
            )

            term_end = date(
                term_year,
                12,
                31
            )


            db.session.execute(
                db.text(
                    """
                    UPDATE admin

                    SET
                        term_year = :term_year,
                        term_start = :term_start,
                        term_end = :term_end,
                        is_current = 1,
                        is_active = 1

                    WHERE id = :admin_id
                    """
                ),
                {
                    "term_year": term_year,
                    "term_start": term_start,
                    "term_end": term_end,
                    "admin_id": admin_id
                }
            )


            db.session.commit()


            print(
                "[UPDATED] Existing administrator "
                "assigned as current administrator."
            )


            print(
                f"Admin ID   : {admin_id}"
            )


            print(
                f"Full Name  : {existing_admin.full_name}"
            )


            print(
                f"Username   : {existing_admin.username}"
            )


            print(
                f"Term Year  : {term_year}"
            )


            print(
                f"Term Start : {term_start}"
            )


            print(
                f"Term End   : {term_end}"
            )


            print(
                "Status      : Current / Active"
            )


        else:

            print(
                "[WARNING] No active administrator "
                "was found."
            )


            print(
                "Create an administrator before "
                "using the yearly admin system."
            )


    # =================================================
    # FINAL RESULT
    # =================================================

    print("")
    print("==============================================")
    print("Migration completed successfully!")
    print("==============================================")
    print("")

    print("Available Admin columns:")

    print("")

    print("- contact_email")
    print("- contact_phone")
    print("- facebook_url")
    print("- term_year")
    print("- term_start")
    print("- term_end")
    print("- is_current")

    print("")