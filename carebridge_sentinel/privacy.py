from __future__ import annotations

import re


REDACTED = "[REDACTED]"

PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b"),
    re.compile(r"\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b"),
    re.compile(r"\bMRN[:\s#-]*[A-Z0-9-]+\b", re.IGNORECASE),
    re.compile(r"\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
]


def redact(text: str) -> str:
    output = text
    for pattern in PATTERNS:
        output = pattern.sub(REDACTED, output)
    return output
