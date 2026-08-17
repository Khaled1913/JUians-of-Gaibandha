"""
JUians of Gaibandha
Upload Service

Handles:

- Member photo upload
- Event image upload
- Image validation
- Unique filename generation
- Photo replacement
- Old photo deletion
"""

import os
from uuid import uuid4

from werkzeug.utils import secure_filename


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
    )
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================
#
# Local:
#
#     static/uploads/
#
# Render / Production:
#
# If UPLOAD_FOLDER environment variable is configured,
# that location will be used instead.
#
# ============================================================

DEFAULT_UPLOAD_FOLDER = os.path.join(
    PROJECT_ROOT,
    "static",
    "uploads",
)


UPLOAD_FOLDER = os.environ.get(
    "UPLOAD_FOLDER",
    DEFAULT_UPLOAD_FOLDER,
)


UPLOAD_FOLDER = os.path.abspath(
    UPLOAD_FOLDER
)


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
}


# ============================================================
# MAXIMUM FILE SIZE
# ============================================================
#
# Maximum supported image size:
#
#     10 MB
#
# ============================================================

MAX_FILE_SIZE = (
    10
    *
    1024
    *
    1024
)


# ============================================================
# DEFAULT IMAGE NAMES
# ============================================================

PROTECTED_DEFAULT_IMAGES = {

    "default.png",

    "default_user.png",

    "images/default.png",

    "images/default_user.png",

    "images/ju_campus.jpeg",

    "images/Event_1.1.jpeg",

}


# ============================================================
# CREATE UPLOAD FOLDER
# ============================================================

def create_upload_folder():

    """
    Create the upload folder if it does not exist.
    """

    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True,
    )


# ============================================================
# FILE EXTENSION VALIDATION
# ============================================================

def allowed_file(filename):

    """
    Check whether the uploaded file has an allowed
    image extension.
    """

    if not filename:

        return False


    filename = str(
        filename
    ).strip()


    if not filename:

        return False


    if "." not in filename:

        return False


    extension = filename.rsplit(
        ".",
        1,
    )[1].lower()


    return (
        extension
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# GENERATE UNIQUE FILE NAME
# ============================================================

def generate_filename(filename):

    """
    Generate a unique filename while preserving
    the original file extension.
    """

    if not filename:

        return None


    filename = str(
        filename
    ).strip()


    if "." not in filename:

        return None


    extension = filename.rsplit(
        ".",
        1,
    )[1].lower()


    if extension not in ALLOWED_EXTENSIONS:

        return None


    return (
        f"{uuid4().hex}.{extension}"
    )


# ============================================================
# GET FILE SIZE
# ============================================================

def get_file_size(photo):

    """
    Safely determine the uploaded file size.

    Returns:

        int  -> file size in bytes

        None -> unable to determine size
    """

    try:

        stream = getattr(
            photo,
            "stream",
            None,
        )


        if stream is None:

            return None


        current_position = (
            stream.tell()
        )


        stream.seek(
            0,
            os.SEEK_END,
        )


        file_size = (
            stream.tell()
        )


        stream.seek(
            current_position,
            os.SEEK_SET,
        )


        return file_size


    except Exception:

        return None


# ============================================================
# NORMALIZE STORED IMAGE PATH
# ============================================================

def normalize_image_path(
    filename
):

    """
    Normalize an image reference.

    Examples:

        static/uploads/test.jpg
        uploads/test.jpg
        test.jpg

    Result:

        test.jpg
    """

    if not filename:

        return None


    filename = str(
        filename
    ).replace(
        "\\",
        "/",
    ).strip()


    if not filename:

        return None


    filename = (
        filename.lstrip("/")
    )


    if filename.startswith(
        "static/uploads/"
    ):

        filename = filename[
            len(
                "static/uploads/"
            ):
        ]


    elif filename.startswith(
        "uploads/"
    ):

        filename = filename[
            len(
                "uploads/"
            ):
        ]


    return os.path.basename(
        filename
    )


# ============================================================
# SAVE PHOTO
# ============================================================

def upload_photo(photo):

    """
    Upload and save an image.

    Maximum supported file size:

        10 MB

    Returns:

        filename

            Successful upload.

        "default.png"

            No photo provided.

        None

            Invalid upload.
    """

    create_upload_folder()


    # --------------------------------------------------------
    # No Photo Supplied
    # --------------------------------------------------------

    if photo is None:

        return "default.png"


    # --------------------------------------------------------
    # Empty File Field
    # --------------------------------------------------------

    original_name = getattr(
        photo,
        "filename",
        "",
    )


    if not original_name:

        return "default.png"


    original_name = (
        original_name.strip()
    )


    if not original_name:

        return "default.png"


    # --------------------------------------------------------
    # Validate Extension
    # --------------------------------------------------------

    if not allowed_file(
        original_name
    ):

        return None


    # --------------------------------------------------------
    # Secure Original Filename
    # --------------------------------------------------------

    original_filename = (
        secure_filename(
            original_name
        )
    )


    if not original_filename:

        return None


    # --------------------------------------------------------
    # Generate Unique Filename
    # --------------------------------------------------------

    filename = (
        generate_filename(
            original_filename
        )
    )


    if not filename:

        return None


    # --------------------------------------------------------
    # File Size Validation
    # --------------------------------------------------------

    file_size = (
        get_file_size(
            photo
        )
    )


    if file_size is None:

        return None


    if file_size <= 0:

        return None


    if file_size > MAX_FILE_SIZE:

        return None


    # --------------------------------------------------------
    # Reset Stream Before Saving
    # --------------------------------------------------------

    try:

        photo.stream.seek(
            0
        )

    except Exception:

        return None


    # --------------------------------------------------------
    # Save File
    # --------------------------------------------------------

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename,
    )


    try:

        photo.save(
            file_path
        )


    except Exception as exc:

        print(
            f"Image upload error: {exc}"
        )

        return None


    # --------------------------------------------------------
    # Verify File Was Saved
    # --------------------------------------------------------

    if not os.path.isfile(
        file_path
    ):

        return None


    # --------------------------------------------------------
    # Verify Stored File Is Not Empty
    # --------------------------------------------------------

    try:

        if (
            os.path.getsize(
                file_path
            )
            <= 0
        ):

            os.remove(
                file_path
            )

            return None


    except OSError:

        return None


    return filename


# ============================================================
# EVENT IMAGE UPLOAD
# ============================================================

def upload_event_image(photo):

    """
    Upload an event image.

    Event images are stored inside:

        static/uploads/

    Maximum supported file size:

        10 MB

    The returned value is a path relative to the
    Flask static directory.

    Example:

        uploads/abc123.jpg
    """

    if photo is None:

        return None


    if not getattr(
        photo,
        "filename",
        "",
    ):

        return None


    filename = (
        upload_photo(
            photo
        )
    )


    if not filename:

        return None


    # --------------------------------------------------------
    # default.png Is Not A Valid Event Image
    # --------------------------------------------------------

    if filename == "default.png":

        return None


    return (
        f"uploads/{filename}"
    )


# ============================================================
# DELETE PHOTO
# ============================================================

def delete_photo(filename):

    """
    Delete an uploaded image.

    Default/static images are never deleted.
    """

    if not filename:

        return


    # --------------------------------------------------------
    # Normalize Path
    # --------------------------------------------------------

    normalized_value = str(
        filename
    ).replace(
        "\\",
        "/",
    ).strip()


    normalized_value = (
        normalized_value.lstrip("/")
    )


    # --------------------------------------------------------
    # Remove Possible static/ Prefix
    # --------------------------------------------------------

    if normalized_value.startswith(
        "static/"
    ):

        normalized_value = (
            normalized_value[
                len(
                    "static/"
                ):
            ]
        )


    # --------------------------------------------------------
    # Default Image Protection
    # --------------------------------------------------------

    if (
        normalized_value
        in PROTECTED_DEFAULT_IMAGES
    ):

        return


    # --------------------------------------------------------
    # Do Not Delete Anything Inside Static Images
    # --------------------------------------------------------

    if normalized_value.startswith(
        "images/"
    ):

        return


    # --------------------------------------------------------
    # Only Use Filename
    # --------------------------------------------------------

    basename = normalize_image_path(
        normalized_value
    )


    if not basename:

        return


    # --------------------------------------------------------
    # Additional Protection
    # --------------------------------------------------------

    if basename in {

        "default.png",

        "default_user.png",

    }:

        return


    # --------------------------------------------------------
    # Build Upload Path
    # --------------------------------------------------------

    path = os.path.abspath(
        os.path.join(
            UPLOAD_FOLDER,
            basename,
        )
    )


    # --------------------------------------------------------
    # Security Check
    #
    # Prevent deleting files outside UPLOAD_FOLDER.
    # --------------------------------------------------------

    upload_root = (
        os.path.abspath(
            UPLOAD_FOLDER
        )
    )


    try:

        common_path = (
            os.path.commonpath(
                [
                    upload_root,
                    path,
                ]
            )
        )


    except ValueError:

        return


    if common_path != upload_root:

        return


    # --------------------------------------------------------
    # Delete File
    # --------------------------------------------------------

    if os.path.isfile(
        path
    ):

        try:

            os.remove(
                path
            )


        except OSError as exc:

            print(
                f"Image deletion error: {exc}"
            )


# ============================================================
# UPDATE / REPLACE PHOTO
# ============================================================

def replace_photo(
    old_photo,
    new_photo,
):

    """
    Replace an existing image.

    Maximum supported new image size:

        10 MB

    Process:

        1. Upload new image.

        2. Delete old image.

        3. Return new filename.

    If no valid new image is supplied,
    the old image remains unchanged.
    """

    # --------------------------------------------------------
    # No New Photo Selected
    # --------------------------------------------------------

    if new_photo is None:

        return old_photo


    # --------------------------------------------------------
    # Empty File Field
    # --------------------------------------------------------

    if not getattr(
        new_photo,
        "filename",
        "",
    ):

        return old_photo


    # --------------------------------------------------------
    # Upload New Photo
    # --------------------------------------------------------

    filename = (
        upload_photo(
            new_photo
        )
    )


    # --------------------------------------------------------
    # Upload Failed
    # --------------------------------------------------------

    if not filename:

        return old_photo


    # --------------------------------------------------------
    # default.png Means No Valid Replacement
    # --------------------------------------------------------

    if filename == "default.png":

        return old_photo


    # --------------------------------------------------------
    # Delete Previous Photo
    # --------------------------------------------------------

    if old_photo:

        delete_photo(
            old_photo
        )


    # --------------------------------------------------------
    # Return New Filename
    # --------------------------------------------------------

    return filename


# ============================================================
# END OF FILE
# ============================================================
