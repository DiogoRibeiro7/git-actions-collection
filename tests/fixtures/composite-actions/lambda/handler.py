"""Consumer fixture for the aws-lambda-build self-test."""

from packaging.version import Version


def handler(event, context):
    return {"newest": str(max(Version(v) for v in event.get("versions", ["0"])))}
