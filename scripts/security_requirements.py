"""Print Python package pins embedded in actions, workflows, and examples for pip-audit."""

from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9._-]*)==([0-9][A-Za-z0-9.!+_-]*)")


def collect_pins(root: Path) -> list[str]:
    """Collect literal package pins and the public pip-version defaults.

    Tests and lockfiles are deliberately excluded: they are fixtures or have
    their own package-manager audit. Variable package versions are resolved by
    the installed-environment audit, not guessed here.
    """
    paths = [
        *root.glob("scripts/**/*.sh"),
        *root.glob(".github/actions/*/action.y*ml"),
        *root.glob(".github/workflows/*.y*ml"),
        *root.glob("examples/*/pyproject.toml"),
        *root.glob("examples/*/requirements*.txt"),
    ]
    pins: set[str] = set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        pins.update(f"{name.lower()}=={version}" for name, version in PIN.findall(text))
        if path.suffix in {".yml", ".yaml"}:
            document = yaml.safe_load(text)
            inputs = document.get("inputs", {})
            events = document.get("on", document.get(True, {}))
            if isinstance(events, dict):
                inputs = (events.get("workflow_call") or {}).get("inputs", inputs)
            version = (inputs.get("pip-version") or {}).get("default")
            if version and version != "latest":
                pins.add(f"pip=={version}")
    return sorted(pins)


if __name__ == "__main__":
    print("\n".join(collect_pins(ROOT)))
