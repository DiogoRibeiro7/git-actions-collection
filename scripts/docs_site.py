"""Assemble the documentation site from Markdown spread across the repository.

MkDocs only reads `docs/`, but the repository keeps its policy files at the root
and usage guides beside examples and composite actions. The mkdocs-gen-files
plugin runs this module on every build: it publishes those files as site pages,
rewrites their relative links to the published pages (or to GitHub for files
outside the site), and writes the navigation read by mkdocs-literate-nav.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
import posixpath
import re

REPOSITORY = "https://github.com/DiogoRibeiro7/git-actions-collection"
RAW = "https://raw.githubusercontent.com/DiogoRibeiro7/git-actions-collection/main"
ROOT = Path(__file__).resolve().parents[1]

# Root policy pages in navigation order: repository path -> (site path, title).
ROOT_PAGES = {
    "README.md": ("index.md", "Home"),
    "SUPPORT.md": ("support.md", "Support policy"),
    "RELEASES.md": ("releases.md", "Releases"),
    "ROADMAP.md": ("roadmap.md", "Roadmap"),
    "CHANGELOG.md": ("changelog.md", "Changelog"),
    "CONTRIBUTING.md": ("contributing.md", "Contributing"),
}

INLINE_LINK = re.compile(r"(?P<prefix>!?\[[^\]]*\]\()(?P<target>[^)\s]+)(?P<suffix>[^)]*\))")
REFERENCE_LINK = re.compile(r"^(?P<prefix>\s{0,3}\[[^\]]+\]:\s*)(?P<target>\S+)(?P<suffix>.*)$")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
FENCE = re.compile(r"^\s{0,3}(```|~~~)")


@dataclass(frozen=True)
class Page:
    """A repository Markdown file published at a site path."""

    source: str
    target: str
    title: str


def _title(path: Path, fallback: str) -> str:
    """Use the first level-one heading, which is what readers see on the page."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def discover_pages(root: Path) -> list[Page]:
    """Find every Markdown file the site publishes."""
    pages = [Page(source, target, title) for source, (target, title) in ROOT_PAGES.items()]
    pages += [
        Page(f"docs/{path.name}", path.name, _title(path, path.stem))
        for path in sorted((root / "docs").glob("*.md"))
    ]
    for directory, section in (("examples", "examples"), (".github/actions", "actions")):
        pages += [
            Page(
                f"{directory}/{path.parent.name}/README.md",
                f"{section}/{path.parent.name}.md",
                path.parent.name,
            )
            for path in sorted((root / directory).glob("*/README.md"))
        ]
    return pages


def resolve_link(
    target: str, page: Page, pages: Mapping[str, Page], root: Path, image: bool
) -> str:
    """Map a link written for GitHub to the equivalent link on the site."""
    if SCHEME.match(target) or target.startswith(("#", "/")):
        return target
    path, _, fragment = target.partition("#")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(page.source), path))
    if resolved.startswith(".."):
        return target
    anchor = f"#{fragment}" if fragment else ""

    linked = pages.get(resolved) or pages.get(posixpath.join(resolved, "README.md"))
    if linked is not None:
        start = posixpath.dirname(page.target) or "."
        return posixpath.relpath(linked.target, start) + anchor

    location = root / resolved
    if not location.exists():
        return target  # left unchanged so `mkdocs build --strict` reports it
    if image:
        return f"{RAW}/{resolved}"
    kind = "tree" if location.is_dir() else "blob"
    return f"{REPOSITORY}/{kind}/main/{resolved}{anchor}"


def rewrite_links(text: str, page: Page, pages: Mapping[str, Page], root: Path) -> str:
    """Rewrite relative links outside fenced code blocks."""
    lines = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence:
            line = INLINE_LINK.sub(
                lambda m: (
                    m["prefix"]
                    + resolve_link(m["target"], page, pages, root, m["prefix"].startswith("!"))
                    + m["suffix"]
                ),
                line,
            )
            line = REFERENCE_LINK.sub(
                lambda m: (
                    m["prefix"]
                    + resolve_link(m["target"], page, pages, root, image=False)
                    + m["suffix"]
                ),
                line,
            )
        lines.append(line)
    return "".join(lines)


def render_nav(pages: Iterable[Page]) -> str:
    """Write the literate-nav SUMMARY: policy pages first, then grouped sections."""
    pages = list(pages)
    lines = [f"* [{page.title}]({page.target})" for page in pages if page.source in ROOT_PAGES]
    sections = (
        ("Guides", [p for p in pages if p.source.startswith("docs/")]),
        ("Examples", [p for p in pages if p.source.startswith("examples/")]),
        ("Composite actions", [p for p in pages if p.source.startswith(".github/actions/")]),
    )
    for name, members in sections:
        lines.append(f"* {name}")
        lines += [
            f"    * [{page.title}]({page.target})"
            for page in sorted(members, key=lambda page: page.title.lower())
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Generate the site pages; mkdocs-gen-files provides the virtual file system."""
    import mkdocs_gen_files

    pages = discover_pages(ROOT)
    by_source = {page.source: page for page in pages}
    for page in pages:
        text = (ROOT / page.source).read_text(encoding="utf-8")
        with mkdocs_gen_files.open(page.target, "w", encoding="utf-8") as handle:
            handle.write(rewrite_links(text, page, by_source, ROOT))
        mkdocs_gen_files.set_edit_path(page.target, page.source)
    with mkdocs_gen_files.open("SUMMARY.md", "w", encoding="utf-8") as handle:
        handle.write(render_nav(pages))


if __name__ == "<run_path>":
    main()
