import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Fixtures are consumer projects that the composite-action self-tests run with
# their own tools (for example a pytest-benchmark suite), not tests of this repo.
collect_ignore_glob = ["fixtures/*"]
