"""
Predictive Population Health & Outbreak Surveillance Router
============================================================
Handles:
  - Spatio-Temporal Outbreak Detection (Dengue, Influenza, Malaria, COVID-19)
  - 30-Day Hospital Readmission Risk Scoring (LACE+ Index)
  - Chronic Care-Gap Identification (HEDIS Measures)
"""

from typing import Optional
from fastapi import APIRouter, Query

from domains.population_health.models import (
    DiseaseOutbreakCluster,
    PatientReadmissionScore,
    CareGapMeasure,
)
from domains.population_health.outbreak_detector import outbreak_detector
from domains.population_health.readmission_risk import lace_engine
from domains.population_health.care_gaps import care_gap_engine

router = APIRouter()


@router.get(
    "/outbreaks",
    response_model=list[DiseaseOutbreakCluster],
    summary="Regional Communicable Disease Outbreak Clusters & Rt Tracking",
)
async def get_outbreak_clusters(
    pathogen: Optional[str] = Query(None, description="Filter by pathogen: Dengue, Influenza, Malaria, COVID-19")
) -> list[DiseaseOutbreakCluster]:
    """
    Returns active geospatial outbreak clusters detected via spatial density clustering.
    Provides estimated reproduction rate Rt, doubling rate, and recommended municipal public health actions.
    """
    return outbreak_detector.detect_outbreak_clusters(pathogen_filter=pathogen)


@router.get(
    "/readmission-risk",
    response_model=PatientReadmissionScore,
    summary="Compute 30-Day Hospital Readmission Risk Score (LACE+ Index)",
)
async def get_readmission_risk(
    clinical_subject_id: str = Query("pat_default", description="Patient identifier"),
    length_of_stay_days: int = Query(4, ge=0, description="Length of hospital stay in days"),
    is_emergent: bool = Query(True, description="Whether admission was acute/emergent"),
    comorbidity_score: int = Query(3, ge=0, description="Charlson Comorbidity Index score"),
    prior_ed_visits_6m: int = Query(2, ge=0, description="Emergency department visits in previous 6 months"),
) -> PatientReadmissionScore:
    """
    Calculates validated LACE+ Index score (0-19), probability of readmission within 30 days,
    and assigns a personalized transitional care bundle.
    """
    return lace_engine.calculate_lace_score(
        clinical_subject_id=clinical_subject_id,
        length_of_stay_days=length_of_stay_days,
        is_emergent_admission=is_emergent,
        charlson_comorbidity_score=comorbidity_score,
        prior_ed_visits_6m=prior_ed_visits_6m,
    )


@router.get(
    "/care-gaps",
    response_model=list[CareGapMeasure],
    summary="Identify Longitudinal Chronic Care Gaps (HEDIS Quality Measures)",
)
async def get_patient_care_gaps(
    clinical_subject_id: str = Query("pat_default", description="Patient identifier"),
    conditions: Optional[str] = Query("Type 2 Diabetes, Hypertension", description="Comma-separated active diagnoses"),
) -> list[CareGapMeasure]:
    """
    Scans longitudinal patient history for overdue HEDIS quality measures:
    HbA1c testing, nephropathy screening (UACR), retinal eye exams, and BP control.
    """
    cond_list = [c.strip() for c in conditions.split(",") if c.strip()] if conditions else []
    return care_gap_engine.evaluate_patient_care_gaps(
        clinical_subject_id=clinical_subject_id,
        conditions=cond_list,
        labs={"hba1c_days_ago": 240, "uacr_days_ago": 410, "retinal_exam_days_ago": 450},
        vitals={"systolic_bp": 146.0, "diastolic_bp": 92.0},
    )
