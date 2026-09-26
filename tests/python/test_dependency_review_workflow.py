from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/dependency-review.yml"


def test_review_runs_only_where_the_action_can_find_base_and_head_refs() -> None:
    """dependency-review-action throws on events without pull request or merge group refs."""
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    assert data["jobs"]["review"]["if"] == (
        "contains(fromJson('[\"pull_request\",\"pull_request_target\",\"merge_group\"]'), "
        "github.event_name)"
    )


def test_review_only_reads_the_repository() -> None:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    assert data["permissions"] == {"contents": "read"}
