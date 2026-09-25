from __future__ import annotations

from pathlib import Path

from scripts import action_docs as docs

ROOT = Path(__file__).resolve().parents[1]
METADATA = {
    "inputs": {
        "token": {"description": "Token | scope", "required": True},
        "mode": {"description": "Run\n  mode", "default": ""},
        "strict": {"description": "Fail on warnings", "default": False},
    },
    "outputs": {"report": {"description": "JSON report"}},
}


def test_action_readmes_match_their_metadata() -> None:
    stale = docs.stale_readmes(ROOT, write=False)

    assert not stale, "Run `python scripts/action_docs.py --write`:\n" + "\n".join(stale)


def test_render_reference_tabulates_inputs_and_outputs() -> None:
    lines = docs.render_reference(METADATA).splitlines()

    assert lines[0] == docs.BEGIN and lines[-1] == docs.END
    assert "| `token` | yes |  | Token \\| scope |" in lines
    assert '| `mode` | no | `""` | Run mode |' in lines
    assert "| `strict` | no | `false` | Fail on warnings |" in lines
    assert "| `report` | JSON report |" in lines


def test_render_reference_states_when_there_is_nothing_to_list() -> None:
    reference = docs.render_reference({})

    assert "This action has no inputs." in reference
    assert "This action has no outputs." in reference


def test_update_readme_replaces_only_the_generated_section() -> None:
    readme = f"# Title\n\nIntro.\n\n{docs.BEGIN}\nold\n{docs.END}\n\n## Example\n\nKept.\n"

    updated = docs.update_readme(readme, f"{docs.BEGIN}\nnew\n{docs.END}")

    assert updated == f"# Title\n\nIntro.\n\n{docs.BEGIN}\nnew\n{docs.END}\n\n## Example\n\nKept.\n"


def test_update_readme_replaces_hand_written_inputs_and_outputs_in_place() -> None:
    readme = (
        "# Title\n\n## Overview\n\nText.\n\n## Inputs\n\n- `a`\n\n## Outputs\n\nNone\n\n"
        "## Example\n\nKept.\n"
    )

    updated = docs.update_readme(readme, "GENERATED")

    assert updated == "# Title\n\n## Overview\n\nText.\n\nGENERATED\n\n## Example\n\nKept.\n"


def test_update_readme_inserts_before_the_first_section_or_at_the_end() -> None:
    assert docs.update_readme("# T\n\nIntro.\n\n## Usage\n", "GEN") == "# T\n\nIntro.\n\nGEN\n\n## Usage\n"
    assert docs.update_readme("# T\n\nIntro.\n", "GEN") == "# T\n\nIntro.\n\nGEN\n"


def test_missing_readme_starts_from_the_action_metadata(tmp_path: Path) -> None:
    action = tmp_path / ".github" / "actions" / "demo"
    action.mkdir(parents=True)
    (action / "action.yml").write_text("name: Demo\ndescription: Does things\n", encoding="utf-8")

    assert docs.stale_readmes(tmp_path, write=True) == [".github/actions/demo/README.md"]
    readme = (action / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Demo\n\nDoes things\n\n" + docs.BEGIN)
    assert docs.stale_readmes(tmp_path, write=False) == []
