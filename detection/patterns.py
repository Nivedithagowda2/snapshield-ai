"""Regex patterns for known sensitive-data formats. Each entry pairs a regex
with an optional checksum validator (from checksums.py) to reduce false
positives — a 12-digit number alone isn't an Aadhaar, but one that also
passes the Verhoeff check almost certainly is."""

import re
from detection.checksums import luhn_check, verhoeff_check

PATTERNS = {
    "aadhaar": {
        "regex": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
        "validator": verhoeff_check,
        "label": "Aadhaar Number",
    },
    "pan": {
        "regex": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
        "validator": None,
        "label": "PAN Number",
    },
    "card_number": {
        "regex": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
        "validator": luhn_check,
        "label": "Card Number",
    },
    "upi_id": {
        "regex": re.compile(r"\b[\w.\-]{2,256}@[a-zA-Z]{2,64}\b"),
        "validator": None,
        "label": "UPI ID",
    },
    "email": {
        "regex": re.compile(r"\b[\w.\-]+@[\w\-]+\.[a-zA-Z]{2,}\b"),
        "validator": None,
        "label": "Email Address",
    },
    "phone_in": {
        "regex": re.compile(r"\b(?:\+?91[\-\s]?)?[6-9]\d{2,4}[\-\s]?\d{2,4}[\-\s]?\d{0,4}\b"),
        "validator": None,
        "label": "Phone Number",
    },
    "aws_key": {
        "regex": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "validator": None,
        "label": "AWS Access Key",
    },
    "github_token": {
        "regex": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
        "validator": None,
        "label": "GitHub Token",
    },
    "generic_api_key": {
        "regex": re.compile(r"\bsk-[A-Za-z0-9_\-]{15,}\b"),
        "validator": None,
        "label": "API Key",
    },
    "google_api_key": {
        "regex": re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
        "validator": None,
        "label": "Google API Key",
    },
    "stripe_key": {
        "regex": re.compile(r"\b(sk|pk)_(live|test)_[0-9A-Za-z]{20,}\b"),
        "validator": None,
        "label": "Stripe Key",
    },
    "generic_bearer": {
        "regex": re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.]{20,}\b"),
        "validator": None,
        "label": "Bearer Token",
    },
    "jwt": {
        "regex": re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
        "validator": None,
        "label": "JWT Token",
    },
}

CONTEXT_KEYWORDS = [
    "password", "passwd", "pwd", "secret", "api_key", "apikey",
    "token", "auth", "credential", "private_key", "access_key",
]


def match_patterns(text: str):
    """Returns a list of (label, matched_string, start, end) for every
    pattern that matches AND passes its validator (if any)."""
    results = []
    for name, spec in PATTERNS.items():
        for m in spec["regex"].finditer(text):
            value = m.group(0)
            if spec["validator"] is None or spec["validator"](value):
                results.append((spec["label"], value, m.start(), m.end()))
    return results


def has_context_keyword(text: str, window: int = 30) -> bool:
    """Checks if a sensitive-sounding keyword appears near the given text
    region — used to boost confidence for entropy-based detections."""
    lowered = text.lower()
    return any(kw in lowered for kw in CONTEXT_KEYWORDS)
