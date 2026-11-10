import pytest

from governance.killswitch import KillSwitch, KillSwitchEngagedError


def test_global_kill_switch_blocks(kill_switch: KillSwitch) -> None:
    assert kill_switch.is_engaged() is False
    kill_switch.engage_global(reason="maintenance", updated_by="admin")
    assert kill_switch.is_engaged() is True
    with pytest.raises(KillSwitchEngagedError):
        kill_switch.assert_not_engaged()
    kill_switch.disengage_global(reason="done", updated_by="admin")
    kill_switch.assert_not_engaged()


def test_business_kill_switch_scoped(kill_switch: KillSwitch) -> None:
    kill_switch.engage_business("biz1", reason="incident", updated_by="admin")
    assert kill_switch.is_engaged("biz1") is True
    assert kill_switch.is_engaged("biz2") is False
    with pytest.raises(KillSwitchEngagedError):
        kill_switch.assert_not_engaged("biz1")
    kill_switch.assert_not_engaged("biz2")


def test_unreadable_state_fails_closed(tmp_path) -> None:
    ks = KillSwitch(tmp_path / "ks")
    path = ks._global_path()  # intentional for fail-closed test
    path.write_text("{not-json", encoding="utf-8")
    assert ks.is_engaged() is True
