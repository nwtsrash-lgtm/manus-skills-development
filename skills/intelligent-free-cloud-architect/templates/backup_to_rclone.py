#!/usr/bin/env python3
"""إنشاء نسخة SQLite متسقة ثم رفعها عبر rclone إلى remote مشفّر من طرف العميل.

الاستخدام من خادم يملك مجلد data فعلياً:
  RCLONE_REMOTE=secure_gdrive:tozyw RCLONE_CONFIG=/etc/tozyw/rclone.conf \
  RCLONE_CONFIG_PASS=... python scripts/backup_to_rclone.py

يجب أن يشير RCLONE_REMOTE إلى remote من نوع ``crypt`` يلتف حول Google Drive أو
مزود تخزين آخر. لا تضع التوكن أو كلمة مرور rclone في Git أو في سجلات الخدمة.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

from backup_data import run as create_snapshot

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"المتغير {name} مطلوب ولا يجوز وضعه في Git")
    return value


def main() -> int:
    remote = require_env("RCLONE_REMOTE").rstrip("/")
    rclone_config = require_env("RCLONE_CONFIG")
    rclone_config_pass = require_env("RCLONE_CONFIG_PASS")
    if not Path(rclone_config).is_file():
        raise RuntimeError("ملف إعداد rclone غير موجود أو ليس secret file صالحاً")
    if shutil.which("rclone") is None:
        raise RuntimeError("rclone غير مثبّت على الخادم")

    work_parent = Path(os.environ.get("BACKUP_WORKDIR", DATA_DIR / ".backup-work"))
    work_parent.mkdir(parents=True, exist_ok=True)
    os.umask(0o077)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label = f"auto-{stamp}"
    stage = Path(tempfile.mkdtemp(prefix="tozyw-", dir=work_parent))

    try:
        if create_snapshot(dest_root=stage, label=label) != 0:
            return 2

        snapshot = stage / f"{date.today().isoformat()}-{label}"
        if not snapshot.is_dir():
            raise RuntimeError("لم يُنشأ مجلد اللقطة المتوقع")

        archive = stage / f"tozyw-sqlite-{stamp}.tar.gz"
        with tarfile.open(archive, mode="w:gz") as bundle:
            bundle.add(snapshot, arcname=snapshot.name)
        manifest = archive.with_suffix(archive.suffix + ".sha256")
        manifest.write_text(f"{sha256(archive)}  {archive.name}\n", encoding="utf-8")

        env = os.environ.copy()
        env["RCLONE_CONFIG"] = rclone_config
        env["RCLONE_CONFIG_PASS"] = rclone_config_pass
        for file_path in (archive, manifest):
            destination = f"{remote}/{file_path.name}"
            subprocess.run(
                [
                    "rclone", "copyto", "--retries", "3",
                    "--low-level-retries", "10", str(file_path), destination,
                ],
                check=True,
                env=env,
            )
            subprocess.run(["rclone", "lsf", destination], check=True, env=env)

        print(f"✅ اكتمل رفع النسخة المشفرة: {archive.name}")
        return 0
    finally:
        if os.environ.get("KEEP_LOCAL_BACKUP", "0") != "1":
            shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"⛔ فشل النسخ الاحتياطي: {exc}", file=sys.stderr)
        raise SystemExit(1)
