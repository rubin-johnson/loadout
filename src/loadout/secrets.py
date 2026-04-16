from __future__ import annotations

import pathlib
import re

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AKIA token", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token (ghp_)", re.compile(r"ghp_[A-Za-z0-9]+")),
    ("OpenAI token (sk-)", re.compile(r"sk-[A-Za-z0-9]+")),
    ("Slack bot token (xoxb-)", re.compile(r"xoxb-[A-Za-z0-9-]+")),
    ("Slack user token (xoxp-)", re.compile(r"xoxp-[A-Za-z0-9-]+")),
    ("export of sensitive variable", re.compile(r"export\s+(?:PASSWORD|TOKEN|SECRET|KEY|CREDENTIAL|API)\w*=(\S+)")),
    ("PASSWORD/TOKEN/SECRET/API_KEY assignment", re.compile(r"(?:PASSWORD|TOKEN|SECRET|API_KEY)\s*=\s*(\S+)")),
]


def scan_for_secrets(path: pathlib.Path) -> list[str]:
    warnings: list[str] = []
    for n, line in enumerate(path.read_text().splitlines(), start=1):
        for label, pattern in _PATTERNS:
            if pattern.search(line):
                warnings.append(f"Line {n}: potential secret matched pattern '{label}'")
                break
    return warnings
