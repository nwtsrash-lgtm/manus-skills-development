#!/usr/bin/env python3
"""Audit a curated Manus skills collection against repository quality gates.

This tool is intentionally conservative: it reports evidence and gaps, but it does
not rewrite a skill. It can run before and after each development wave.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install it before running this audit.") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GATES = ROOT / "governance" / "quality_gates.json"
DEFAULT_TEST_SCHEMA = ROOT / "governance" / "skill_test_card.schema.json"


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], list[str]]:
    if not text.startswith("---\n"):
        return {}, ["missing YAML frontmatter"]
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        return {}, ["invalid YAML frontmatter delimiter"]
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return {}, [f"invalid YAML: {exc}"]
    if not isinstance(data, dict):
        return {}, ["frontmatter must be a YAML mapping"]
    return data, []


def skill_risk(name: str, gates: dict[str, Any]) -> str:
    name_lower = name.lower()
    profiles = gates["risk_profiles"]
    for level in ("high", "medium", "low"):
        if any(token in name_lower for token in profiles.get(level, [])):
            return level
    return "medium"


def has_workflow(text: str) -> bool:
    markers = (
        "workflow", "process", "checklist", "step ", "step:",
        "routing", "decision", "quick check", "procedure",
        "سير العمل", "دورة التطوير", "دورة حياة", "مسار الاختيار", "تسجيل الدخول", "خطوة ", "الخطوات", "مسار قرار", "قائمة تحقق",
    )
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def has_verification(text: str) -> bool:
    markers = (
        "validat", "verification", "test", "quality", "acceptance", "check",
        "تحقق", "اختبار", "جودة", "قبول", "فحص",
    )
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def has_failure_guidance(text: str) -> bool:
    markers = (
        "error", "failure", "fallback", "retry", "refuse", "safety", "fail closed",
        "خطأ", "فشل", "تراجع", "رفض", "سلامة",
    )
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def markdown_links(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", text)


def lint_links(skill_dir: Path, text: str) -> list[str]:
    broken: list[str] = []
    for raw_target in markdown_links(text):
        if raw_target.startswith(("http://", "https://", "mailto:")):
            continue
        target = (skill_dir / raw_target).resolve()
        if not target.exists():
            broken.append(raw_target)
    return sorted(set(broken))


def load_test_card(test_cards_dir: Path, skill_name: str, min_cases: int) -> dict[str, Any]:
    path = test_cards_dir / f"{skill_name}.json"
    if not path.exists():
        return {"present": False, "valid": False, "issues": ["test card is missing"], "case_count": 0}
    try:
        with path.open(encoding="utf-8") as handle:
            card = json.load(handle)
    except json.JSONDecodeError as exc:
        return {"present": True, "valid": False, "issues": [f"invalid JSON: {exc.msg}"], "case_count": 0}

    issues: list[str] = []
    cases = card.get("cases") if isinstance(card, dict) else None
    if not isinstance(card, dict):
        issues.append("test card must be a JSON object")
        cases = []
    if card.get("skill") != skill_name:
        issues.append("test card skill does not match directory name")
    if not isinstance(card.get("version"), str) or not re.fullmatch(r"\d+\.\d+\.\d+", card.get("version", "")):
        issues.append("test card requires semantic version")
    if not isinstance(cases, list):
        issues.append("test card cases must be an array")
        cases = []
    if len(cases) < min_cases:
        issues.append(f"test card needs at least {min_cases} cases")

    kinds = {case.get("kind") for case in cases if isinstance(case, dict)}
    if "positive" not in kinds:
        issues.append("test card needs a positive invocation case")
    if "negative" not in kinds:
        issues.append("test card needs a negative invocation case")
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            issues.append(f"case {index} must be an object")
            continue
        for key in ("id", "kind", "prompt", "should_invoke", "expected_outcome"):
            if key not in case:
                issues.append(f"case {index} is missing {key}")
        if case.get("kind") not in {"positive", "negative", "failure", "safety"}:
            issues.append(f"case {index} has invalid kind")
        if not isinstance(case.get("should_invoke"), bool):
            issues.append(f"case {index} should_invoke must be boolean")
    return {"present": True, "valid": not issues, "issues": sorted(set(issues)), "case_count": len(cases)}


def audit_skill(skill_dir: Path, gates: dict[str, Any], test_cards_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"skill": skill_dir.name, "status": "invalid", "issues": ["SKILL.md is missing"]}

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    frontmatter, frontmatter_issues = parse_frontmatter(text)
    name = frontmatter.get("name", "") if isinstance(frontmatter.get("name", ""), str) else ""
    description = frontmatter.get("description", "") if isinstance(frontmatter.get("description", ""), str) else ""
    risk = skill_risk(skill_dir.name, gates)
    min_cases = gates["rules"]["high_risk_minimum_test_cases"] if risk == "high" else gates["rules"]["minimum_test_cases"]
    test_card = load_test_card(test_cards_dir, skill_dir.name, min_cases)

    structural_issues = list(frontmatter_issues)
    if name != skill_dir.name:
        structural_issues.append("frontmatter name does not match directory name")
    if not description.strip():
        structural_issues.append("description is missing or empty")
    if len(description.strip()) < gates["rules"]["minimum_description_characters"]:
        structural_issues.append("description is too short for reliable routing")
    structural_issues.extend(f"broken relative link: {target}" for target in lint_links(skill_dir, text))
    for forbidden in gates["rules"]["forbidden_skill_root_files"]:
        if (skill_dir / forbidden).exists():
            structural_issues.append(f"forbidden root file: {forbidden}")

    scores: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}
    issues: list[str] = []

    scores["structural_integrity"] = 15 if not structural_issues else 0
    evidence["structural_integrity"] = ["valid metadata and links"] if not structural_issues else structural_issues
    issues.extend(structural_issues)

    invocation_ok = bool(description.strip()) and test_card["present"] and test_card["valid"]
    scores["invocation_boundaries"] = 15 if invocation_ok else 0
    evidence["invocation_boundaries"] = ["description plus valid positive/negative test cases"] if invocation_ok else test_card["issues"]
    if not invocation_ok:
        issues.extend(f"invocation: {item}" for item in test_card["issues"])

    workflow_ok = has_workflow(text) and test_card["present"] and test_card["valid"]
    scores["workflow"] = 20 if workflow_ok else (10 if has_workflow(text) else 0)
    evidence["workflow"] = ["workflow marker and valid expected outcomes"] if workflow_ok else (["workflow marker found; test card missing or invalid"] if has_workflow(text) else ["no workflow marker found"])
    if not workflow_ok:
        issues.extend(f"workflow: {item}" for item in evidence["workflow"])

    max_lines = gates["rules"]["skill_md_max_lines"]
    disclosure_ok = len(lines) <= max_lines or (skill_dir / "references").exists()
    scores["progressive_disclosure"] = 15 if len(lines) <= max_lines else (8 if disclosure_ok else 0)
    evidence["progressive_disclosure"] = [f"{len(lines)} lines"] if len(lines) <= max_lines else [f"{len(lines)} lines exceeds {max_lines}; split or record an exception"]
    if len(lines) > max_lines:
        issues.extend(evidence["progressive_disclosure"])

    verification_ok = has_verification(text) and test_card["present"] and test_card["valid"]
    scores["verification"] = 15 if verification_ok else (5 if has_verification(text) else 0)
    evidence["verification"] = ["verification marker and valid test card"] if verification_ok else (["verification marker found; test card missing or invalid"] if has_verification(text) else ["no verification marker found"])
    if not verification_ok:
        issues.extend(f"verification: {item}" for item in evidence["verification"])

    safety_ok = has_failure_guidance(text)
    scores["failure_and_safety"] = 10 if safety_ok else 0
    evidence["failure_and_safety"] = ["failure or safety guidance found"] if safety_ok else ["no explicit failure or safety guidance found"]
    if risk == "high" and not safety_ok:
        issues.extend(f"safety: {item}" for item in evidence["failure_and_safety"])

    # Freshness is initially evidentiary only. A later wave can populate external source checks.
    scores["source_freshness"] = 0
    evidence["source_freshness"] = ["baseline: source freshness not yet recorded"]

    score = sum(scores.values())
    mandatory = set(gates["mandatory_gates"])
    mandatory_pass = all(scores.get(gate, 0) > 0 for gate in mandatory)
    status = "approved" if score >= gates["approval_threshold"] and mandatory_pass else "needs_work"

    return {
        "skill": skill_dir.name,
        "path": str(skill_dir.relative_to(ROOT)),
        "risk_level": risk,
        "line_count": len(lines),
        "word_count": len(re.findall(r"\S+", text)),
        "frontmatter": {"name": name, "description": description},
        "test_card": test_card,
        "scores": scores,
        "score": score,
        "mandatory_gates_passed": mandatory_pass,
        "status": status,
        "evidence": evidence,
        "issues": sorted(set(issues)),
    }


def markdown_report(results: list[dict[str, Any]], generated_at: str) -> str:
    approved = sum(item["status"] == "approved" for item in results)
    lines = [
        "# Skills Baseline Audit",
        "",
        f"Generated: `{generated_at}`",
        "",
        f"The audit inspected **{len(results)}** skills. **{approved}** passed all current gates; the remainder form the development backlog.",
        "",
        "| Skill | Risk | Lines | Score | Status | First actionable gap |",
        "|---|---|---:|---:|---|---|",
    ]
    for item in results:
        gap = item["issues"][0] if item["issues"] else "None"
        gap = gap.replace("|", "\\|")
        lines.append(f"| `{item['skill']}` | {item['risk_level']} | {item['line_count']} | {item['score']}/100 | {item['status']} | {gap} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "A `needs_work` result is a prioritization signal, not a claim that the skill is unusable. The baseline intentionally awards no credit for test cards until behavior is documented and validated.",
        "",
    ])
    return "\n".join(lines)


def registry(results: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "generated_at": generated_at,
        "policy": "Operational quality is prioritized over ownership metadata. Refresh source-sensitive skills in their relevant development wave.",
        "skills": [
            {
                "name": item["skill"],
                "path": item["path"],
                "risk_level": item["risk_level"],
                "status": item["status"],
                "baseline_score": item["score"],
                "source_category": "bundled_baseline",
                "test_card": f"tests/skill-cards/{item['skill']}.json",
            }
            for item in results
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=ROOT / "skills")
    parser.add_argument("--gates", type=Path, default=DEFAULT_GATES)
    parser.add_argument("--test-cards", type=Path, default=ROOT / "tests" / "skill-cards")
    parser.add_argument("--output-json", type=Path, default=ROOT / "artifacts" / "skills-audit.json")
    parser.add_argument("--output-markdown", type=Path, default=ROOT / "artifacts" / "skills-audit.md")
    parser.add_argument("--registry", type=Path, default=ROOT / "governance" / "skill_registry.json")
    args = parser.parse_args()

    gates = read_json(args.gates)
    args.test_cards.mkdir(parents=True, exist_ok=True)
    results = [audit_skill(path.parent, gates, args.test_cards) for path in sorted(args.skills_root.glob("*/SKILL.md"))]
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "schema_version": "0.1.0",
        "generated_at": generated_at,
        "quality_gates": str(args.gates.relative_to(ROOT)),
        "summary": {
            "skill_count": len(results),
            "approved_count": sum(item["status"] == "approved" for item in results),
            "needs_work_count": sum(item["status"] == "needs_work" for item in results),
        },
        "skills": results,
    }
    for output, content in (
        (args.output_json, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"),
        (args.output_markdown, markdown_report(results, generated_at)),
        (args.registry, json.dumps(registry(results, generated_at), ensure_ascii=False, indent=2) + "\n"),
    ):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
