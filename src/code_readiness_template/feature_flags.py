from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from hashlib import sha256
from typing import Literal

from code_readiness_template.config import Settings, get_settings


@dataclass(frozen=True)
class FeatureFlag:
    key: str
    enabled_by_default: bool
    description: str
    lifecycle: Literal["active", "cleanup", "retired"] = "active"
    rollout_percentage: int = 100
    owner: str = "engineering"
    introduced_on: str = "2026-03-28"
    cleanup_by: str | None = None


WIDGET_WRITE_FLAG = FeatureFlag(
    key="widget_write_enabled",
    enabled_by_default=True,
    description="Controls whether widget creation endpoints accept write traffic.",
    lifecycle="cleanup",
    rollout_percentage=100,
    owner="backend",
    introduced_on="2026-03-28",
    cleanup_by="2026-04-01",
)

FEATURE_FLAGS: dict[str, FeatureFlag] = {
    WIDGET_WRITE_FLAG.key: WIDGET_WRITE_FLAG,
}


def _parse_iso_date(raw_value: str | None) -> datetime | None:
    if raw_value is None:
        return None
    return datetime.fromisoformat(raw_value).replace(tzinfo=UTC)


def stale_feature_flags(
    *, reference_time: datetime | None = None, max_age_days: int = 30
) -> list[FeatureFlag]:
    now = reference_time or datetime.now(UTC)
    stale_flags: list[FeatureFlag] = []
    for flag in FEATURE_FLAGS.values():
        introduced_on = _parse_iso_date(flag.introduced_on)
        cleanup_by = _parse_iso_date(flag.cleanup_by)
        if flag.lifecycle == "cleanup":
            if cleanup_by is None or cleanup_by <= now:
                stale_flags.append(flag)
            continue
        if flag.lifecycle == "active" and introduced_on is not None:
            if introduced_on + timedelta(days=max_age_days) <= now:
                stale_flags.append(flag)
    return stale_flags


def _normalize_bool(raw_value: str) -> bool | None:
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _normalize_percentage(raw_value: str) -> int | None:
    try:
        value = int(raw_value.strip())
    except ValueError:
        return None
    if 0 <= value <= 100:
        return value
    return None


@lru_cache(maxsize=8)
def _parse_feature_flag_overrides(raw_value: str) -> dict[str, bool | int]:
    overrides: dict[str, bool | int] = {}
    if not raw_value:
        return overrides

    for entry in raw_value.split(","):
        item = entry.strip()
        if not item or "=" not in item:
            continue
        key, raw_value = item.split("=", 1)
        normalized = _normalize_bool(raw_value)
        percentage = _normalize_percentage(raw_value)
        flag_key = key.strip()
        if flag_key.endswith("_rollout"):
            base_key = flag_key.removesuffix("_rollout")
            if percentage is None or base_key not in FEATURE_FLAGS:
                continue
            overrides[flag_key] = percentage
            continue
        if normalized is None:
            continue
        if flag_key in FEATURE_FLAGS:
            overrides[flag_key] = normalized
    return overrides


def _rollout_enabled(
    flag: FeatureFlag, distinct_id: str | None, overrides: dict[str, bool | int]
) -> bool:
    rollout_key = f"{flag.key}_rollout"
    rollout_percentage = overrides.get(rollout_key, flag.rollout_percentage)
    if isinstance(rollout_percentage, bool):
        rollout_percentage = int(rollout_percentage) * 100
    if rollout_percentage >= 100:
        return True
    if rollout_percentage <= 0:
        return False
    if distinct_id is None:
        return False
    bucket = int(sha256(distinct_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    return bucket < rollout_percentage


def is_feature_enabled(
    flag_key: str,
    settings: Settings | None = None,
    *,
    distinct_id: str | None = None,
) -> bool:
    runtime_settings = settings or get_settings()
    flag = FEATURE_FLAGS[flag_key]
    overrides = _parse_feature_flag_overrides(runtime_settings.feature_flags)
    enabled = overrides.get(flag_key, flag.enabled_by_default)
    if not enabled:
        return False
    return _rollout_enabled(flag, distinct_id, overrides)


def describe_feature_flags(settings: Settings | None = None) -> dict[str, bool]:
    runtime_settings = settings or get_settings()
    raw_flags = runtime_settings.rollback_feature_flags or runtime_settings.feature_flags
    effective_settings = runtime_settings.model_copy(update={"feature_flags": raw_flags})
    return {
        flag_key: is_feature_enabled(flag_key, settings=effective_settings)
        for flag_key in FEATURE_FLAGS
    }
