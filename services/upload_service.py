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
# UPLOAD CONFIGURATION
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
    )
)

UPLOAD_FOLDER = os.path.join(
    PROJECT_ROOT,
    "static",
    "uploads",
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


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

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1,
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# GENERATE UNIQUE FILE NAME
# ============================================================

def generate_filename(filename):
    """
    Generate a unique filename while preserving
    the original file extension.
    """

    if not filename or "." not in filename:
        return None

    extension = filename.rsplit(
        ".",
        1,
    )[1].lower()

    return f"{uuid4().hex}.{extension}"


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
        current_position = photo.stream.tell()

        photo.stream.seek(
            0,
            os.SEEK_END,
        )

        file_size = photo.stream.tell()

        photo.stream.seek(
            current_position,
            os.SEEK_SET,
        )

        return file_size

    except Exception:
        return None


# ============================================================
# SAVE PHOTO
# ============================================================

def upload_photo(photo):
    """
    Upload and save an image.

    Returns:
        filename -> successful upload
        "default.png" -> no photo provided
        None -> invalid upload
    """

    create_upload_folder()

    # --------------------------------------------------------
    # No photo supplied
    # --------------------------------------------------------

    if photo is None:
        return "default.png"

    # --------------------------------------------------------
    # Empty file field
    # --------------------------------------------------------

    if not getattr(
        photo,
        "filename",
        "",
    ):
        return "default.png"

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    if not allowed_file(
        photo.filename
    ):
        return None

    # --------------------------------------------------------
    # Secure original filename
    # --------------------------------------------------------

    original_filename = secure_filename(
        photo.filename
    )

    if not original_filename:
        return None

    # --------------------------------------------------------
    # Generate unique filename
    # --------------------------------------------------------

    filename = generate_filename(
        original_filename
    )

    if not filename:
        return None

    # --------------------------------------------------------
    # File size validation
    # --------------------------------------------------------

    file_size = get_file_size(
        photo
    )

    if file_size is None:
        return None

    if file_size > MAX_FILE_SIZE:
        return None

    # --------------------------------------------------------
    # Save file
    # --------------------------------------------------------

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename,
    )

    try:
        photo.save(
            file_path
        )

    except Exception:
        return None

    # --------------------------------------------------------
    # Verify file was actually saved
    # --------------------------------------------------------

    if not os.path.isfile(
        file_path
    ):
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

    filename = upload_photo(
        photo
    )

    if not filename:
        return None

    # upload_photo() can return default.png when
    # there is no uploaded file. That should not
    # happen for an event image.

    if filename == "default.png":
        return None

    return os.path.join(
        "uploads",
        filename,
    ).replace(
        "\\",
        "/",
    )


# ============================================================
# DELETE PHOTO
# ============================================================

def delete_photo(filename):
    """
    Delete an uploaded image.

    The default image is never deleted.
    """

    if not filename:
        return

    # --------------------------------------------------------
    # Normalize path
    # --------------------------------------------------------

    filename = str(
        filename
    ).replace(
        "\\",
        "/",
    )

    # --------------------------------------------------------
    # Remove possible static/ prefix
    # --------------------------------------------------------

    if filename.startswith(
        "static/"
    ):
        filename = filename[
            len("static/") :
        ]

    # --------------------------------------------------------
    # Default image protection
    # --------------------------------------------------------

    if filename in {
        "default.png",
        "images/default.png",
    }:
        return

    # --------------------------------------------------------
    # Only use the filename itself
    # --------------------------------------------------------

    basename = os.path.basename(
        filename
    )

    if not basename:
        return

    # --------------------------------------------------------
    # Build upload path
    # --------------------------------------------------------

    path = os.path.join(
        UPLOAD_FOLDER,
        basename,
    )

    # --------------------------------------------------------
    # Delete file
    # --------------------------------------------------------

    if os.path.isfile(
        path
    ):

        try:
            os.remove(
                path
            )

        except OSError:
            pass


# ============================================================
# UPDATE / REPLACE PHOTO
# ============================================================

def replace_photo(
    old_photo,
    new_photo,
):
    """
    Replace an existing image.

    Process:

        1. Upload new image.
        2. Delete old image.
        3. Return new filename.

    If no valid new image is supplied,
    the old image remains unchanged.
    """

    # --------------------------------------------------------
    # No new photo selected
    # --------------------------------------------------------

    if new_photo is None:
        return old_photo

    # --------------------------------------------------------
    # Empty file field
    # --------------------------------------------------------

    if not getattr(
        new_photo,
        "filename",
        "",
    ):
        return old_photo

    # --------------------------------------------------------
    # Upload new photo
    # --------------------------------------------------------

    filename = upload_photo(
        new_photo
    )

    # --------------------------------------------------------
    # Upload failed
    # --------------------------------------------------------

    if not filename:
        return old_photo

    # --------------------------------------------------------
    # Do not delete anything when default.png
    # is returned
    # --------------------------------------------------------

    if filename == "default.png":
        return old_photo

    # --------------------------------------------------------
    # Delete previous photo
    # --------------------------------------------------------

    if old_photo:
        delete_photo(
            old_photo
        )

    # --------------------------------------------------------
    # Return new filename
    # --------------------------------------------------------

    return filename