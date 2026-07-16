from __future__ import annotations

from scipy.stats import ks_2samp

from model_drift.domain import ColumnStatistic, MonitoringBatch


class ScipyKsDetector:
    def __init__(self, minimum_samples: int = 200) -> None:
        if minimum_samples < 2:
            raise ValueError("minimum_samples must be at least two")
        self.minimum_samples = minimum_samples

    def compare(
        self,
        reference: MonitoringBatch,
        current: MonitoringBatch,
    ) -> tuple[ColumnStatistic, ...]:
        if tuple(reference.values) != tuple(current.values):
            raise ValueError("reference and current columns or order differ")
        if dict(reference.roles) != dict(current.roles):
            raise ValueError("reference and current column roles differ")
        if reference.row_count < self.minimum_samples:
            raise ValueError("reference batch is smaller than minimum_samples")
        if current.row_count < self.minimum_samples:
            raise ValueError("current batch is smaller than minimum_samples")

        statistics: list[ColumnStatistic] = []
        for name, reference_values in reference.values.items():
            result = ks_2samp(
                reference_values,
                current.values[name],
                alternative="two-sided",
                method="auto",
            )
            statistics.append(
                ColumnStatistic(
                    name=name,
                    role=reference.roles[name],
                    p_value=float(result.pvalue),
                    effect_size=float(result.statistic),
                )
            )
        return tuple(statistics)
