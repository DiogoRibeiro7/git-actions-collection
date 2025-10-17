import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demo import add


def test_add():
    assert add(1, 2) == 3
