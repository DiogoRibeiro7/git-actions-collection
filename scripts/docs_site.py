"""Assemble the documentation site from Markdown spread across the repository.

MkDocs only reads `docs/`, but the repository keeps its policy files at the root
and usage guides beside examples and composite actions. The mkdocs-gen-files
plugin runs this module on every build: it publishes those files as site pages,
generates a reference page for each public workflow and a catalogue of public
components, rewrites relative links to the published pages (or to GitHub for
files outside the site), and writes the navigation read by mkdocs-literate-nav.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import posixpath
import re
import sys

REPOSITORY = "https://github.com/DiogoRibeiro7/git-actions-collection"
RAW = "https://raw.githubusercontent.com/DiogoRibeiro7/git-actions-collection/main"
ROOT = Path(__file__).resolve().parents[1]

# `mkdocs build` does not put the repository on sys.path when it runs this file.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import workflow_docs  # noqa: E402

# The catalogue is generated from the support matrix, so links to it land there.
CATALOGUE = ".github/support-matrix.yml"

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
    """A repository file published at a site path."""

    source: str
    target: str
    title: str
    tier: str = ""  # support tier of a generated workflow page


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
    pages.append(Page(CATALOGUE, "catalogue.md", "Catalogue"))
    pages += [
        Page(
            f"{workflow_docs.WORKFLOWS.as_posix()}/{component.name}",
            f"workflows/{component.name.rsplit('.', 1)[0]}.md",
            component.title,
            component.tier,
        )
        for component in workflow_docs.public_components(root)
        if component.kind == "workflow"
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
    """Write the literate-nav SUMMARY: policy pages and the catalogue, then sections."""
    pages = list(pages)
    lines = [f"* [{page.title}]({page.target})" for page in pages if page.source in ROOT_PAGES]
    lines[1:1] = [f"* [{page.title}]({page.target})" for page in pages if page.source == CATALOGUE]

    def listed(members: Iterable[Page], indent: str) -> list[str]:
        ordered = sorted(members, key=lambda page: page.title.lower())
        return [f"{indent}* [{page.title}]({page.target})" for page in ordered]

    lines.append("* Reusable workflows")
    for tier in workflow_docs.TIERS:
        members = [page for page in pages if page.tier == tier]
        if members:
            lines.append(f"    * {tier.capitalize()}")
            lines += listed(members, "        ")
    sections = (
        ("Composite actions", [p for p in pages if p.source.startswith(".github/actions/")]),
        ("Guides", [p for p in pages if p.source.startswith("docs/")]),
        ("Examples", [p for p in pages if p.source.startswith("examples/")]),
    )
    for name, members in sections:
        lines.append(f"* {name}")
        lines += listed(members, "    ")
    return "\n".join(lines) + "\n"


def page_markdown(
    page: Page,
    pages: Sequence[Page],
    root: Path,
    components: Mapping[str, workflow_docs.Component],
) -> str:
    """Return a page's Markdown with links rewritten for the site."""
    by_source = {candidate.source: candidate for candidate in pages}
    # Generated pages write links relative to the repository root.
    generated = Page("index", page.target, page.title)
    definitions = workflow_docs.support_matrix(root).get("definitions") or {}
    if page.source == CATALOGUE:
        text = workflow_docs.render_catalogue(
            components.values(),
            definitions,
            lambda c: (
                f"{workflow_docs.WORKFLOWS.as_posix()}/{c.name}"
                if c.kind == "workflow"
                else f"{workflow_docs.ACTIONS.as_posix()}/{c.name}/README.md"
            ),
        )
        return rewrite_links(text, generated, by_source, root)
    if page.tier:
        component = components[posixpath.basename(page.source)]
        related = [
            (candidate.title, candidate.source)
            for candidate in pages
            if candidate.source.startswith(("docs/", "examples/"))
            and component.name in (root / candidate.source).read_text(encoding="utf-8")
        ]
        text = workflow_docs.render_workflow_page(root, component, definitions, related)
        return rewrite_links(text, generated, by_source, root)
    text = (root / page.source).read_text(encoding="utf-8")
    return rewrite_links(text, page, by_source, root)


def main() -> None:
    """Generate the site pages; mkdocs-gen-files provides the virtual file system."""
    import mkdocs_gen_files

    pages = discover_pages(ROOT)
    components = {component.name: component for component in workflow_docs.public_components(ROOT)}
    for page in pages:
        with mkdocs_gen_files.open(page.target, "w", encoding="utf-8") as handle:
            handle.write(page_markdown(page, pages, ROOT, components))
        mkdocs_gen_files.set_edit_path(page.target, page.source)
    with mkdocs_gen_files.open("SUMMARY.md", "w", encoding="utf-8") as handle:
        handle.write(render_nav(pages))


if __name__ == "<run_path>":
    main()
