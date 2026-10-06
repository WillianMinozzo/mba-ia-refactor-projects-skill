import re
from datetime import datetime, timezone

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def utcnow():
    """UTC atual como datetime ingênuo, no mesmo formato já gravado no banco."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_REGEX.match(email) is not None
