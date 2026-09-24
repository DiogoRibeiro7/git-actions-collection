"""Assert the real composite action's result from a separate consumer workspace."""

import json
import os
from pathlib import Path

report = json.loads(os.environ["REPORT"])
manifest = json.loads(Path("package.json").read_text(encoding="utf-8"))
apply = os.environ["APPLY"] == "true"

assert report["conflicts"] == {}
assert report["alerts"] == []
assert manifest["dependencies"]["fixture-package"] == ("^1.2.4" if apply else "^1.2.3")
if apply:
    assert len(report["updates"]) == 1
    assert report["updates"][0]["name"] == "fixture-package"
    assert report["updates"][0]["updated"] == "^1.2.4"
else:
    assert report["updates"] == []
