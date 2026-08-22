"""
=====================================================
JUians of Gaibandha Portal
Professional Flask Application
Main Application File
Version 6.0
=====================================================
"""

import os

from flask import Flask

from config import Config
from extensions import db


def create_app():

    app = Flask(__name__)


    # -------------------------------------------------
    # Load Configuration
    # -------------------------------------------------

    app.config.from_object(
        Config
    )


    # -------------------------------------------------
    # Initialize Extensions
    # -------------------------------------------------

    db.init_app(
        app
    )


    # -------------------------------------------------
    # Create Upload Folder
    # -------------------------------------------------

    upload_folder = app.config.get(
        "UPLOAD_FOLDER",
        "static/uploads"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    # -------------------------------------------------
    # Import Models
    # -------------------------------------------------
    #
    # Import all database models before db.create_all()
    # so SQLAlchemy knows about every table.
    # -------------------------------------------------

    from models import (
        Admin,
        Information,
        Event,
        EventImage,
    )


    # -------------------------------------------------
    # Register Blueprints
    # -------------------------------------------------

    from routes.home import home_bp

    from routes.auth import auth_bp

    from routes.admin import admin_bp

    from routes.member import member_bp

    from routes.search import search_bp

    from routes.api import api_bp


    app.register_blueprint(
        home_bp
    )

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        admin_bp
    )

    app.register_blueprint(
        member_bp
    )

    app.register_blueprint(
        search_bp
    )

    app.register_blueprint(
        api_bp
    )


    # -------------------------------------------------
    # Create Database Tables
    # -------------------------------------------------
    #
    # Local:
    # Creates tables inside SQLite if missing.
    #
    # Render:
    # Creates tables inside PostgreSQL if DATABASE_URL
    # is configured.
    #
    # Existing tables/data are not deleted.
    # -------------------------------------------------

    with app.app_context():

        try:

            db.create_all()

            print(
                "Database tables initialized successfully."
            )

        except Exception as error:

            print(
                "Database initialization failed:"
            )

            print(
                error
            )

            raise


    # -------------------------------------------------
    # Context Processor
    # -------------------------------------------------

    @app.context_processor
    def inject_settings():

        return {

            "APP_NAME": app.config.get(
                "APP_NAME",
                "JUians of Gaibandha"
            ),

            "VERSION": app.config.get(
                "VERSION",
                "6.0"
            )

        }


    # -------------------------------------------------
    # Error Handlers
    # -------------------------------------------------

    @app.errorhandler(404)
    def page_not_found(error):

        return (
            "404 - Page Not Found",
            404
        )


    @app.errorhandler(500)
    def internal_error(error):

        db.session.rollback()

        return (
            "500 - Internal Server Error",
            500
        )


    # -------------------------------------------------
    # Return Flask Application
    # -------------------------------------------------

    return app


# =====================================================
# APPLICATION INSTANCE
# =====================================================
#
# Required by Gunicorn:
#
# gunicorn app:app
#
# =====================================================

app = create_app()



# =====================================================
# LOCAL DEVELOPMENT SERVER
# =====================================================

if __name__ == "__main__":

    # -------------------------------------------------
    # Render automatically provides PORT.
    #
    # Local development falls back to port 5000.
    # -------------------------------------------------

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    # -------------------------------------------------
    # Debug only for local development.
    #
    # Render sets RENDER=true automatically.
    # -------------------------------------------------

    is_render = (
        os.environ.get(
            "RENDER"
        )
        is not None
    )


    app.run(

        debug=not is_render,

        host="0.0.0.0",

        port=port

    )