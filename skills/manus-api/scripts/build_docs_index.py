#!/usr/bin/env python3
"""Build a deterministic index of bundled Manus API v2 documentation files."""
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
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    docs_root = args.docs_root.resolve()
    output = args.output.resolve() if args.output else docs_root / "index.json"
    if not docs_root.is_dir():
        raise SystemExit(f"Documentation directory does not exist: {docs_root}")

    documents = []
    for path in sorted(docs_root.rglob("*")):
        if not path.is_file() or path.resolve() == output:
            continue
        if path.suffix not in {".mdx", ".json"}:
            continue
        documents.append(
            {
                "path": path.relative_to(docs_root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    payload = {
        "schema_version": "0.1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "document_count": len(documents),
        "documents": documents,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {len(documents)} documents at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
