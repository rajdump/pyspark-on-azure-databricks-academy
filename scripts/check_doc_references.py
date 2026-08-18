#!/usr/bin/env python3
"""Verify that the explicit references inside Cursor commands, rules, and AGENTS.md resolve.

Two kinds of reference are checked, and nothing else:

1. File paths written as `path` or @path.
2. Section references written as [[Section name]].

A section reference resolves only against the documents the same file already
names, so a reference cannot quietly point at a section living somewhere the
file never tells the reader to read. Ordinary **bold** text is emphasis and is
never treated as a reference.

Reference forms:

    [[Section name]]             resolved against this file's named documents
    [[readme-authoring#Name]]    qualified, when a bare name would be ambiguous
    [[#Section name]]            a heading in this same file
    [[file#Name|display text]]   alias form, as used in vault/

Usage: uv run python scripts/check_doc_references.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files whose references are checked. Adding "docs/standards/*.md" here widens
# the pass; nothing below assumes a source lives under .cursor/.
SOURCE_GLOBS: tuple[str, ...] = (
    ".cursor/commands/*.md",
    ".cursor/rules/*.mdc",
    "docs/standards/*.md",
    "AGENTS.md",
)

# Documents a reference may resolve into.
TARGET_GLOBS: tuple[str, ...] = ("docs/standards/*.md", "docs/data/*.md")
TARGET_FILES: tuple[str, ...] = ("AGENTS.md", "COURSE_MODULES.md", "README.md")

# .mdc must precede .md so the longer extension wins. The optional leading dot
# keeps dot-directories such as .cursor/ visible.
PATH_RE = re.compile(r"[`@](\.?[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:mdc|md|py|toml))`?")
REF_RE = re.compile(r"\[\[([^\]]+?)\]\]")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


class Index(NamedTuple):
    """Anchors available in each target document, keyed by repo-relative path."""

    headings: dict[str, set[str]]
    bold: dict[str, set[str]]
    byname: dict[str, str]


def normalize(label: str) -> str:
    """Reduce a heading, bold label, or reference to a comparable key."""
    text = label.replace("`", "").replace("*", "")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().strip(".:;,—-").strip().lower()


def flatten(text: str) -> str:
    """Join wrapped lines so a reference split across lines is still one token."""
    return re.sub(r"\s+", " ", text)


def strip_fences(text: str) -> str:
    """Blank out fenced code blocks, preserving line numbering.

    Databricks examples contain lines such as `# COMMAND ----------`, which a
    line-oriented heading regex would otherwise index as real headings.
    """
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def heading_names(body: str) -> set[str]:
    """Normalized headings in already-defenced text."""
    return {normalize(m) for m in HEADING_RE.findall(body)} - {""}


def bold_names(body: str) -> set[str]:
    """Normalized bold labels in already-defenced text."""
    return {normalize(m) for m in BOLD_RE.findall(flatten(body))} - {""}


def find_line(lines: list[str], *candidates: str) -> int:
    """Best-effort line number: try each candidate, then the last one's first word."""
    tokens = [c for c in candidates if c]
    for token in tokens:
        for number, line in enumerate(lines, start=1):
            if token in line:
                return number
    if tokens:
        first_word = tokens[-1].split(" ", 1)[0].strip("`*[]")
        if first_word:
            for number, line in enumerate(lines, start=1):
                if first_word in line:
                    return number
    return 0


def resolve_reference(
    raw: str,
    declared: set[str],
    own_headings: set[str],
    index: Index,
) -> tuple[str, bool]:
    """Resolve one [[...]] reference.

    Returns an empty reason on success, plus whether it resolved via a bold
    label rather than a heading.
    """
    ref = raw.split("|", 1)[0].strip()
    file_part: str | None = None
    section = ref
    if "#" in ref:
        head, _, tail = ref.partition("#")
        file_part = head.strip()
        section = tail.strip()

    key = normalize(section)
    if not key:
        return f"[[{raw}]] has an empty section name", False

    if file_part == "":
        if key in own_headings:
            return "", False
        return f"[[{raw}]] names no heading in this file", False

    if file_part:
        target = index.byname.get(file_part) or index.byname.get(file_part.lower())
        if target is None:
            return f"[[{raw}]] names an unknown document {file_part!r}", False
        if key in index.headings.get(target, set()):
            return "", False
        if key in index.bold.get(target, set()):
            return "", True
        return f"[[{raw}]] has no section {section!r} in {target}", False

    # Global heading precedence: a name that is a heading anywhere must resolve
    # to that heading, in a document this file names. Bold labels are a
    # fallback only for names that are headings nowhere.
    heading_owners = sorted(f for f, names in index.headings.items() if key in names)
    if heading_owners:
        matches = sorted(f for f in heading_owners if f in declared)
        if len(matches) == 1:
            return "", False
        if not matches:
            owners = ", ".join(heading_owners)
            return f"[[{raw}]] is a heading in {owners}, which this file does not name", False
        return f"[[{raw}]] matches headings in {', '.join(matches)}; qualify it", False

    bold_owners = sorted(f for f, names in index.bold.items() if key in names and f in declared)
    if len(bold_owners) == 1:
        return "", True
    if not bold_owners:
        return f"[[{raw}]] matches no section in the documents this file names", False
    return f"[[{raw}]] matches labels in {', '.join(bold_owners)}; qualify it", False


def check_source(
    name: str,
    text: str,
    index: Index,
    known_paths: set[str],
) -> tuple[list[str], list[str]]:
    """Return failures and informational notes for one source document."""
    failures: list[str] = []
    notes: list[str] = []
    lines = text.splitlines()
    body = strip_fences(text)
    flat = flatten(body)
    own_headings = heading_names(body)

    written_paths = set(PATH_RE.findall(body))
    for raw_path in sorted(written_paths):
        if raw_path not in known_paths:
            failures.append(f"{name}:{find_line(lines, raw_path)}: missing path `{raw_path}`")

    # A file may only reference sections of documents it already names, and
    # never its own bold labels.
    declared = {index.byname[p] for p in written_paths if p in index.byname} - {name}

    for raw in sorted(set(REF_RE.findall(flat))):
        reason, via_bold = resolve_reference(raw, declared, own_headings, index)
        line = find_line(lines, f"[[{raw}", raw)
        if reason:
            failures.append(f"{name}:{line}: {reason}")
        elif via_bold:
            notes.append(f"{name}:{line}: [[{raw}]] resolved to a bold label, not a heading")

    return failures, notes


def repo_paths(root: Path) -> set[str]:
    """Every tracked-looking file path, relative to the repository root."""
    paths: set[str] = set()
    for path in root.rglob("*"):
        if path.is_file() and ".git/" not in str(path) and ".venv" not in str(path):
            paths.add(str(path.relative_to(root)))
            paths.add(path.name)
    return paths


def index_targets(root: Path) -> Index:
    """Index every anchor a reference is allowed to resolve to."""
    headings: dict[str, set[str]] = {}
    bold: dict[str, set[str]] = {}
    byname: dict[str, str] = {}

    targets: list[Path] = []
    for pattern in TARGET_GLOBS:
        targets.extend(sorted(root.glob(pattern)))
    for rel in TARGET_FILES:
        path = root / rel
        if path.is_file():
            targets.append(path)

    for path in targets:
        rel = str(path.relative_to(root))
        body = strip_fences(path.read_text())
        headings[rel] = heading_names(body)
        bold[rel] = bold_names(body)
        for alias in (rel, path.name, path.stem):
            byname[alias] = rel
            byname[alias.lower()] = rel

    return Index(headings, bold, byname)


def check_repo(root: Path) -> tuple[list[str], list[str], int]:
    """Check every source document. Returns failures, notes, and files checked."""
    index = index_targets(root)
    known_paths = repo_paths(root)

    sources: list[Path] = []
    for pattern in SOURCE_GLOBS:
        sources.extend(sorted(root.glob(pattern)))

    failures: list[str] = []
    notes: list[str] = []
    for path in sources:
        rel = str(path.relative_to(root))
        text = path.read_text()
        file_failures, file_notes = check_source(rel, text, index, known_paths)
        failures.extend(file_failures)
        notes.extend(file_notes)

    return sorted(failures), sorted(notes), len(sources)


def _fixture_index() -> Index:
    """A small hand-built index so the rules can be tested without the repo."""
    headings = {
        "docs/a.md": {"alpha section", "shared name"},
        "docs/b.md": {"beta section", "notebooks table"},
        "docs/c.md": {"shared name"},
    }
    bold = {
        "docs/a.md": {"notebooks table", "loose label"},
        "docs/b.md": {"loose label"},
        "docs/c.md": {"bold only label"},
    }
    byname: dict[str, str] = {}
    for rel in headings:
        name = rel.split("/")[-1]
        for alias in (rel, name, name.removesuffix(".md")):
            byname[alias] = rel
            byname[alias.lower()] = rel
    return Index(headings, bold, byname)


def self_test() -> list[str]:
    """Guard every rule the checker depends on."""
    problems: list[str] = []
    index = _fixture_index()
    paths = {"docs/a.md", "docs/b.md", "docs/c.md", ".cursor/rules/x.mdc"}

    def check(text: str) -> tuple[list[str], list[str]]:
        return check_source("fixture", text, index, paths)

    for raw, want in {
        "Voice consistency (reviewer judgment):": "voice consistency",
        "Dataset setup:": "dataset setup",
        "`Focus` entry": "focus entry",
        "**Author-only writes**": "author-only writes",
        "Module 5 setup or cleanup:": "module 5 setup or cleanup",
    }.items():
        got = normalize(raw)
        if got != want:
            problems.append(f"normalize({raw!r}) == {got!r}, want {want!r}")

    if PATH_RE.findall("see `notebook-command-output.mdc` now") != ["notebook-command-output.mdc"]:
        problems.append(".mdc path must match in full, not as .md")

    if PATH_RE.findall("read @.cursor/rules/x.mdc") != [".cursor/rules/x.mdc"]:
        problems.append("a dot-prefixed path must be matched")

    if REF_RE.findall(flatten("read [[Full-lesson\nmanifest]] now")) != ["Full-lesson manifest"]:
        problems.append("a reference wrapped across lines must be found")

    fenced = heading_names(strip_fences("```python\n# COMMAND ------\n```\n\n## Real heading\n"))
    if fenced != {"real heading"}:
        problems.append(f"a heading inside a fence must not be an anchor, got {fenced}")

    ok, notes = check("Read `docs/a.md` and apply [[Alpha section]].\n")
    if ok or notes:
        problems.append(f"a declared heading reference must pass cleanly, got {ok} {notes}")

    bad, _ = check("Read `docs/a.md` and apply [[No such section]].\n")
    if len(bad) != 1 or "matches no section" not in bad[0]:
        problems.append(f"an unresolvable reference must fail, got {bad}")

    emphasis, _ = check("Read `docs/a.md`. This is **Alpha section** as emphasis.\n")
    if emphasis:
        problems.append(f"ordinary bold must be ignored, got {emphasis}")

    undeclared, _ = check("Read `docs/a.md` and apply [[Beta section]].\n")
    if len(undeclared) != 1 or "does not name" not in undeclared[0]:
        problems.append(f"a reference to an unnamed document must fail, got {undeclared}")

    # Global heading precedence: "notebooks table" is bold in docs/a.md but a
    # heading in docs/b.md, so declaring only docs/a.md must not satisfy it.
    masked, _ = check("Read `docs/a.md` and apply [[Notebooks table]].\n")
    if len(masked) != 1 or "does not name" not in masked[0]:
        problems.append(f"a bold label must not mask an undeclared heading, got {masked}")

    ambiguous_bold, _ = check("Read `docs/a.md` and `docs/b.md`, then [[Loose label]].\n")
    if len(ambiguous_bold) != 1 or "qualify it" not in ambiguous_bold[0]:
        problems.append(f"a label in two named documents must fail, got {ambiguous_bold}")

    ambiguous_head, _ = check("Read `docs/a.md` and `docs/c.md`, then [[Shared name]].\n")
    if len(ambiguous_head) != 1 or "qualify it" not in ambiguous_head[0]:
        problems.append(f"a heading in two named documents must fail, got {ambiguous_head}")

    qualified, _ = check("Apply [[b#Beta section]].\n")
    if qualified:
        problems.append(f"the qualified form must resolve without a named path, got {qualified}")

    alias, _ = check("Apply [[b#Beta section|the beta bit]].\n")
    if alias:
        problems.append(f"the alias form must resolve, got {alias}")

    unknown_doc, _ = check("Apply [[nope#Beta section]].\n")
    if len(unknown_doc) != 1 or "unknown document" not in unknown_doc[0]:
        problems.append(f"an unknown qualified document must fail, got {unknown_doc}")

    same_file, _ = check("## Own heading\n\nSee [[#Own heading]].\n")
    if same_file:
        problems.append(f"a same-file reference must resolve, got {same_file}")

    same_file_bad, _ = check("## Own heading\n\nSee [[#Missing]].\n")
    if len(same_file_bad) != 1 or "no heading in this file" not in same_file_bad[0]:
        problems.append(f"a broken same-file reference must fail, got {same_file_bad}")

    # A source's own bold label must never anchor its own reference.
    self_anchor, _ = check("**Some label** and then [[Some label]].\n")
    if len(self_anchor) != 1:
        problems.append(f"a source label must not anchor itself, got {self_anchor}")

    fallback, fallback_notes = check("Read `docs/c.md` and apply [[Bold only label]].\n")
    if fallback or len(fallback_notes) != 1:
        problems.append(f"a bold fallback must pass with a note, got {fallback} {fallback_notes}")

    missing_path, _ = check("read @docs/gone.md\n")
    if len(missing_path) != 1 or "missing path" not in missing_path[0]:
        problems.append(f"a missing path must fail, got {missing_path}")

    dot_path, _ = check("Response format: @.cursor/rules/x.mdc\n")
    if dot_path:
        problems.append(f"a known dot-prefixed path must pass, got {dot_path}")

    located, _ = check("Read `docs/a.md`.\n\nLine two.\n\n[[No such section]]\n")
    if not located or not located[0].startswith("fixture:5:"):
        problems.append(f"a failure must cite the right line, got {located}")

    return [f"self-test: {p}" for p in problems]


def main() -> int:
    problems = self_test()
    if problems:
        print("\n".join(problems))
        print("FAIL: checker self-test failed")
        return 2

    failures, notes, checked = check_repo(REPO_ROOT)
    for note in notes:
        print(f"note: {note}")
    if failures:
        print("\n".join(failures))
        print(f"FAIL: {len(failures)} reference problem(s) in {checked} file(s)")
        return 1

    print(f"OK: {checked} files checked, {len(notes)} bold-label note(s), 0 unresolved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
