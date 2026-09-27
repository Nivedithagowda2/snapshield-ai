"""Combines pattern matches, entropy signals, and context keywords into a
single confidence score and a final list of regions to blur."""

from detection.patterns import match_patterns, has_context_keyword
from detection.entropy import find_high_entropy_tokens

BLUR_THRESHOLD = 0.6

# A standalone string this long AND this random is almost never normal
# text — mixed-case alphanumeric plus symbols at this length is the
# signature of a generated token, not a word or sentence. This tier does
# NOT require a nearby "password"/"key" label, because on real screens
# the label and the value are almost always read as SEPARATE OCR text
# regions (different UI elements), so same-fragment context matching
# misses most real secrets.
OBVIOUS_SECRET_ENTROPY = 4.0
OBVIOUS_SECRET_MIN_LEN = 24


def score_text_region(text: str, box) -> list:
    """
    text: the OCR'd string for this region
    box: bounding box for this region
    Returns a list of dicts: {label, value, confidence, box}
    """
    findings = []

    # Layer 1: known patterns + checksum validation -> high confidence
    for label, value, start, end in match_patterns(text):
        findings.append({
            "label": label,
            "value": value,
            "confidence": 0.95,
            "box": box,
        })

    # Layer 2: entropy-based unknown secrets
    for token, entropy_score, start, end in find_high_entropy_tokens(text):
        nearby = text[max(0, start - 30): end + 30]

        if entropy_score >= OBVIOUS_SECRET_ENTROPY and len(token) >= OBVIOUS_SECRET_MIN_LEN:
            confidence = 0.8
        elif has_context_keyword(nearby):
            confidence = 0.85
        else:
            confidence = 0.5

        if confidence >= BLUR_THRESHOLD:
            findings.append({
                "label": "Possible Secret (high entropy)",
                "value": token,
                "confidence": confidence,
                "box": box,
            })

    return findings


def should_blur(findings: list) -> bool:
    return any(f["confidence"] >= BLUR_THRESHOLD for f in findings)
