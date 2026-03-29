from __future__ import annotations

from datetime import UTC, datetime

from code_readiness_template.config import Settings
from code_readiness_template.feature_flags import (
    FEATURE_FLAGS,
    WIDGET_WRITE_FLAG,
    describe_feature_flags,
    is_feature_enabled,
    stale_feature_flags,
)


def test_feature_flag_defaults_to_enabled() -> None:
    settings = Settings(feature_flags="")
    assert is_feature_enabled(WIDGET_WRITE_FLAG.key, settings=settings) is True


def test_feature_flag_override_can_disable_flag() -> None:
    settings = Settings(feature_flags="widget_write_enabled=false")
    assert is_feature_enabled(WIDGET_WRITE_FLAG.key, settings=settings) is False


def test_feature_flag_descriptions_include_runtime_state() -> None:
    settings = Settings(feature_flags="widget_write_enabled=false")
    assert describe_feature_flags(settings=settings) == {"widget_write_enabled": False}


def test_feature_flag_rollout_can_disable_all_traffic() -> None:
    settings = Settings(feature_flags="widget_write_enabled=true,widget_write_enabled_rollout=0")
    assert is_feature_enabled(WIDGET_WRITE_FLAG.key, settings=settings, distinct_id="demo") is False


def test_feature_flag_rollout_is_stable_per_distinct_id() -> None:
    settings = Settings(feature_flags="widget_write_enabled=true,widget_write_enabled_rollout=50")
    result_one = is_feature_enabled(WIDGET_WRITE_FLAG.key, settings=settings, distinct_id="demo")
    result_two = is_feature_enabled(WIDGET_WRITE_FLAG.key, settings=settings, distinct_id="demo")
    assert result_one is result_two


def test_describe_feature_flags_prefers_rollback_overrides() -> None:
    settings = Settings(
        feature_flags="widget_write_enabled=true",
        rollback_feature_flags="widget_write_enabled=false,widget_write_enabled_rollout=0",
    )
    assert describe_feature_flags(settings=settings) == {"widget_write_enabled": False}


def test_stale_feature_flags_reports_cleanup_flags_past_deadline() -> None:
    stale = stale_feature_flags(reference_time=datetime(2026, 4, 15, tzinfo=UTC))

    assert [flag.key for flag in stale] == ["widget_write_enabled"]


def test_feature_flag_catalog_tracks_stale_detection_metadata() -> None:
    assert FEATURE_FLAGS == {"widget_write_enabled": WIDGET_WRITE_FLAG}
    assert WIDGET_WRITE_FLAG.lifecycle == "cleanup"
    assert WIDGET_WRITE_FLAG.owner == "backend"
    assert WIDGET_WRITE_FLAG.cleanup_by == "2026-04-01"
