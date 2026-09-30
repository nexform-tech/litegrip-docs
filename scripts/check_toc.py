#!/usr/bin/env python3
"""Fail when a handbook table of contents no longer matches its headings.

Every handbook opens with a contents section — `## Contents` in the English
editions, `## 目录` in the Chinese ones — that links to each top-level and
second-level heading. Renaming a heading without updating that list breaks the
links silently, which no other check in this repository would notice.

The same holds for the cross-references in the prose: a `](#section)` link
inside one handbook, and a `](other-handbook.md#section)` link that jumps from
the product manual into the development manual. Both are checked here.

The anchor slugs use GitHub's algorithm. It was verified entry by entry against
`github-slugger`, the package GitHub itself uses, across every heading of the
four handbooks, so this script and a rendered GitHub page agree on every link.

Run from anywhere:

    python3 scripts/check_toc.py

Exit status is 0 when every handbook passes, 1 otherwise.
"""

import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Each entry pairs the English edition with its Chinese edition. Both are
# checked, and both must carry the same number of contents entries.
HANDBOOKS = [
    ("product-manual.md", "product-manual-zh.md"),
    ("soft-gripper-development-manual.md", "soft-gripper-development-manual-zh.md"),
]

CONTENTS_TITLES = {"contents", "目录"}
LINK = re.compile(r"^( *)- \[([^\]]+)\]\(#([^)]+)\)$")
INDENT = "  "


def slugify(text, seen):
    """Return the GitHub anchor for a heading, disambiguating repeats."""
    # Keep word characters, the CJK block (U+4E00-U+9FFF), spaces and hyphens;
    # drop everything else. Verified against github-slugger.
    slug = re.sub(r"[^\w一-鿿 \-]", "", text.strip().lower()).replace(" ", "-")
    seen[slug] += 1
    return slug if seen[slug] == 1 else f"{slug}-{seen[slug] - 1}"


def scan(lines):
    """Yield (line index, level, text, slug) for headings outside code fences."""
    fence = False
    seen = collections.Counter()
    for index, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        match = re.match(r"^(#{1,6}) (.+)$", stripped)
        if match:
            text = match.group(2).strip()
            yield index, len(match.group(1)), text, slugify(text, seen)


ANCHOR_CACHE = {}


def anchors_of(name):
    """The set of heading anchors in *name*, read once per run."""
    if name not in ANCHOR_CACHE:
        lines = (REPO / name).read_text(encoding="utf-8").split("\n")
        ANCHOR_CACHE[name] = {slug for _, _, _, slug in scan(lines)}
    return ANCHOR_CACHE[name]


def check(name):
    """Return (contents entry count, list of problems) for one handbook."""
    lines = (REPO / name).read_text(encoding="utf-8").split("\n")
    headings = list(scan(lines))
    problems = []

    contents = [h for h in headings if h[2].lower() in CONTENTS_TITLES]
    if len(contents) != 1:
        return 0, [f"{name}: expected exactly one contents heading, found {len(contents)}"]

    contents_at = contents[0][0]
    following = [h for h in headings if h[0] > contents_at]
    ends_at = following[0][0] if following else len(lines)

    links = []
    for line in lines[contents_at:ends_at]:
        match = LINK.match(line)
        if match:
            links.append((len(match.group(1)), match.group(2), match.group(3)))

    anchors = {slug: text for _, _, text, slug in headings}

    for _, text, slug in links:
        if slug not in anchors:
            problems.append(f"{name}: contents links to #{slug}, which is not a heading")
        elif anchors[slug] != text:
            problems.append(
                f"{name}: contents entry {text!r} points at #{slug}, "
                f"whose heading reads {anchors[slug]!r}"
            )

    # Cross-references in the prose break exactly the way contents entries do,
    # and nothing else in this repository checks them. The contents block is
    # skipped here because the loop above already reports its problems.
    fence = False
    for index, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.startswith("```"):
            fence = not fence
            continue
        if fence or contents_at <= index < ends_at:
            continue
        for text, slug in re.findall(r"\[([^\]]+)\]\(#([^)]+)\)", stripped):
            if slug not in anchors:
                problems.append(
                    f"{name}:{index + 1}: the link {text!r} points at #{slug}, "
                    f"which is not a heading"
                )
        # A jump into another handbook of this repository. The heading it names
        # lives in that file, so the check above cannot see it.
        for text, target, slug in re.findall(
            r"\[([^\]]+)\]\(([^)#\s]+\.md)#([^)]+)\)", stripped
        ):
            if not (REPO / target).exists():
                problems.append(
                    f"{name}:{index + 1}: the link {text!r} points at {target}, "
                    f"which is not a file in this repository"
                )
            elif slug not in anchors_of(target):
                problems.append(
                    f"{name}:{index + 1}: the link {text!r} points at "
                    f"{target}#{slug}, which is not a heading there"
                )

    # Every top-level heading except the document title, and every second-level
    # heading except the contents heading itself, must appear in the list. An
    # entry is nested once its heading sits inside a top-level section; the
    # headings that precede the first section sit at the top level.
    expected = []
    in_section = False
    for position, (_, level, text, slug) in enumerate(headings):
        if level == 1 and position > 0:
            in_section = True
            expected.append((0, slug))
        elif level == 2 and text.lower() not in CONTENTS_TITLES:
            expected.append((1 if in_section else 0, slug))

    expected_slugs = [slug for _, slug in expected]
    wanted = {slug: depth for depth, slug in expected}
    listed = [slug for _, _, slug in links]

    for slug in expected_slugs:
        if slug not in listed:
            problems.append(f"{name}: heading #{slug} is missing from the contents")
    for slug in listed:
        if slug not in wanted:
            problems.append(
                f"{name}: contents lists #{slug}, which is not a first- or second-level heading"
            )

    if listed != expected_slugs:
        problems.append(f"{name}: contents entries are out of document order")
    else:
        for indent, _, slug in links:
            if indent != len(INDENT) * wanted[slug]:
                problems.append(
                    f"{name}: entry #{slug} is indented by {indent} spaces, "
                    f"expected {len(INDENT) * wanted[slug]}"
                )

    return len(links), problems


def main():
    problems = []
    counts = {}
    for english, chinese in HANDBOOKS:
        for name in (english, chinese):
            counts[name], found = check(name)
            problems += found
        if counts[english] != counts[chinese]:
            problems.append(
                f"{english} and {chinese} list {counts[english]} and "
                f"{counts[chinese]} contents entries; the editions must match"
            )

    for name, count in counts.items():
        print(f"{name}: {count} contents entries")
    if problems:
        print()
        for problem in problems:
            print(f"error: {problem}")
        return 1
    print("\nall handbook contents lists resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
