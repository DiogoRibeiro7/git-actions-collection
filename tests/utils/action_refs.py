"""Assert on `uses:` references without hardcoding the pinned commit SHA.

Dependabot moves the SHAs; `tests/test_action_pinning.py` enforces that every
reference stays pinned. Workflow tests only need to know which action is used.
"""

from __future__ import annotations

import re

COMMIT_SHA = re.compile(r"[0-9a-f]{40}")


def action_name(uses: str | None) -> str:
    """Return the action path of a `uses:` reference without its ref."""
    return (uses or "").partition("@")[0]


def is_commit_pinned(uses: str | None, action: str) -> bool:
    """True when `uses` references `action` at a full 40-character commit SHA."""
    name, _, ref = (uses or "").partition("@")
    return name == action and COMMIT_SHA.fullmatch(ref) is not None
