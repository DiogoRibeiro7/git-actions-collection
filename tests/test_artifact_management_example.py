from pathlib import Path


def test_workflow_references_reusable():
    wf = Path("examples/artifact-management/.github/workflows/cleanup.yml").read_text()
    assert "artifact-management.yml@develop" in wf
