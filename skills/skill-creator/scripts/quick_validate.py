#!/usr/bin/env python3
"""Validate the structure and minimum operational readiness of one Manus skill.

Usage:
    quick_validate.py <skill-name-or-path> [--base-path PATH] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

DEFAULT_BASE_PATH = Path("/home/ubuntu/skills")
ALLOWED_PROPERTIES = {"name", "description", "license", "allowed-tools", "metadata"}
FORBIDDEN_ROOT_FILES = {"README.md", "CHANGELOG.md", ".DS_Store"}


def resolve_skill_path(value: str, base_path: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base_path / path


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str | None]:
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", content, re.DOTALL)
    if not match:
        return {}, "No valid YAML frontmatter found"
    try:
        value = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return {}, f"Invalid YAML frontmatter: {exc}"
    if not isinstance(value, dict):
        return {}, "Frontmatter must be a YAML mapping"
    return value, None


def relative_markdown_links(content: str) -> list[str]:
    links = re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", content)
    return [link for link in links if not link.startswith(("http://", "https://", "mailto:"))]


def validate_skill(skill_path_or_name: str, base_path: Path = DEFAULT_BASE_PATH) -> dict[str, Any]:
    skill_path = resolve_skill_path(skill_path_or_name, base_path)
    report: dict[str, Any] = {
        "skill_path": str(skill_path),
        "valid": False,
        "errors": [],
        "warnings": [],
        "metrics": {},
    }
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        report["errors"].append("SKILL.md not found")
        return report

    content = skill_md.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    report["metrics"]["line_count"] = len(lines)
    frontmatter, frontmatter_error = parse_frontmatter(content)
    if frontmatter_error:
        report["errors"].append(frontmatter_error)
        return report

    unexpected = sorted(set(frontmatter) - ALLOWED_PROPERTIES)
    if unexpected:
        report["errors"].append("Unexpected frontmatter key(s): " + ", ".join(unexpected))

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        report["errors"].append("Missing or invalid 'name'")
    else:
        name = name.strip()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            report["errors"].append("Name must use lowercase hyphen-case")
        if len(name) > 64:
            report["errors"].append("Name exceeds 64 characters")
        if name != skill_path.name:
            report["errors"].append("Frontmatter name must match the skill directory")

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        report["errors"].append("Missing or invalid 'description'")
    else:
        description = description.strip()
        report["metrics"]["description_length"] = len(description)
        if "<" in description or ">" in description:
            report["errors"].append("Description cannot contain angle brackets")
        if len(description) > 1024:
            report["errors"].append("Description exceeds 1024 characters")
        if len(description) < 40:
            report["warnings"].append("Description is short; routing may be unreliable")

    if re.search(r"\[TODO:|^description:\s*[\"']?TODO\b", content, flags=re.IGNORECASE | re.MULTILINE):
        report["errors"].append("Remove template TODO markers before delivery")
    if len(lines) > 500:
        report["warnings"].append("SKILL.md exceeds 500 lines; move variant-specific detail into references")

    for filename in sorted(FORBIDDEN_ROOT_FILES):
        if (skill_path / filename).exists():
            report["errors"].append(f"Forbidden skill-root file: {filename}")

    for target in sorted(set(relative_markdown_links(content))):
        if not (skill_path / target).exists():
            report["errors"].append(f"Broken relative link: {target}")

    report["valid"] = not report["errors"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", help="Skill name relative to --base-path, or an absolute path")
    parser.add_argument("--base-path", type=Path, default=DEFAULT_BASE_PATH)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    report = validate_skill(args.skill, args.base_path)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        state = "PASS" if report["valid"] else "FAIL"
        print(f"{state}: {report['skill_path']}")
        for item in report["errors"]:
            print(f"ERROR: {item}")
        for item in report["warnings"]:
            print(f"WARNING: {item}")
        if report["valid"]:
            print("Skill structure is valid.")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
