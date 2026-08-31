from __future__ import annotations

import os
from pathlib import Path


def _write_grep_wrapper(fakebin: Path) -> None:
    """Install a grep shim that treats dash-prefixed fixture patterns literally."""
    path = fakebin / "grep"
    path.write_text(
        """#!/usr/bin/env bash
if [ "${1:-}" = "-q" ] && [[ "${2:-}" == --* ]]; then
  pattern="$2"
  shift 2
  exec /usr/bin/grep -q -- "$pattern" "$@"
fi
exec /usr/bin/grep "$@"
""",
        encoding="utf-8",
    )
    os.chmod(path, 0o755)


def make_fakebin(tmp_path: Path, commands: dict[str, str]) -> Path:
    """Create deterministic command shims used by composite-action tests."""
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir(parents=True, exist_ok=True)
    if "grep" not in commands:
        _write_grep_wrapper(fakebin)
    for name, body in commands.items():
        path = fakebin / name
        path.write_text("#!/usr/bin/env bash\n" + body + "\n", encoding="utf-8")
        os.chmod(path, 0o755)
    return fakebin
