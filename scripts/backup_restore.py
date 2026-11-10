from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
BACKUP_DIR = BASE_DIR / "backups"
DEFAULT_DB = STATE_DIR / "aisma.db"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def backup_sqlite(db_path: Path = DEFAULT_DB, output_dir: Path = BACKUP_DIR) -> dict[str, str]:
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_file = output_dir / f"aisma_backup_{ts}.db"

    # Use SQLite online backup API for transactional consistency
    src_conn = sqlite3.connect(str(db_path))
    dst_conn = sqlite3.connect(str(backup_file))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    checksum = sha256_file(backup_file)
    manifest_file = output_dir / f"aisma_backup_{ts}.manifest.json"
    manifest = {
        "database": str(db_path),
        "backup_file": str(backup_file),
        "sha256": checksum,
        "timestamp_utc": ts,
        "size_bytes": backup_file.stat().st_size,
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify_and_restore_sqlite(backup_file: Path, manifest_file: Path, target_db: Path) -> bool:
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    actual_hash = sha256_file(backup_file)
    if actual_hash != manifest["sha256"]:
        raise ValueError(f"Checksum mismatch! Expected {manifest['sha256']}, got {actual_hash}")

    target_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_file, target_db)
    # Verify restored SQLite integrity check
    conn = sqlite3.connect(str(target_db))
    try:
        res = conn.execute("PRAGMA integrity_check;").fetchone()
        if not res or res[0] != "ok":
            raise RuntimeError(f"SQLite PRAGMA integrity_check failed: {res}")
    finally:
        conn.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "backup":
        info = backup_sqlite()
        print("Backup created successfully:", json.dumps(info, indent=2))
    else:
        print("Usage: python scripts/backup_restore.py backup")

