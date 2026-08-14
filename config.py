"""
=====================================================
config.py
JUians of Gaibandha Portal
Application Configuration
Version 5.0
=====================================================
"""


import os



# =====================================================
# BASE DIRECTORY
# =====================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)





# =====================================================
# DATABASE CONFIGURATION
# =====================================================

DATABASE_FOLDER = os.path.join(
    BASE_DIR,
    "database"
)



if not os.path.exists(
    DATABASE_FOLDER
):

    os.makedirs(
        DATABASE_FOLDER
    )



DATABASE_NAME = "gaibandha.db"


DATABASE_PATH = os.path.join(
    DATABASE_FOLDER,
    DATABASE_NAME
)





# =====================================================
# UPLOAD CONFIGURATION
# =====================================================

UPLOAD_FOLDER = os.path.join(

    BASE_DIR,

    "static",

    "uploads"

)



if not os.path.exists(
    UPLOAD_FOLDER
):

    os.makedirs(
        UPLOAD_FOLDER
    )




ALLOWED_EXTENSIONS = {

    "png",

    "jpg",

    "jpeg",

    "webp"

}





# =====================================================
# FLASK CONFIGURATION
# =====================================================

class Config:



    # =================================================
    # SECURITY
    # =================================================

    SECRET_KEY = os.environ.get(

        "SECRET_KEY",

        "juians_gaibandha_secret_key_2026"

    )




    # =================================================
    # DATABASE
    # =================================================

    SQLALCHEMY_DATABASE_URI = (

        "sqlite:///"

        +

        DATABASE_PATH.replace(
            "\\",
            "/"
        )

    )


    SQLALCHEMY_TRACK_MODIFICATIONS = False





    # =================================================
    # FILE UPLOAD
    # =================================================

    UPLOAD_FOLDER = UPLOAD_FOLDER


    MAX_CONTENT_LENGTH = (

        2 *

        1024 *

        1024

    )



    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS





    # =================================================
    # SESSION SECURITY
    # =================================================

    SESSION_COOKIE_HTTPONLY = True


    SESSION_COOKIE_SAMESITE = "Lax"





    # =================================================
    # REMEMBER ME SETTINGS
    # =================================================

    PERMANENT_SESSION_LIFETIME = (

        60 *

        60 *

        24 *

        7

    )





    # =================================================
    # APPLICATION SETTINGS
    # =================================================

    APP_NAME = (

        "JUians of Gaibandha Portal"

    )


    VERSION = (

        "5.0"

    )





    # =================================================
    # PAGINATION
    # =================================================

    MEMBERS_PER_PAGE = 12





    # =================================================
    # TIMEZONE
    # =================================================

    TIMEZONE = (

        "Asia/Dhaka"

    )





# =====================================================
# DEVELOPMENT CONFIGURATION
# =====================================================

class DevelopmentConfig(Config):

    DEBUG = True





# =====================================================
# PRODUCTION CONFIGURATION
# =====================================================

class ProductionConfig(Config):

    DEBUG = False





# =====================================================
# TESTING CONFIGURATION
# =====================================================

class TestingConfig(Config):

    TESTING = True


    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///:memory:"
    )





# =====================================================
# CONFIG SELECTOR
# =====================================================

config = {


    "development": DevelopmentConfig,


    "production": ProductionConfig,


    "testing": TestingConfig,


    "default": DevelopmentConfig

}