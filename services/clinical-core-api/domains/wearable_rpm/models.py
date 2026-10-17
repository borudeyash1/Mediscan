"""
Domain models for Wearable Telemetry, Streaming RPM, EWMA Anomaly Detection & 3-Tier Escalation.
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

# Standardized Clinical LOINC & UCUM Constants
LOINC_HEART_RATE = "8867-4"
LOINC_HRV = "80404-7"
LOINC_SPO2 = "59408-5"
LOINC_SYSTOLIC_BP = "8480-6"
LOINC_DIASTOLIC_BP = "8462-4"
LOINC_GLUCOSE = "14749-6"
LOINC_RESPIRATORY_RATE = "9279-1"
LOINC_TEMPERATURE = "8310-5"

UCUM_BPM = "/min"
UCUM_MS = "ms"
UCUM_PERCENT = "%"
UCUM_MMHG = "mm[Hg]"
UCUM_MGDL = "mg/dL"
UCUM_CELSIUS = "Cel"


class EscalationTier(str, Enum):
    TIER_1_PATIENT_CHECKIN = "TIER_1_PATIENT_CHECKIN"
    TIER_2_NURSE_RPM_QUEUE = "TIER_2_NURSE_RPM_QUEUE"
    TIER_3_CRITICAL_DISPATCH = "TIER_3_CRITICAL_DISPATCH"


class TelemetrySourceDevice(str, Enum):
    APPLE_HEALTHKIT = "APPLE_HEALTHKIT"
    GOOGLE_HEALTH_CONNECT = "GOOGLE_HEALTH_CONNECT"
    DEXCOM_CGM = "DEXCOM_CGM"
    ABBOTT_FREESTYLE = "ABBOTT_FREESTYLE"
    BLE_PULSE_OXIMETER = "BLE_PULSE_OXIMETER"
    BLE_ECG_PATCH = "BLE_ECG_PATCH"
    BEDSIDE_ICU_MONITOR = "BEDSIDE_ICU_MONITOR"


class VitalReading(BaseModel):
    """Standardized single clinical vital telemetry reading."""
    reading_id: str = Field(default_factory=lambda: f"vit_{uuid4().hex[:8]}")
    loinc_code: str
    metric_value: float
    ucum_unit: str
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signal_quality_index: float = Field(default=0.95, ge=0.0, le=1.0)
    device_source: TelemetrySourceDevice = Field(default=TelemetrySourceDevice.BLE_PULSE_OXIMETER)
    ewma_z_score: Optional[float] = None


class TelemetryIngestRequest(BaseModel):
    """Payload for POST /api/v2/telemetry/ingest."""
    clinical_subject_id: str
    tenant_id: Optional[str] = "mediscan-default"
    readings: list[VitalReading]
    patient_activity_state: str = Field(default="RESTING", description="RESTING | AMBULATORY | SLEEPING | EXERCISING")
    supplemental_oxygen: bool = False


class AnomalyEvent(BaseModel):
    """Individual EWMA anomaly flagged on a telemetry metric."""
    loinc_code: str
    metric_name: str
    observed_value: float
    rolling_mean: float
    rolling_std: float
    z_score: float
    is_critical: bool


class EscalationAlert(BaseModel):
    """3-Tier Escalation Notification Payload."""
    alert_id: str = Field(default_factory=lambda: f"esc_{uuid4().hex[:8]}")
    clinical_subject_id: str
    tier: EscalationTier
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    anomalies: list[AnomalyEvent]
    news2_score: int
    news2_category: str
    summary_message: str
    emergency_dispatch_payload: Optional[dict[str, Any]] = None


class TelemetryIngestResponse(BaseModel):
    """Response returned upon telemetry ingestion."""
    status: str = "success"
    clinical_subject_id: str
    readings_processed: int
    anomalies_detected: list[AnomalyEvent] = []
    current_news2_score: int
    current_news2_category: str
    escalation_triggered: Optional[EscalationAlert] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
