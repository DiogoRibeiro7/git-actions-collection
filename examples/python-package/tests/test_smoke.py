import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from demo import add


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (1, 2, 3),
        (0, 0, 0),
        (-1, 1, 0),
        (-5, -7, -12),
        (10, -3, 7),
        (1_000_000, 2_000_000, 3_000_000),
    ],
)
def test_add(a, b, expected):
    assert add(a, b) == expected


def test_add_commutative():
    assert add(2, 5) == add(5, 2)


def test_add_associative():
    a, b, c = 3, -4, 10
    assert add(add(a, b), c) == add(a, add(b, c))
