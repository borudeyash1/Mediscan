"""
Data models for Population Health, Outbreak Detection, LACE+ Readmission Risk, and Care Gaps.
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class OutbreakSeverity(str, Enum):
    EMERGENT_OUTBREAK = "EMERGENT_OUTBREAK"
    ELEVATED_SURGE = "ELEVATED_SURGE"
    WATCHLIST = "WATCHLIST"
    BASELINE = "BASELINE"


class DiseaseOutbreakCluster(BaseModel):
    """Geospatial outbreak cluster."""
    cluster_id: str = Field(default_factory=lambda: f"cluster_{uuid4().hex[:8]}")
    pathogen: str  # Dengue, Influenza, Malaria, COVID-19
    latitude: float
    longitude: float
    radius_km: float = 12.5
    case_count: int
    reproduction_rate_rt: float = Field(..., description="Estimated effective reproduction number Rt")
    growth_rate_percent: float
    severity: OutbreakSeverity
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    affected_geohash: str
    recommended_public_health_actions: list[str] = Field(default_factory=list)


class ReadmissionRiskTier(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PatientReadmissionScore(BaseModel):
    """LACE+ Index 30-Day Hospital Readmission Risk."""
    clinical_subject_id: str
    lace_score: int = Field(..., ge=0, le=20)
    readmission_probability_30d: float = Field(..., ge=0.0, le=1.0)
    risk_tier: ReadmissionRiskTier
    length_of_stay_days: int
    is_emergent_admission: bool
    charlson_comorbidity_score: int
    prior_ed_visits_6m: int
    key_risk_drivers: list[str] = Field(default_factory=list)
    suggested_transitional_care_bundle: list[str] = Field(default_factory=list)


class CareGapMeasure(BaseModel):
    """HEDIS / Clinical Quality Measure Care Gap."""
    gap_id: str = Field(default_factory=lambda: f"gap_{uuid4().hex[:8]}")
    clinical_subject_id: str
    measure_id: str  # e.g., "HEDIS-CDC-A1C", "HEDIS-KED-NEPHRO", "HEDIS-CBP-BP"
    measure_name: str
    status: str = "OVERDUE"  # OVERDUE, DUE_SOON, COMPLIANT
    days_overdue: int
    recommended_clinical_outreach: str
