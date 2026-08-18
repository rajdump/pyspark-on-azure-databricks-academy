#!/usr/bin/env python3
"""Verify that .cursor/rules/*.mdc glob patterns match their intended files.

Uses stdlib fnmatch only. This checks pattern syntax against the workspace
filesystem; it does not prove Cursor's Agent attaches the rule. For that,
run the smoke test in cursor_ecosystem/FUTURE-TOPICS.md (Rule reliability).
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = REPO_ROOT / ".cursor" / "rules"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
GLOBS_ARRAY_RE = re.compile(r"^globs:\s*\[(.*)\]\s*$", re.MULTILINE)
GLOBS_STRING_RE = re.compile(r"^globs:\s*(.+?)\s*$", re.MULTILINE)

# rule stem -> paths that must match at least one glob on the rule
EXPECTED_MATCHES: dict[str, list[str]] = {
    "command-authoring": [
        ".cursor/commands/new-lesson.md",
        ".cursor/commands/write-lesson.md",
        ".cursor/commands/validate-notebook.md",
    ],
    "learner-notebooks": [
        "08 - Aggregations and Window Functions/06 - Running Totals and Lag and Lead.py",
    ],
    "course-authoring": [
        "README.md",
        "COURSE_MODULES.md",
    ],
}

# paths that must not match any glob on the rule
EXPECTED_NON_MATCHES: dict[str, list[str]] = {
    "command-authoring": [
        "README.md",
        "docs/standards/command-authoring.md",
        ".cursor/rules/command-authoring.mdc",
    ],
    "learner-notebooks": [
        ".cursor/commands/new-lesson.md",
        "README.md",
    ],
    "course-authoring": [
        ".cursor/commands/new-lesson.md",
        "docs/standards/command-authoring.md",
    ],
}


def parse_globs(frontmatter: str) -> list[str]:
    array_match = GLOBS_ARRAY_RE.search(frontmatter)
    if array_match:
        inner = array_match.group(1)
        return [part.strip().strip('"').strip("'") for part in inner.split(",") if part.strip()]
    string_match = GLOBS_STRING_RE.search(frontmatter)
    if string_match:
        raw = string_match.group(1).strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1]
            return [part.strip().strip('"').strip("'") for part in inner.split(",") if part.strip()]
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def collect_rule_files() -> dict[str, list[str]]:
    rules: dict[str, list[str]] = {}
    for rule_path in sorted(RULES_DIR.glob("*.mdc")):
        text = rule_path.read_text(encoding="utf-8")
        fm_match = FRONTMATTER_RE.match(text)
        if not fm_match:
            continue
        patterns = parse_globs(fm_match.group(1))
        if patterns:
            rules[rule_path.stem] = patterns
    return rules


def main() -> int:
    rules = collect_rule_files()
    failures: list[str] = []

    if "command-authoring" not in rules:
        failures.append("command-authoring.mdc: no globs found in frontmatter")
    else:
        patterns = rules["command-authoring"]
        print("command-authoring.mdc globs:", ", ".join(patterns))
        command_files = sorted(
            str(p.relative_to(REPO_ROOT))
            for p in (REPO_ROOT / ".cursor" / "commands").glob("*.md")
        )
        print(f"  .cursor/commands/*.md files on disk: {len(command_files)}")
        for path in command_files:
            if not matches_any(path, patterns):
                failures.append(f"command-authoring: expected match for {path!r}")

    for stem, patterns in rules.items():
        print(f"\n{stem}.mdc: {', '.join(patterns)}")
        for path in EXPECTED_MATCHES.get(stem, []):
            ok = matches_any(path, patterns)
            print(f"  match   {path}: {ok}")
            if not ok:
                failures.append(f"{stem}: expected match for {path!r}")
        for path in EXPECTED_NON_MATCHES.get(stem, []):
            ok = not matches_any(path, patterns)
            print(f"  reject  {path}: {ok}")
            if not ok:
                failures.append(f"{stem}: expected non-match for {path!r}")

    if failures:
        print("\nFAIL")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("\nPASS: all glob patterns match expected files (filesystem check only).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
