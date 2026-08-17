#!/usr/bin/env python3
"""Verify that pointers written inside Cursor commands and rules still resolve.

Two kinds of explicit reference are checked, and nothing else:

1. File paths written as `path` or @path.
2. Named section pointers written as **Bold text**, which must match a heading
   or a bold label in one of the target documents.

A bold string that is local emphasis rather than a pointer must be listed in
DECLARED_EMPHASIS. That list is deliberately literal: the checker never guesses
which strings are emphasis, so a new unresolved pointer always fails.

Usage: uv run python scripts/check_doc_references.py
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files whose pointers are checked.
SOURCE_GLOBS = (".cursor/commands/*.md", ".cursor/rules/*.mdc")

# Files a pointer may resolve into. Sources are deliberately excluded so a
# pointer can never resolve against a bold label in its own file.
TARGET_GLOBS = ("docs/standards/*.md", "docs/data/*.md")
TARGET_FILES = ("AGENTS.md", "COURSE_MODULES.md", "README.md")

# Bold strings that are emphasis or step labels, not pointers.
DECLARED_EMPHASIS = frozenset(
    {
        "after a clean pass",
        "course_modules.md",
        "do not write the full lesson",
        "existing readme",
        "folder name",
        "issues only",
        "missing design",
        "numbered module readme.md",
        "read-only",
        "roadmap row",
        "root readme.md",
        "scaffold only",
        "target",
        "user-facing reply minimal",
        "workflow note",
        "write",
    }
)

# .mdc must precede .md so the longer extension wins.
PATH_RE = re.compile(r"[`@]([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:mdc|md|py|toml))`?")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)


def normalize(label: str) -> str:
    """Reduce a heading, bold label, or pointer to a comparable key."""
    text = label.replace("`", "").replace("*", "")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().strip(".:;,—-").strip().lower()


def flatten(text: str) -> str:
    """Join wrapped lines so a pointer split across lines is still one token."""
    return re.sub(r"\s+", " ", text)


def collect_headings(text: str) -> set[str]:
    """Headings only, used so a document may point at its own section."""
    anchors = {normalize(m) for m in HEADING_RE.findall(text)}
    anchors.discard("")
    return anchors


def collect_anchors(texts: Iterable[str]) -> set[str]:
    """Every heading and bold label a pointer is allowed to resolve to."""
    anchors: set[str] = set()
    for text in texts:
        flat = flatten(text)
        anchors.update(normalize(m) for m in HEADING_RE.findall(text))
        anchors.update(normalize(m) for m in BOLD_RE.findall(flat))
    anchors.discard("")
    return anchors


def find_line(lines: list[str], token: str) -> int:
    """Best-effort line number for a token, using its first word."""
    first_word = token.split(" ", 1)[0].strip("`*")
    for index, line in enumerate(lines, start=1):
        if first_word and first_word in line:
            return index
    return 0


def check_text(
    name: str, text: str, anchors: set[str], known_paths: set[str]
) -> tuple[list[str], set[str]]:
    """Return failures for one source document and the emphasis keys it used."""
    failures: list[str] = []
    skipped: set[str] = set()
    lines = text.splitlines()
    flat = flatten(text)

    for raw_path in sorted(set(PATH_RE.findall(text))):
        if raw_path not in known_paths:
            failures.append(f"{name}:{find_line(lines, raw_path)}: missing path `{raw_path}`")

    for raw_bold in sorted(set(BOLD_RE.findall(flat))):
        key = normalize(raw_bold)
        if not key or key in anchors:
            continue
        if key in DECLARED_EMPHASIS:
            skipped.add(key)
            continue
        failures.append(f"{name}:{find_line(lines, raw_bold)}: unresolved pointer **{raw_bold}**")

    return failures, skipped


def repo_paths(root: Path) -> set[str]:
    """Every tracked-looking file path, relative to the repository root."""
    paths: set[str] = set()
    for path in root.rglob("*"):
        if path.is_file() and ".git/" not in str(path) and ".venv" not in str(path):
            paths.add(str(path.relative_to(root)))
            paths.add(path.name)
    return paths


def check_repo(root: Path) -> tuple[list[str], int, set[str]]:
    """Check every source document. Returns failures, files checked, emphasis keys used."""
    target_texts: list[str] = []
    for glob in TARGET_GLOBS:
        target_texts.extend(p.read_text() for p in sorted(root.glob(glob)))
    for rel in TARGET_FILES:
        target = root / rel
        if target.is_file():
            target_texts.append(target.read_text())

    anchors = collect_anchors(target_texts)
    known_paths = repo_paths(root)

    failures: list[str] = []
    checked = 0
    skipped: set[str] = set()
    sources = [p for glob in SOURCE_GLOBS for p in sorted(root.glob(glob))]
    for source in sources:
        text = source.read_text()
        file_failures, file_skipped = check_text(
            str(source.relative_to(root)),
            text,
            anchors | collect_headings(text),
            known_paths,
        )
        failures.extend(file_failures)
        checked += 1
        skipped |= file_skipped

    # A declared-emphasis entry that no longer appears must be pruned, so the
    # list can never quietly grow into a mask for real pointers.
    for stale in sorted(DECLARED_EMPHASIS - skipped):
        failures.append(f"DECLARED_EMPHASIS: stale entry {stale!r}; remove it from the list")

    return sorted(failures), checked, skipped


def self_test() -> list[str]:
    """Guard the normalization and detection rules the checker depends on."""
    problems: list[str] = []

    cases = {
        "Voice consistency (reviewer judgment):": "voice consistency",
        "Dataset setup:": "dataset setup",
        "`Focus` entry": "focus entry",
        "**Author-only writes**": "author-only writes",
        "Module 5 setup or cleanup:": "module 5 setup or cleanup",
    }
    for raw, want in cases.items():
        got = normalize(raw)
        if got != want:
            problems.append(f"self-test: normalize({raw!r}) == {got!r}, want {want!r}")

    if PATH_RE.findall("see `notebook-command-output.mdc` now") != ["notebook-command-output.mdc"]:
        problems.append("self-test: .mdc path must match in full, not as .md")

    if BOLD_RE.findall(flatten("read the **Full-lesson\nmanifest** now")) != [
        "Full-lesson manifest"
    ]:
        problems.append("self-test: a pointer wrapped across lines must be found")

    anchors = collect_anchors(["## Author-only writes\n\n**Dataset setup:** text\n"])
    fixture_ok, _ = check_text(
        "fixture", "See **Author-only writes** and **Dataset setup**.\n", anchors, set()
    )
    if fixture_ok:
        problems.append(f"self-test: resolvable fixture must pass, got {fixture_ok}")

    fixture_bad, _ = check_text("fixture", "See **No Such Section**.\n", anchors, set())
    if len(fixture_bad) != 1 or "No Such Section" not in fixture_bad[0]:
        problems.append(f"self-test: unresolved fixture must fail, got {fixture_bad}")

    fixture_path, _ = check_text("fixture", "read @docs/gone.md\n", anchors, set())
    if len(fixture_path) != 1 or "missing path" not in fixture_path[0]:
        problems.append(f"self-test: missing path must fail, got {fixture_path}")

    # A bold label in the source must not resolve against itself.
    fixture_self, _ = check_text(
        "fixture", "**Some Label** and **Some Label** again\n", set(), set()
    )
    if len(fixture_self) != 1:
        problems.append(f"self-test: a source label must not anchor itself, got {fixture_self}")

    return problems


def main() -> int:
    problems = self_test()
    if problems:
        print("\n".join(problems))
        print("FAIL: checker self-test failed")
        return 2

    failures, checked, skipped = check_repo(REPO_ROOT)
    if failures:
        print("\n".join(failures))
        print(f"FAIL: {len(failures)} reference problem(s) in {checked} file(s)")
        return 1

    print(f"OK: {checked} files checked, {len(skipped)} declared emphasis skipped, 0 unresolved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
