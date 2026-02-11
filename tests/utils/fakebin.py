from __future__ import annotations

from pathlib import Path
import os


def make_fakebin(tmp_path: Path, commands: dict[str, str]) -> Path:
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir(parents=True, exist_ok=True)
    for name, body in commands.items():
        path = fakebin / name
        path.write_text("#!/usr/bin/env bash\n" + body + "\n", encoding="utf-8")
        os.chmod(path, 0o755)
    return fakebin
