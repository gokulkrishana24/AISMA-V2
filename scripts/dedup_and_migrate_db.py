from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
SCRIPTS_DIR = BASE_DIR / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from backup_restore import backup_sqlite
from db.database import DEFAULT_SQLITE_PATH, init_db

TEST_EMAIL_PATTERNS = (
    re.compile(r"^sarah_[0-9a-f]+@innovate-tech\.ai$"),
    re.compile(r"^dave_[0-9a-f]+@synergy-corp\.io$"),
    re.compile(r"^sarah\.lead@innovate-tech\.ai$"),
    re.compile(r"^dave\.ops@synergy-corp\.io$"),
    re.compile(r"^owner_x_[0-9a-f]+@corp-x\.com$"),
    re.compile(r"^founder_[0-9a-f]+@scaleup\.io$"),
    re.compile(r"^op_[0-9a-f]+@example\.com$"),
    re.compile(r"^journey_[0-9a-f]+@aisma\.local$"),
    re.compile(r"^test_[0-9a-f]+@"),
)

TEST_BIZ_NAME_PATTERNS = (
    re.compile(r"^Innovate Tech AI"),
    re.compile(r"^Synergy Corp IO"),
    re.compile(r"^Corp X Holdings"),
    re.compile(r"^ScaleUp (Tech|AI) "),
    re.compile(r"^Journey (Org|Co) "),
)


def is_test_email(email: str) -> bool:
    return any(p.match(email or "") for p in TEST_EMAIL_PATTERNS)


def is_test_biz(name: str) -> bool:
    return any(p.match(name or "") for p in TEST_BIZ_NAME_PATTERNS)


def run_cleanup(db_path: Path = DEFAULT_SQLITE_PATH) -> dict[str, object]:
    backup_manifest = backup_sqlite(db_path=db_path)
    init_db()

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    report: dict[str, object] = {
        "backup": backup_manifest,
        "before": {},
        "removed": {},
        "after": {},
        "unique_indexes_created": [],
    }
    try:
        cur = con.cursor()
        for tbl in (
            "users",
            "businesses",
            "memberships",
            "social_accounts",
            "subscriptions",
            "organization_invites",
            "support_tickets",
            "usage_meters",
        ):
            report["before"][tbl] = cur.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]

        # 1. Identify test users & businesses created by prior un-isolated pytest runs
        users = cur.execute("SELECT id, email FROM users").fetchall()
        test_user_ids = [r["id"] for r in users if is_test_email(r["email"])]

        businesses = cur.execute("SELECT id, name FROM businesses").fetchall()
        test_biz_ids = [
            r["id"]
            for r in businesses
            if r["id"] != "biz_apex_enterprises" and is_test_biz(r["name"])
        ]

        removed_counts: dict[str, int] = {}

        if test_biz_ids:
            placeholders = ",".join("?" for _ in test_biz_ids)
            for child_tbl in (
                "memberships",
                "subscriptions",
                "organization_invites",
                "support_tickets",
                "social_accounts",
                "usage_meters",
                "campaigns",
                "content_drafts",
                "approval_items",
                "notifications",
                "agent_tasks",
                "audit_log_records",
                "brand_profiles",
                "tenant_settings",
            ):
                cur.execute(
                    f'DELETE FROM "{child_tbl}" WHERE business_id IN ({placeholders})',
                    test_biz_ids,
                )
                removed_counts[f"{child_tbl}_test_biz"] = cur.rowcount

            cur.execute(f"DELETE FROM businesses WHERE id IN ({placeholders})", test_biz_ids)
            removed_counts["businesses_test"] = cur.rowcount

        if test_user_ids:
            u_ph = ",".join("?" for _ in test_user_ids)
            cur.execute(f"DELETE FROM memberships WHERE user_id IN ({u_ph})", test_user_ids)
            removed_counts["memberships_test_users"] = cur.rowcount
            cur.execute(f"DELETE FROM users WHERE id IN ({u_ph})", test_user_ids)
            removed_counts["users_test"] = cur.rowcount

        # 2. Remove duplicate/synthetic test-run social_accounts on biz_apex_enterprises (acct_* from test_api)
        cur.execute(
            "DELETE FROM social_accounts WHERE business_id = 'biz_apex_enterprises' AND account_id LIKE 'acct_%'"
        )
        removed_counts["social_accounts_test_artifacts"] = cur.rowcount

        # 3. Deduplicate any remaining memberships on (user_id, business_id) keeping earliest id
        cur.execute(
            """
            DELETE FROM memberships
            WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM memberships GROUP BY user_id, business_id
            )
            """
        )
        removed_counts["memberships_dedup"] = cur.rowcount

        # 4. Deduplicate subscriptions per business_id keeping earliest
        cur.execute(
            """
            DELETE FROM subscriptions
            WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM subscriptions GROUP BY business_id
            )
            """
        )
        removed_counts["subscriptions_dedup"] = cur.rowcount

        # 5. Deduplicate usage_meters per (business_id, period_month)
        cur.execute(
            """
            DELETE FROM usage_meters
            WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM usage_meters GROUP BY business_id, period_month
            )
            """
        )
        removed_counts["usage_meters_dedup"] = cur.rowcount

        # 6. Deduplicate social_accounts per (business_id, platform, account_id)
        cur.execute(
            """
            DELETE FROM social_accounts
            WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM social_accounts GROUP BY business_id, platform, account_id
            )
            """
        )
        removed_counts["social_accounts_dedup"] = cur.rowcount

        # 7. Clean orphaned test support_tickets without existing business or test beta noise
        cur.execute(
            "DELETE FROM support_tickets WHERE description = 'Works well in local beta.' AND subject LIKE '%Clean UI%'"
        )
        removed_counts["support_tickets_test_feedback"] = cur.rowcount

        # 8. Enforce unique indexes at SQLite level for single source of truth
        indexes = [
            ("uq_membership_user_business", "memberships", "user_id, business_id"),
            ("uq_social_account_tenant_platform", "social_accounts", "business_id, platform, account_id"),
            ("uq_usage_meter_tenant_month", "usage_meters", "business_id, period_month"),
            ("uq_subscription_business", "subscriptions", "business_id"),
        ]
        created_idx = []
        for idx_name, tbl_name, cols in indexes:
            cur.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS "{idx_name}" ON "{tbl_name}" ({cols})')
            created_idx.append(idx_name)

        con.commit()
        report["removed"] = removed_counts
        report["unique_indexes_created"] = created_idx

        for tbl in (
            "users",
            "businesses",
            "memberships",
            "social_accounts",
            "subscriptions",
            "organization_invites",
            "support_tickets",
            "usage_meters",
        ):
            report["after"][tbl] = cur.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
    finally:
        con.close()

    return report


if __name__ == "__main__":
    res = run_cleanup()
    print(json.dumps(res, indent=2))
