from __future__ import annotations

from textwrap import dedent

CHECKOUT_REF = "3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON_REF = "ece7cb06caefa5fff74198d8649806c4678c61a1"
SETUP_NODE_REF = "249970729cb0ef3589644e2896645e5dc5ba9c38"
REPO = "DiogoRibeiro7/git-actions-collection"
CONSUMER_REF = "v1"


def python_workflow(branch: str) -> str:
    return dedent(
        f"""
        name: Python CI
        "on":
          push:
            branches: [{branch}]
          pull_request:

        permissions:
          contents: read

        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@{CHECKOUT_REF}
              - uses: actions/setup-python@{SETUP_PYTHON_REF}
                with:
                  python-version: '3.x'
                  cache: pip
              - run: pip install -r requirements.txt
              - run: pytest -q
        """
    ).lstrip()


def node_workflow(branch: str) -> str:
    return dedent(
        f"""
        name: Node CI
        "on":
          push:
            branches: [{branch}]
          pull_request:

        permissions:
          contents: read

        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@{CHECKOUT_REF}
              - uses: actions/setup-node@{SETUP_NODE_REF}
                with:
                  node-version: '24'
                  cache: yarn
              - run: corepack enable
              - run: yarn install --immutable
              - run: yarn test
        """
    ).lstrip()
