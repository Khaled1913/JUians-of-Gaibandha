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
from urllib.parse import unquote, urlparse
from uuid import uuid4

import cloudinary
import cloudinary.uploader
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
# CLOUDINARY CONFIGURATION
# ============================================================

def _cloudinary_is_configured():
    """
    Check whether all required Cloudinary environment
    variables are available.
    """

    return all(
        os.environ.get(name)
        for name in (
            "CLOUDINARY_CLOUD_NAME",
            "CLOUDINARY_API_KEY",
            "CLOUDINARY_API_SECRET",
        )
    )


def _configure_cloudinary():
    """
    Configure the Cloudinary Python SDK.
    """

    if not _cloudinary_is_configured():
        return False

    cloudinary.config(
        cloud_name=os.environ[
            "CLOUDINARY_CLOUD_NAME"
        ],
        api_key=os.environ[
            "CLOUDINARY_API_KEY"
        ],
        api_secret=os.environ[
            "CLOUDINARY_API_SECRET"
        ],
        secure=True,
    )

    return True


def _cloudinary_public_id(image_url):
    """
    Extract a Cloudinary public ID from a Cloudinary URL.
    """

    if not image_url:
        return None

    image_url = str(
        image_url
    ).strip()

    if "res.cloudinary.com" not in image_url:
        return None

    path = unquote(
        urlparse(image_url).path
    )

    if "/upload/" not in path:
        return None

    parts = (
        path
        .split("/upload/", 1)[1]
        .split("/")
    )

    if (
        parts
        and parts[0].startswith("v")
        and parts[0][1:].isdigit()
    ):
        parts = parts[1:]

    public_id = "/".join(
        parts
    )

    filename = public_id.rsplit(
        "/",
        1,
    )[-1]

    if "." in filename:
        public_id = public_id.rsplit(
            ".",
            1,
        )[0]

    return public_id or None


# ============================================================
# MAXIMUM FILE SIZE
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
    Create the local upload folder if it does not exist.
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

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# GENERATE UNIQUE FILE NAME
# ============================================================

def generate_filename(filename):
    """
    Generate a unique filename while preserving
    the original extension.
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

    return f"{uuid4().hex}.{extension}"


# ============================================================
# GET FILE SIZE
# ============================================================

def get_file_size(photo):
    """
    Safely determine the uploaded file size.
    """

    try:
        stream = getattr(
            photo,
            "stream",
            None,
        )

        if stream is None:
            return None

        current_position = stream.tell()

        stream.seek(
            0,
            os.SEEK_END,
        )

        file_size = stream.tell()

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

def normalize_image_path(filename):
    """
    Normalize a locally stored image reference.

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

    filename = filename.lstrip(
        "/"
    )

    if filename.startswith(
        "static/uploads/"
    ):
        filename = filename[
            len("static/uploads/"):
        ]

    elif filename.startswith(
        "uploads/"
    ):
        filename = filename[
            len("uploads/"):
        ]

    return os.path.basename(
        filename
    )


# ============================================================
# SAVE MEMBER PHOTO LOCALLY
# ============================================================

def upload_photo(photo):
    """
    Upload and locally save a member image.

    Returns:

        filename:
            Successful upload.

        default.png:
            No photo provided.

        None:
            Invalid upload.
    """

    create_upload_folder()

    if photo is None:
        return "default.png"

    original_name = getattr(
        photo,
        "filename",
        "",
    )

    if not original_name:
        return "default.png"

    original_name = original_name.strip()

    if not original_name:
        return "default.png"

    if not allowed_file(
        original_name
    ):
        return None

    original_filename = secure_filename(
        original_name
    )

    if not original_filename:
        return None

    filename = generate_filename(
        original_filename
    )

    if not filename:
        return None

    file_size = get_file_size(
        photo
    )

    if file_size is None:
        return None

    if file_size <= 0:
        return None

    if file_size > MAX_FILE_SIZE:
        return None

    try:
        photo.stream.seek(0)

    except Exception:
        return None

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

    if not os.path.isfile(
        file_path
    ):
        return None

    try:
        if os.path.getsize(
            file_path
        ) <= 0:
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
    Upload an Event image to Cloudinary when Cloudinary
    credentials are available.

    If Cloudinary is not configured, local storage is used
    as a fallback.
    """

    if photo is None:
        return None

    original_name = getattr(
        photo,
        "filename",
        "",
    )

    if not original_name:
        return None

    original_name = original_name.strip()

    if not original_name:
        return None

    if not allowed_file(
        original_name
    ):
        return None

    file_size = get_file_size(
        photo
    )

    if file_size is None:
        return None

    if file_size <= 0:
        return None

    if file_size > MAX_FILE_SIZE:
        return None

    try:
        photo.stream.seek(0)

    except Exception:
        return None

    if _configure_cloudinary():
        folder = os.environ.get(
            "CLOUDINARY_FOLDER",
            "juians_of_gaibandha",
        ).strip("/")

        try:
            result = cloudinary.uploader.upload(
                photo,
                folder=f"{folder}/events",
                resource_type="image",
                unique_filename=True,
                overwrite=False,
                use_filename=False,
            )

        except Exception as exc:
            print(
                f"Cloudinary upload error: {exc}"
            )
            return None

        secure_url = result.get(
            "secure_url"
        )

        if not secure_url:
            return None

        return secure_url

    filename = upload_photo(
        photo
    )

    if not filename:
        return None

    if filename == "default.png":
        return None

    return f"uploads/{filename}"


# ============================================================
# DELETE PHOTO
# ============================================================

def delete_photo(filename):
    """
    Delete a Cloudinary or locally stored uploaded image.

    Default/static images are never deleted.
    """

    if not filename:
        return

    filename = str(
        filename
    ).strip()

    if not filename:
        return

    # Delete a Cloudinary image.
    if filename.startswith(
        (
            "https://",
            "http://",
        )
    ):
        public_id = _cloudinary_public_id(
            filename
        )

        if (
            public_id
            and _configure_cloudinary()
        ):
            try:
                cloudinary.uploader.destroy(
                    public_id,
                    resource_type="image",
                    invalidate=True,
                )

            except Exception as exc:
                print(
                    f"Cloudinary deletion error: {exc}"
                )

        return

    normalized_value = filename.replace(
        "\\",
        "/",
    ).strip()

    normalized_value = normalized_value.lstrip(
        "/"
    )

    if normalized_value.startswith(
        "static/"
    ):
        normalized_value = normalized_value[
            len("static/"):
        ]

    if normalized_value in PROTECTED_DEFAULT_IMAGES:
        return

    if normalized_value.startswith(
        "images/"
    ):
        return

    basename = normalize_image_path(
        normalized_value
    )

    if not basename:
        return

    if basename in {
        "default.png",
        "default_user.png",
    }:
        return

    path = os.path.abspath(
        os.path.join(
            UPLOAD_FOLDER,
            basename,
        )
    )

    upload_root = os.path.abspath(
        UPLOAD_FOLDER
    )

    try:
        common_path = os.path.commonpath(
            [
                upload_root,
                path,
            ]
        )

    except ValueError:
        return

    if common_path != upload_root:
        return

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
# UPDATE / REPLACE MEMBER PHOTO
# ============================================================

def replace_photo(
    old_photo,
    new_photo,
):
    """
    Replace an existing member photo.

    If no valid new photo is supplied, the previous
    photo remains unchanged.
    """

    if new_photo is None:
        return old_photo

    if not getattr(
        new_photo,
        "filename",
        "",
    ):
        return old_photo

    filename = upload_photo(
        new_photo
    )

    if not filename:
        return old_photo

    if filename == "default.png":
        return old_photo

    if old_photo:
        delete_photo(
            old_photo
        )

    return filename


# ============================================================
# END OF FILE
# ============================================================