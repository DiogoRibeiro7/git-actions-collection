"""Imports only the standard library and the declared dependency."""

import json

from packaging.version import Version


def newest(versions: list[str]) -> str:
    return json.dumps(str(max(Version(v) for v in versions)))
