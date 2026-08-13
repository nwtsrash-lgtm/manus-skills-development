#!/usr/bin/env bash
# ينفَّذ فقط على الخادم/الجهاز الذي يملك data/ وقواعد SQLite الحية.
# يحتاج: age وgh، وGH_TOKEN بصلاحية كتابة إلى مستودع نسخ احتياطي خاص منفصل.
# لا تشغّله من Render Free أو GitHub Actions؛ لا يمتلك أي منهما ملفات SQLite الحية.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${BACKUP_REPOSITORY:?اكتب owner/private-backup-repo في BACKUP_REPOSITORY}"
: "${GH_TOKEN:?ضع GH_TOKEN في مدير أسرار الخادم لا في Git}"
: "${AGE_RECIPIENT:?ضع AGE_RECIPIENT العام للنسخ الاحتياطي}"

command -v age >/dev/null || { echo "age غير مثبّت" >&2; exit 1; }
command -v gh >/dev/null || { echo "GitHub CLI غير مثبّت" >&2; exit 1; }

umask 077
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
workdir="$(mktemp -d "${ROOT}/.backup-work.XXXXXX")"
cleanup() { rm -rf "$workdir"; }
trap cleanup EXIT

python3 "$ROOT/scripts/backup_data.py" "github-${stamp}" >/dev/null
snapshot="${ROOT}/data/backups/$(date -u +%F)-github-${stamp}"
test -d "$snapshot"

plain="$workdir/tozyw-sqlite-${stamp}.tar.gz"
cipher="$plain.age"
manifest="$cipher.sha256"
tar -C "$(dirname "$snapshot")" -czf "$plain" "$(basename "$snapshot")"
age --recipient "$AGE_RECIPIENT" --output "$cipher" "$plain"
sha256sum "$cipher" > "$manifest"
rm -f "$plain"

tag="sqlite-backup-${stamp}"
notes="نسخة SQLite مشفرة خارجياً. للاستعادة: نزّل الملف، تحقق من SHA-256، ثم age --decrypt بمفتاح المستلم."
if gh release view "$tag" --repo "$BACKUP_REPOSITORY" >/dev/null 2>&1; then
  gh release upload "$tag" "$cipher" "$manifest" --clobber --repo "$BACKUP_REPOSITORY"
else
  gh release create "$tag" "$cipher" "$manifest" --title "$tag" --notes "$notes" --repo "$BACKUP_REPOSITORY"
fi

echo "✅ نُشرت نسخة GitHub المشفرة: $tag"
