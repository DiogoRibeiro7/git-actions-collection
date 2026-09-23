from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SELF_MAIN = re.compile(
    r"DiogoRibeiro7/git-actions-collection/[^\s\"'\x60]+@main"
)


def _public_consumer_files() -> list[Path]:
    paths = [
        ROOT / "README.md",
        *ROOT.glob("docs/**/*.md"),
        *ROOT.glob("examples/**/*.md"),
        *ROOT.glob("examples/**/.github/workflows/*.yml"),
        *ROOT.glob("examples/**/.github/workflows/*.yaml"),
        *ROOT.glob(".github/actions/*/README.md"),
        *ROOT.glob(".vscode/*.code-snippets"),
    ]
    return sorted(path for path in paths if path.is_file())


def test_public_consumer_material_does_not_reference_main() -> None:
    offenders: list[str] = []
    for path in _public_consumer_files():
        content = path.read_text(encoding="utf-8")
        for match in SELF_MAIN.findall(content):
            offenders.append(f"{path.relative_to(ROOT)}: {match}")

    assert not offenders, (
        "Public consumer material must use stable v1 or an immutable SHA:\n"
        + "\n".join(offenders)
    )
