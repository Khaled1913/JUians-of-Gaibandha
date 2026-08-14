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
    app.config.from_object(Config)

    # -------------------------------------------------
    # Initialize Extensions
    # -------------------------------------------------
    db.init_app(app)

    # -------------------------------------------------
    # Create Upload Folder
    # -------------------------------------------------
    upload_folder = app.config.get("UPLOAD_FOLDER", "static/uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # -------------------------------------------------
    # Import Models
    # -------------------------------------------------
    from models import Admin, Information

    # -------------------------------------------------
    # Register Blueprints
    # -------------------------------------------------
    from routes.home import home_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.member import member_bp
    from routes.search import search_bp
    from routes.api import api_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(api_bp)

    # -------------------------------------------------
    # Create Database Tables
    # -------------------------------------------------
    with app.app_context():
        db.create_all()

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
        return "404 - Page Not Found", 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "500 - Internal Server Error", 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )