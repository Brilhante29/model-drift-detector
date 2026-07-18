from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

MONITORED_ROLES = frozenset({"feature", "prediction"})


@dataclass(frozen=True)
class MonitoringBatch:
    batch_id: str
    values: Mapping[str, tuple[float, ...]]
    roles: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.batch_id:
            raise ValueError("batch_id must not be empty")
        if not self.values:
            raise ValueError("batch must contain monitored columns")
        if set(self.values) != set(self.roles):
            raise ValueError("values and roles must contain the same columns")

        immutable_values: dict[str, tuple[float, ...]] = {}
        expected_rows: int | None = None
        for name, raw_values in self.values.items():
            role = self.roles[name]
            if role not in MONITORED_ROLES:
                raise ValueError(f"unsupported monitored role for {name}: {role}")
            values = tuple(float(value) for value in raw_values)
            if not values:
                raise ValueError(f"column {name} must not be empty")
            if expected_rows is None:
                expected_rows = len(values)
            elif len(values) != expected_rows:
                raise ValueError("all monitored columns must have the same row count")
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"column {name} contains a non-finite value")
            immutable_values[name] = values

        immutable_roles = {name: str(role) for name, role in self.roles.items()}
        object.__setattr__(self, "values", MappingProxyType(immutable_values))
        object.__setattr__(self, "roles", MappingProxyType(immutable_roles))

    @property
    def row_count(self) -> int:
        return len(next(iter(self.values.values())))


@dataclass(frozen=True)
class ColumnStatistic:
    name: str
    role: str
    p_value: float
    effect_size: float

    def __post_init__(self) -> None:
        if self.role not in MONITORED_ROLES:
            raise ValueError(f"unsupported role: {self.role}")
        if not math.isfinite(self.p_value) or not 0.0 <= self.p_value <= 1.0:
            raise ValueError("p_value must be finite and between zero and one")
        if not math.isfinite(self.effect_size) or not 0.0 <= self.effect_size <= 1.0:
            raise ValueError("effect_size must be finite and between zero and one")


@dataclass(frozen=True)
class ColumnDecision:
    name: str
    role: str
    p_value: float
    effect_size: float
    adjusted_alpha: float
    statistically_significant: bool
    effect_exceeds_minimum: bool
    drifted: bool


@dataclass(frozen=True)
class DriftDecision:
    alarm: bool
    feature_drift_share: float
    prediction_drifted: bool
    drifted_columns: tuple[str, ...]
    columns: tuple[ColumnDecision, ...]
    policy: Mapping[str, float | str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy", MappingProxyType(dict(self.policy)))


@dataclass(frozen=True)
class AlarmPolicy:
    alpha: float = 0.05
    minimum_effect: float = 0.10
    minimum_feature_drift_share: float = 0.125
    correction: str = "holm"

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must be between zero and one")
        if not 0.0 <= self.minimum_effect <= 1.0:
            raise ValueError("minimum_effect must be between zero and one")
        if not 0.0 < self.minimum_feature_drift_share <= 1.0:
            raise ValueError("minimum_feature_drift_share must be in (0, 1]")
        if self.correction != "holm":
            raise ValueError("only Holm correction is supported")

    def decide(self, statistics: tuple[ColumnStatistic, ...]) -> DriftDecision:
        if not statistics:
            raise ValueError("at least one column statistic is required")
        if len({statistic.name for statistic in statistics}) != len(statistics):
            raise ValueError("column statistics must have unique names")

        ordered = sorted(statistics, key=lambda item: (item.p_value, item.name))
        decisions_by_name: dict[str, ColumnDecision] = {}
        family_still_rejected = True
        total = len(ordered)

        for index, statistic in enumerate(ordered):
            adjusted_alpha = self.alpha / (total - index)
            significant = family_still_rejected and statistic.p_value <= adjusted_alpha
            if not significant:
                family_still_rejected = False
            effect_exceeds = statistic.effect_size >= self.minimum_effect
            decisions_by_name[statistic.name] = ColumnDecision(
                name=statistic.name,
                role=statistic.role,
                p_value=statistic.p_value,
                effect_size=statistic.effect_size,
                adjusted_alpha=adjusted_alpha,
                statistically_significant=significant,
                effect_exceeds_minimum=effect_exceeds,
                drifted=significant and effect_exceeds,
            )

        columns = tuple(decisions_by_name[item.name] for item in statistics)
        feature_columns = tuple(item for item in columns if item.role == "feature")
        if not feature_columns:
            raise ValueError("at least one feature column is required")
        feature_drift_share = (
            sum(item.drifted for item in feature_columns) / len(feature_columns)
        )
        prediction_drifted = any(
            item.drifted for item in columns if item.role == "prediction"
        )
        drifted_columns = tuple(item.name for item in columns if item.drifted)
        alarm = (
            feature_drift_share >= self.minimum_feature_drift_share
            or prediction_drifted
        )
        return DriftDecision(
            alarm=alarm,
            feature_drift_share=feature_drift_share,
            prediction_drifted=prediction_drifted,
            drifted_columns=drifted_columns,
            columns=columns,
            policy={
                "alpha": self.alpha,
                "minimum_effect": self.minimum_effect,
                "minimum_feature_drift_share": self.minimum_feature_drift_share,
                "correction": self.correction,
            },
        )
