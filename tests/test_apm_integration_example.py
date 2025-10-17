from pathlib import Path


def test_workflow_references_action():
    wf = Path('examples/apm-integration/.github/workflows/deploy.yml').read_text()
    assert 'apm-integration@main' in wf
