#!/usr/bin/env python3
"""Fail when a handbook's two language editions drift apart structurally.

Each handbook ships as an English edition and a Chinese edition that are
line-for-line twins: the same number of lines, and at every line number the
same *kind* of content — a heading of the same level, a table row, a list
item, a blockquote, a code fence delimiter, a blank, or prose. Code blocks are
byte-identical across the pair.

That invariant is what makes a translation reviewable: a reader who cannot
read one of the two languages can still see that nothing was dropped, added,
or moved. A restructure applied to one edition and not the other breaks it
silently, which no other check in this repository would notice.

Run from anywhere:

    python3 scripts/check_editions.py

Exit status is 0 when every pair is aligned, 1 otherwise.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

HANDBOOKS = [
    ("product-manual.md", "product-manual-zh.md"),
    ("soft-gripper-development-manual.md", "soft-gripper-development-manual-zh.md"),
]

HEADING = re.compile(r"^(#{1,6}) ")
TABLE_ROW = re.compile(r"^\|")
LIST_ITEM = re.compile(r"^ *([-*+]|\d+\.) ")
QUOTE = re.compile(r"^>")


def is_ascii(line):
    return line.isascii()


def strip_comment(line):
    """Drop a trailing ``#`` comment and trailing whitespace.

    Naive on purpose: a ``#`` inside a string literal would be treated as a
    comment. Neither handbook's examples contain one, and the failure mode is a
    missed difference, never a false alarm.
    """
    head, marker, _ = line.partition("#")
    return (head if marker else line).rstrip()


def kinds(path):
    """Return one kind label per line, plus the set of fenced code lines."""
    lines = path.read_text(encoding="utf-8").split("\n")
    result = []
    fence = False
    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("```"):
            result.append("fence")
            fence = not fence
            continue
        if fence:
            result.append("code")
        elif not stripped:
            result.append("blank")
        else:
            match = HEADING.match(stripped)
            if match:
                result.append(f"h{len(match.group(1))}")
            elif TABLE_ROW.match(stripped):
                result.append("table")
            elif LIST_ITEM.match(stripped):
                result.append("list")
            elif QUOTE.match(stripped):
                result.append("quote")
            else:
                result.append("text")
    return result, lines, fence


def check(english, chinese):
    en_path, zh_path = REPO / english, REPO / chinese
    en_kinds, en_lines, en_open = kinds(en_path)
    zh_kinds, zh_lines, zh_open = kinds(zh_path)
    problems = []

    if en_open or zh_open:
        problems.append(f"{english} / {chinese}: unbalanced code fence")

    if len(en_lines) != len(zh_lines):
        problems.append(
            f"{english} has {len(en_lines)} lines, {chinese} has {len(zh_lines)}"
        )

    shared = min(len(en_kinds), len(zh_kinds))
    mismatches = [
        index
        for index in range(shared)
        if en_kinds[index] != zh_kinds[index]
    ]
    if mismatches:
        shown = mismatches[:10]
        detail = ", ".join(
            f"line {index + 1}: {en_kinds[index]} vs {zh_kinds[index]}"
            for index in shown
        )
        more = "" if len(mismatches) <= len(shown) else f" (+{len(mismatches) - len(shown)} more)"
        problems.append(f"{english} / {chinese}: line kinds differ at {detail}{more}")

    headings_en = [k for k in en_kinds if k.startswith("h")]
    headings_zh = [k for k in zh_kinds if k.startswith("h")]
    if headings_en != headings_zh:
        problems.append(
            f"{english} / {chinese}: heading levels differ "
            f"({len(headings_en)} vs {len(headings_zh)} headings)"
        )

    # Inside a code block, statements must match but two things legitimately do
    # not: the trailing comment, which is prose and is translated, and any line
    # carrying translated text or illustrative pseudo-code, such as the byte
    # diagrams in the product manual. So compare only the code lines that are
    # pure ASCII in *both* editions, after dropping the comment. That is the
    # subset where a silent edit on one side is a real defect, and it keeps the
    # check free of the false alarms that a byte comparison would raise.
    en_code = [strip_comment(l) for k, l in zip(en_kinds, en_lines) if k == "code"]
    zh_code = [strip_comment(l) for k, l in zip(zh_kinds, zh_lines) if k == "code"]
    for index, (en_line, zh_line) in enumerate(zip(en_code, zh_code)):
        if is_ascii(en_line) and is_ascii(zh_line) and en_line != zh_line:
            problems.append(
                f"{english} / {chinese}: code differs at code line {index + 1} "
                f"({en_line!r} vs {zh_line!r})"
            )

    return len(headings_en), problems


def main():
    problems = []
    for english, chinese in HANDBOOKS:
        count, found = check(english, chinese)
        problems += found
        print(f"{english} / {chinese}: {count} headings, kinds aligned"
              if not found else f"{english} / {chinese}: {len(found)} problem(s)")

    if problems:
        print()
        for problem in problems:
            print(f"error: {problem}")
        return 1
    print("\nboth editions of every handbook are aligned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
