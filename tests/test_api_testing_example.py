from pathlib import Path


def test_workflow_references_reusable():
    wf = Path("examples/api-testing/.github/workflows/ci.yml").read_text()
    assert "api-testing.yml@develop" in wf
