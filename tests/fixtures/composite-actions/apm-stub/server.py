"""Stub APM endpoint for the apm-integration real-runner self-test.

Every POST is appended to requests.jsonl in the working directory, with its path,
headers (lower-cased names) and body. Paths under /reject get 403, so the test
can check that a refused request fails the action; every other path gets 202.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path

LOG = Path("requests.jsonl")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        record = {
            "path": self.path,
            "headers": {name.lower(): value for name, value in self.headers.items()},
            "body": self.rfile.read(length).decode("utf-8"),
        }
        with LOG.open("a", encoding="utf-8") as log:
            log.write(json.dumps(record) + "\n")
        self.send_response(403 if self.path.startswith("/reject") else 202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, format: str, *args: object) -> None:
        """Keep access logs out of the job output."""


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
