from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pkg_a import greet


def test_greet_basic():
    assert greet("World") == "Hello, World!"


def test_greet_trims_nothing():
    assert greet(" Diogo ") == "Hello,  Diogo !"
