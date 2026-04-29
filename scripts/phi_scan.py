from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCAN_PATHS = [
    ROOT / "carebridge_sentinel",
    ROOT / "scripts",
    ROOT / "tests",
    ROOT / "submission",
    ROOT / "README.md",
    ROOT / "Dockerfile",
    ROOT / "docker-compose.yml",
    ROOT / "requirements.txt",
]

PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "mrn": re.compile(r"\bMRN[:\s#-]*[A-Z0-9-]+\b", re.IGNORECASE),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
}

ALLOWLIST = {
    "tests/test_privacy.py",
}


def main() -> None:
    findings: list[str] = []
    for path in _files_to_scan():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(errors="ignore")
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                if rel in ALLOWLIST:
                    continue
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{rel}:{line}: possible {name}")

    if findings:
        print("PHI/token scan failed:")
        print("\n".join(findings))
        sys.exit(1)

    print("PHI/token scan passed.")


def _files_to_scan() -> list[Path]:
    files: list[Path] = []
    for path in SCAN_PATHS:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                item
                for item in path.rglob("*")
                if item.is_file()
                and item.suffix in {".py", ".md", ".txt", ".yml", ".yaml", ".toml", ".json"}
            )
    return sorted(files)


if __name__ == "__main__":
    main()
