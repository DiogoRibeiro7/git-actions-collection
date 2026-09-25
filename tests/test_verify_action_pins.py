from __future__ import annotations

from pathlib import Path

from scripts import verify_action_pins as pins

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "1" * 40
TAG_OBJECT = "2" * 40
MOVING_MAJOR = "3" * 40
UNTAGGED = "4" * 40

LS_REMOTE = f"""\
{TAG_OBJECT}\trefs/tags/v2.0.0
{RELEASE}\trefs/tags/v2.0.0^{{}}
{MOVING_MAJOR}\trefs/tags/v1
"""


def test_parse_tags_peels_annotated_tags() -> None:
    commits, tag_objects = pins.parse_tags(LS_REMOTE)

    assert commits == {RELEASE: ["v2.0.0"], MOVING_MAJOR: ["v1"]}
    assert tag_objects == {TAG_OBJECT}


def test_problems_explain_each_kind_of_bad_pin() -> None:
    found = pins.problems(
        {
            ("owner/action", RELEASE): {"a.yml"},
            ("owner/action", MOVING_MAJOR): {"b.yml"},
            ("owner/action", TAG_OBJECT): {"c.yml"},
            ("owner/action", UNTAGGED): {"d.yml", "e.yml"},
            ("owner/missing", RELEASE): {"f.yml"},
        },
        tags_of=lambda repository: LS_REMOTE if repository == "owner/action" else None,
    )

    assert found == [
        f"owner/action@{TAG_OBJECT} is an annotated tag object; pin the commit it points to (c.yml)",
        f"owner/action@{UNTAGGED} is not the commit of any tag (d.yml, e.yml)",
        f"owner/missing@{RELEASE} repository not found (f.yml)",
    ]


def test_pinned_actions_covers_workflows_composite_actions_and_examples() -> None:
    found = pins.pinned_actions(ROOT)
    files = {file for pinned in found.values() for file in pinned}

    assert {repository for repository, _ in found} >= {"actions/checkout", "actions/setup-node"}
    assert any(file.startswith(".github/workflows/") for file in files)
    assert any(file.startswith(".github/actions/") for file in files)
    assert any(file.startswith("examples/") for file in files)
    assert all(pins.COMMIT_SHA.fullmatch(sha) for _, sha in found)
