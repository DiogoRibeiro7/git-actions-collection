from __future__ import annotations

from pathlib import Path
import re

from scripts import workflow_docs as docs
from scripts.workflow_docs import Component

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = {"supported": "Stable.", "reference": "Useful.", "experimental": "Early."}
WORKFLOW = """\
# Deploys a thing
# to production.
name: Deploy
on:
  workflow_call:
    inputs:
      target:
        description: Where to deploy
        required: true
        type: string
      dry-run:
        description: Plan only
        type: boolean
        default: true
    outputs:
      url:
        description: Deployed URL
        value: ${{ jobs.deploy.outputs.url }}
    secrets:
      TOKEN:
        description: Deploy token
        required: true
permissions:
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - run: echo deploy
"""


def _repo(tmp_path: Path) -> Path:
    path = tmp_path / ".github" / "workflows" / "deploy.yml"
    path.parent.mkdir(parents=True)
    path.write_text(WORKFLOW, encoding="utf-8")
    return tmp_path


def test_every_public_workflow_opens_with_a_description() -> None:
    missing = [
        component.name
        for component in docs.public_components(ROOT)
        if component.kind == "workflow" and not component.description
    ]

    assert not missing, "Start these workflows with a `# description` comment:\n" + "\n".join(missing)


def test_public_components_cover_every_tiered_workflow_and_action() -> None:
    components = docs.public_components(ROOT)
    matrix = docs.support_matrix(ROOT)

    for kind, key in (("workflow", "workflows"), ("action", "composite_actions")):
        expected = {name for tier in docs.TIERS for name in matrix[key].get(tier) or []}
        assert {c.name for c in components if c.kind == kind} == expected
    assert all(c.description for c in components if c.kind == "action")


def test_workflow_description_joins_the_opening_comment(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    assert docs.workflow_description(root / ".github/workflows/deploy.yml") == "Deploys a thing to production."


def test_workflow_page_documents_the_interface(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    component = Component("workflow", "deploy.yml", "experimental", "Deploy", "Deploys a thing.")

    page = docs.render_workflow_page(root, component, DEFINITIONS, [("Guide", "docs/guide.md")])

    assert page.startswith("# Deploy\n\nDeploys a thing.\n\n!!! warning \"Experimental\"\n    Early.\n")
    assert (
        "    uses: DiogoRibeiro7/git-actions-collection/.github/workflows/deploy.yml@v1\n"
        "    permissions:\n      contents: read\n      id-token: write\n"
        "    with:\n      target: <string>\n"
        "    secrets:\n      TOKEN: ${{ secrets.TOKEN }}\n"
    ) in page
    assert "| `target` | string | yes |  | Where to deploy |" in page
    assert "| `dry-run` | boolean | no | `true` | Plan only |" in page
    assert "| `url` | Deployed URL |" in page
    assert "| `TOKEN` | yes | Deploy token |" in page
    assert "- [Guide](docs/guide.md)" in page
    assert "blob/main/.github/workflows/deploy.yml" in page


def test_catalogue_groups_components_by_tier() -> None:
    components = [
        Component("workflow", "b.yml", "reference", "B", "Does b."),
        Component("action", "a", "supported", "A", "Does a."),
        Component("workflow", "c.yml", "supported", "C", "Does c | pipes."),
    ]

    catalogue = docs.render_catalogue(components, DEFINITIONS, lambda c: f"link/{c.name}")

    supported = catalogue.index("## Supported")
    reference = catalogue.index("## Reference")
    assert supported < catalogue.index("[`c.yml`](link/c.yml)") < reference
    assert supported < catalogue.index("[`a`](link/a)") < reference
    assert reference < catalogue.index("[`b.yml`](link/b.yml)")
    assert "Does c \\| pipes." in catalogue
    assert "## Experimental" in catalogue  # tiers are always introduced


def test_readme_lists_exactly_the_supported_components() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    linked = set(re.findall(r"\]\(\.github/(?:workflows|actions)/([^)/]+)\)", readme))
    supported = {c.name for c in docs.public_components(ROOT) if c.tier == "supported"}

    assert linked == supported, "Update the README's supported component tables"
