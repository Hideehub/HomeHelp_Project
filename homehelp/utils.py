import os
import secrets
from decimal import Decimal, InvalidOperation

from flask import current_app

ALLOWED_IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif'}


def save_image(file):
    """Save an uploaded image and return its filename.

    Returns None if no file was submitted, False if the file is not an allowed image.
    """
    if not file or not file.filename:
        return None
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        return False
    filename = f'{secrets.token_hex(10)}{ext}'
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return filename


def parse_amount(value):
    """Parse a positive money amount with at most 2 decimal places, or return None."""
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        return None
    if not amount.is_finite() or amount <= 0:
        return None
    return amount.quantize(Decimal('0.01'))
