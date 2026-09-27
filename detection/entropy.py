"""Shannon entropy scoring — catches secrets in formats we never wrote a
regex for. A random-looking string with high character-level entropy
(e.g. 'x7Ff9-QpL2mZ_eR8vN3wK') is very likely a token/secret even if it
doesn't match any known prefix.""" 

import math
import re 

_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-+/=.]{16,}") 


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def find_high_entropy_tokens(text: str, threshold: float = 3.5, min_len: int = 16):
    """Scans text for substrings that look like secrets based on entropy
    alone. Returns (token, entropy_score, start, end)."""
    results = []
    for m in _TOKEN_RE.finditer(text):
        token = m.group(0)
        if len(token) < min_len:
            continue
        score = shannon_entropy(token)
        if score >= threshold:
            results.append((token, score, m.start(), m.end()))
    return results
