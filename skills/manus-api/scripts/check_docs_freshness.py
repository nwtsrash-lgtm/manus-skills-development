#!/usr/bin/env python3
"""Check bundled Manus API v2 documentation against its generated SHA-256 index."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS_ROOT = SKILL_ROOT / "docs" / "v2"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-root", type=Path, default=DEFAULT_DOCS_ROOT)
    parser.add_argument("--index", type=Path, default=None)
    parser.add_argument("--warn-after-days", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    docs_root = args.docs_root.resolve()
    index_path = args.index.resolve() if args.index else docs_root / "index.json"
    if not index_path.is_file():
        raise SystemExit(f"Index is missing: {index_path}. Run build_docs_index.py first.")

    index = json.loads(index_path.read_text(encoding="utf-8"))
    expected = {entry["path"]: entry["sha256"] for entry in index.get("documents", [])}
    current = {
        path.relative_to(docs_root).as_posix(): sha256(path)
        for path in docs_root.rglob("*")
        if path.is_file() and path.resolve() != index_path and path.suffix in {".mdx", ".json"}
    }
    missing = sorted(set(expected) - set(current))
    added = sorted(set(current) - set(expected))
    changed = sorted(name for name in set(expected) & set(current) if expected[name] != current[name])

    generated_at = index.get("generated_at")
    age_days = None
    stale = False
    if isinstance(generated_at, str):
        try:
            timestamp = dt.datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            age_days = (dt.datetime.now(dt.timezone.utc) - timestamp).days
            stale = age_days > args.warn_after_days
        except ValueError:
            stale = True

    report = {
        "valid": not (missing or added or changed),
        "generated_at": generated_at,
        "age_days": age_days,
        "stale_warning": stale,
        "missing": missing,
        "added": added,
        "changed": changed,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("PASS" if report["valid"] else "FAIL")
        print(f"Index age: {age_days if age_days is not None else 'unknown'} days")
        if stale:
            print("WARNING: index is older than the configured review interval")
        for key in ("missing", "added", "changed"):
            for name in report[key]:
                print(f"{key.upper()}: {name}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
