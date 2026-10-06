"""Regression tests for the setup-r package installer helper."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts" / "setup-r" / "install-packages.R"


def test_package_splitter_preserves_letter_n() -> None:
    text = INSTALLER.read_text(encoding="utf-8")

    assert 'strsplit(packages, "[,[:space:]]+")' in text
    assert '"[,\\n ]+"' not in text
