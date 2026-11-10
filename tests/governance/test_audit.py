from governance.audit import AuditLogger, redact_pii, verify_audit_chain


def test_audit_chain_and_redaction(audit_logger: AuditLogger) -> None:
    e1 = audit_logger.log(
        business_id="biz1",
        actor="content_engine",
        action="draft_created",
        resource="draft:123",
        outcome="ok",
        details={"email": "person@example.com", "note": "call +1 (555) 123-4567"},
    )
    e2 = audit_logger.log(
        business_id="biz1",
        actor="orchestrator",
        action="queued",
        resource="draft:123",
        outcome="ok",
        details={"count": 1},
    )
    assert e1.entry_hash != e2.entry_hash
    entries = audit_logger.read_entries("biz1")
    assert len(entries) == 2
    ok, msg = verify_audit_chain(entries)
    assert ok, msg
    assert entries[0]["details"]["email"] == "[REDACTED_EMAIL]"
    assert "[REDACTED_PHONE]" in entries[0]["details"]["note"]


def test_audit_chain_detects_tamper(audit_logger: AuditLogger) -> None:
    audit_logger.log(
        business_id="biz1",
        actor="a",
        action="x",
        resource="r",
        outcome="ok",
        details={},
    )
    entries = audit_logger.read_entries("biz1")
    entries[0]["outcome"] = "tampered"
    ok, msg = verify_audit_chain(entries)
    assert not ok
    assert "invalid entry_hash" in msg


def test_redact_pii_nested() -> None:
    data = {"user": {"contact": "a@b.com"}, "items": ["555-111-2222"]}
    red = redact_pii(data)
    assert red["user"]["contact"] == "[REDACTED_EMAIL]"
    assert red["items"][0] == "[REDACTED_PHONE]"
