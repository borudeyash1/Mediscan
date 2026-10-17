"""
Stateful EWMA (Exponentially Weighted Moving Average) & Z-Score Anomaly Detector.
Maintains rolling personal physiological baselines per clinical subject across:
  - Heart Rate (8867-4)
  - HRV SDNN (80404-7)
  - SpO2 (59408-5)
  - Systolic BP (8480-6) / Diastolic BP (8462-4)
  - Continuous Glucose CGM (14749-6)
"""

import math
from typing import Any, Optional
import structlog

from .models import (
    LOINC_HEART_RATE,
    LOINC_HRV,
    LOINC_SPO2,
    LOINC_SYSTOLIC_BP,
    LOINC_DIASTOLIC_BP,
    LOINC_GLUCOSE,
    LOINC_RESPIRATORY_RATE,
    LOINC_TEMPERATURE,
    VitalReading,
    AnomalyEvent,
)

logger = structlog.get_logger(__name__)

METRIC_NAMES = {
    LOINC_HEART_RATE: "Heart Rate",
    LOINC_HRV: "HRV (SDNN)",
    LOINC_SPO2: "Oxygen Saturation (SpO2)",
    LOINC_SYSTOLIC_BP: "Systolic Blood Pressure",
    LOINC_DIASTOLIC_BP: "Diastolic Blood Pressure",
    LOINC_GLUCOSE: "Continuous Glucose (CGM)",
    LOINC_RESPIRATORY_RATE: "Respiratory Rate",
    LOINC_TEMPERATURE: "Body Temperature",
}


class PatientMetricState:
    """Stateful personal baseline tracker for a single LOINC biomarker."""

    def __init__(self, loinc_code: str, alpha: float = 0.15, beta: float = 0.15):
        self.loinc_code = loinc_code
        self.alpha = alpha
        self.beta = beta
        self.count: int = 0
        self.mean: float = 0.0
        self.variance: float = 1.0

    def update(self, val: float) -> tuple[float, float, float]:
        """
        Ingest new reading value.
        Returns: (prior_mean, prior_std, z_score).
        """
        if self.count == 0:
            self.mean = val
            # Standard physiological initial variances to prevent zero-division
            if self.loinc_code == LOINC_HEART_RATE:
                self.variance = 36.0  # std ~6
            elif self.loinc_code == LOINC_SPO2:
                self.variance = 4.0   # std ~2
            elif self.loinc_code == LOINC_GLUCOSE:
                self.variance = 100.0 # std ~10
            elif self.loinc_code == LOINC_SYSTOLIC_BP:
                self.variance = 64.0  # std ~8
            else:
                self.variance = 16.0  # std ~4

            self.count = 1
            prior_std = math.sqrt(self.variance)
            return (self.mean, prior_std, 0.0)

        prior_mean = self.mean
        prior_std = max(0.5, math.sqrt(max(0.1, self.variance)))

        # Calculate Z-score relative to prior baseline
        z_score = (val - prior_mean) / prior_std

        # Update rolling EWMA mean and variance
        diff = val - prior_mean
        self.mean = (self.alpha * val) + ((1.0 - self.alpha) * prior_mean)
        self.variance = (self.beta * (diff ** 2)) + ((1.0 - self.beta) * self.variance)
        self.count += 1

        return (prior_mean, prior_std, z_score)


class SubjectBaselineTracker:
    """Maintains active baseline trackers across all vitals for a patient."""

    def __init__(self, subject_id: str):
        self.subject_id = subject_id
        self.metrics: dict[str, PatientMetricState] = {}
        self.latest_vitals: dict[str, float] = {
            LOINC_HEART_RATE: 75.0,
            LOINC_SPO2: 98.0,
            LOINC_SYSTOLIC_BP: 120.0,
            LOINC_RESPIRATORY_RATE: 16.0,
            LOINC_TEMPERATURE: 37.0,
            LOINC_GLUCOSE: 100.0,
        }

    def ingest_reading(self, reading: VitalReading) -> Optional[AnomalyEvent]:
        """
        Process single reading.
        Updates baseline, checks Z-score threshold, and checks clinical hard thresholds.
        """
        loinc = reading.loinc_code
        val = reading.metric_value
        self.latest_vitals[loinc] = val

        if loinc not in self.metrics:
            self.metrics[loinc] = PatientMetricState(loinc)

        tracker = self.metrics[loinc]
        prior_mean, prior_std, z_score = tracker.update(val)
        reading.ewma_z_score = round(z_score, 2)

        # Critical physiological boundaries
        is_hard_critical = False
        if loinc == LOINC_HEART_RATE and (val >= 140.0 or val <= 40.0):
            is_hard_critical = True
        elif loinc == LOINC_SPO2 and val <= 88.0:
            is_hard_critical = True
        elif loinc == LOINC_GLUCOSE and (val <= 50.0 or val >= 350.0):
            is_hard_critical = True
        elif loinc == LOINC_SYSTOLIC_BP and (val >= 180.0 or val <= 80.0):
            is_hard_critical = True

        abs_z = abs(z_score)
        # Flag anomaly if |Z| > 3.0 or hard physiological critical trigger
        if abs_z > 3.0 or is_hard_critical:
            metric_name = METRIC_NAMES.get(loinc, f"Biomarker {loinc}")
            return AnomalyEvent(
                loinc_code=loinc,
                metric_name=metric_name,
                observed_value=round(val, 2),
                rolling_mean=round(prior_mean, 2),
                rolling_std=round(prior_std, 2),
                z_score=round(z_score, 2),
                is_critical=abs_z > 3.0 or is_hard_critical,
            )

        return None


class EWMAAnomalyDetector:
    """Global manager for patient baselines and anomaly detection."""

    def __init__(self):
        self._subjects: dict[str, SubjectBaselineTracker] = {}

    def get_or_create_tracker(self, subject_id: str) -> SubjectBaselineTracker:
        if subject_id not in self._subjects:
            self._subjects[subject_id] = SubjectBaselineTracker(subject_id)
        return self._subjects[subject_id]

    def reset_subject(self, subject_id: str) -> None:
        self._subjects.pop(subject_id, None)

    def process_readings(
        self, subject_id: str, readings: list[VitalReading]
    ) -> tuple[list[AnomalyEvent], dict[str, float]]:
        """
        Process batch of readings for a subject.
        Returns list of detected anomalies and current vitals map.
        """
        tracker = self.get_or_create_tracker(subject_id)
        anomalies: list[AnomalyEvent] = []

        for r in readings:
            anomaly = tracker.ingest_reading(r)
            if anomaly:
                anomalies.append(anomaly)

        return anomalies, tracker.latest_vitals
