# AISMA v2 — Backup & Disaster Recovery Verification Report

**Date:** November 10, 2026  
**Tooling Verified:** `scripts/backup_restore.py`  

---

## 1. Tested Backup & Restore Evidence

- **Command Executed:** `python -m pytest -vv tests/integration/test_modernization_and_ops.py::test_database_backup_and_restore_integrity`
- **Actual Result:** **PASSED**
  1. Invoked `backup_sqlite()` using SQLite's online `sqlite3.Connection.backup()` API against `state/aisma.db`.
  2. Generated SHA-256 checksum manifest JSON (`aisma_backup_<ts>.manifest.json` with 64-char hex digest).
  3. Invoked `verify_and_restore_sqlite()` to verify digest equality, restore into an isolated temporary DB, and assert `PRAGMA integrity_check;` returned `ok`.

---

## 2. Operational Policy & Limitations

- **Recommended Frequency:** Daily automated snapshots + pre-migration snapshots before `alembic upgrade`.
- **Retention Policy:** 30 daily snapshots local / encrypted off-host mirror in production.
- **Limitation:** PostgreSQL `pg_dump` / `pg_restore` disaster recovery remains unverified on this machine until PostgreSQL 16 runs inside local Docker Desktop.

