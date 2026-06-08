from __future__ import annotations

import re


def validate_language_code(code: str) -> bool:
    return bool(re.match(r"^[a-z]{2}(-[A-Z]{2})?$", code))


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^\w\-_. ]", "", name).strip() or "untitled"
