#!/usr/bin/env python3
"""Initialize a clean Manus skill directory.

Usage:
    init_skill.py <skill-name> [--base-path PATH] [--with references,scripts,templates]

The initializer creates only the requested resource directories and never inserts
placeholder scripts or template files that could be shipped accidentally.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_BASE_PATH = Path("/home/ubuntu/skills")
VALID_RESOURCE_DIRS = {"references", "scripts", "templates"}

SKILL_TEMPLATE = """---
name: {skill_name}
description: "TODO: State what this skill does and the concrete requests that should trigger it."
---

# {skill_title}

## Goal

Describe the reusable outcome this skill enables.

## When to use

State the positive trigger conditions and at least one adjacent request that should use another skill instead.

## Workflow

1. Gather only the inputs required to begin safely.
2. Apply the domain-specific process.
3. Verify the outcome and state the safe next action if verification fails.

## Resources

Add only the references, scripts, or templates that are repeatedly needed. Remove this section if no bundled resource is required.
"""


def title_case(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split("-"))


def validate_name(name: str) -> str | None:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        return "Skill name must use lowercase hyphen-case"
    if len(name) > 64:
        return "Skill name must not exceed 64 characters"
    return None


def parse_resources(raw: str) -> set[str]:
    if not raw.strip():
        return set()
    values = {value.strip() for value in raw.split(",") if value.strip()}
    invalid = values - VALID_RESOURCE_DIRS
    if invalid:
        raise ValueError("Unsupported resource directories: " + ", ".join(sorted(invalid)))
    return values


def init_skill(skill_name: str, base_path: Path, resources: set[str]) -> Path:
    name_error = validate_name(skill_name)
    if name_error:
        raise ValueError(name_error)
    skill_dir = base_path / skill_name
    if skill_dir.exists():
        raise FileExistsError(f"Skill directory already exists: {skill_dir}")

    skill_dir.mkdir(parents=True, exist_ok=False)
    (skill_dir / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(skill_name=skill_name, skill_title=title_case(skill_name)),
        encoding="utf-8",
    )
    for resource in sorted(resources):
        (skill_dir / resource).mkdir()
    return skill_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_name", help="Lowercase hyphen-case skill identifier")
    parser.add_argument("--base-path", type=Path, default=DEFAULT_BASE_PATH)
    parser.add_argument(
        "--with",
        dest="resources",
        default="",
        help="Comma-separated optional directories: references,scripts,templates",
    )
    args = parser.parse_args()
    try:
        resources = parse_resources(args.resources)
        skill_dir = init_skill(args.skill_name, args.base_path, resources)
    except (ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Created {skill_dir}")
    print("Next: replace TODO text, add only needed resources, then run quick_validate.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
