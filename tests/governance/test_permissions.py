import pytest

from governance.permissions import (
    Action,
    PermissionContext,
    PermissionDeniedError,
    PermissionManager,
)


def test_default_deny_unknown_actor(permission_manager: PermissionManager) -> None:
    ctx = PermissionContext(business_id="biz1", actor="unknown_agent")
    assert permission_manager.is_allowed("unknown_agent", Action.READ_BUSINESS_DATA) is False
    with pytest.raises(PermissionDeniedError):
        permission_manager.require(ctx, Action.READ_BUSINESS_DATA)


def test_agent_allowed_actions(permission_manager: PermissionManager) -> None:
    ctx = PermissionContext(business_id="biz1", actor="content_engine")
    permission_manager.require(ctx, Action.WRITE_DRAFT)
    permission_manager.require(ctx, Action.REQUEST_PUBLISH)
    with pytest.raises(PermissionDeniedError):
        permission_manager.require(ctx, Action.PUBLISH)


def test_business_isolation(permission_manager: PermissionManager) -> None:
    ctx = PermissionContext(business_id="biz2", actor="content_engine", actor_business_id="biz1")
    with pytest.raises(PermissionDeniedError, match="Business isolation"):
        permission_manager.require(ctx, Action.READ_BUSINESS_DATA)
