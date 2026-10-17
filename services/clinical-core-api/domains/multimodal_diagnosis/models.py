"""
MediScan Enterprise — Multimodal Diagnostic Domain Models
=========================================================
Pydantic v2 schemas for Cross-Modal Clinical Fusion, Conformal Prediction,
SHAP Explainability, 12-Lead ECG Analysis, Visual Saliency, and Audit Ledger.
"""

from enum import Enum
from typing import Any, List, Optional, Tuple
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class BiologicalSex(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class ModalityType(str, Enum):
    LAB = "LAB"
    VITAL = "VITAL"
    SYMPTOM = "SYMPTOM"
    ECG_12_LEAD = "ECG_12_LEAD"
    DICOM_CXR = "DICOM_CXR"
    DICOM_CT = "DICOM_CT"
    DERM_PHOTO = "DERM_PHOTO"
    FUNDUS = "FUNDUS"
    HPI = "HPI"


class PatientContext(BaseModel):
    age_years: int = Field(..., ge=0, le=130)
    biological_sex: str = Field(default="MALE", description="MALE | FEMALE | OTHER")
    weight_kg: float | None = Field(default=None, ge=1.0, le=500.0)
    pregnancy_status: str = Field(default="NOT_APPLICABLE")
    latest_egfr_ml_min: float | None = Field(default=None, ge=0.0)
    active_medications_rxnorm: list[str] = Field(default_factory=list)
    known_allergies_snomed: list[str] = Field(default_factory=list)


class ClinicalEntityInput(BaseModel):
    snomed_code: str
    term: str
    assertion: str = Field(default="PRESENT", description="PRESENT | ABSENT | HISTORICAL | FAMILY_HISTORY | HYPOTHETICAL")
    onset_hours: float | None = None
    source: str | None = None


class VitalLabInput(BaseModel):
    loinc_code: str
    name: str
    value: float
    unit: str
    reference_high: float | None = None
    reference_low: float | None = None


class ImagingWaveformRef(BaseModel):
    modality: str = Field(..., description="ECG_12_LEAD | DICOM_CXR | DICOM_CT | DERM_PHOTO | FUNDUS")
    s3_uri: str | None = None
    raw_bytes_base64: str | None = None
    waveform_samples: list[float] | list[list[float]] | None = None


class MultimodalAssessmentRequest(BaseModel):
    clinical_subject_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID | None = None
    patient_context: PatientContext
    extracted_clinical_entities: list[ClinicalEntityInput] = Field(default_factory=list)
    structured_vitals_labs: list[VitalLabInput] = Field(default_factory=list)
    imaging_waveform_refs: list[ImagingWaveformRef] = Field(default_factory=list)


class SHAPFeatureAttribution(BaseModel):
    feature_name: str
    modality: str = Field(..., description="LAB | VITAL | SYMPTOM | ECG | IMAGING | DEMOGRAPHIC")
    value: Any
    attribution_score: float = Field(..., description="SHAP attribution shift in log-odds or probability")
    direction: str = Field(..., description="INCREASES_RISK | DECREASES_RISK")


class ConformalDifferentialPrediction(BaseModel):
    rank: int = Field(..., ge=1)
    condition: str
    icd11_code: str
    snomed_code: str
    calibrated_probability: float = Field(..., ge=0.0, le=1.0)
    conformal_95_interval: list[float] = Field(..., min_length=2, max_length=2, description="[lower, upper]")
    shap_attributions: list[SHAPFeatureAttribution] = Field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)
    rule_out_workup: list[str] = Field(default_factory=list)


class ECGAnalysisResult(BaseModel):
    heart_rate_bpm: float = Field(..., ge=0.0)
    pr_interval_ms: float = Field(..., ge=0.0)
    qrs_duration_ms: float = Field(..., ge=0.0)
    qtc_interval_ms: float = Field(..., ge=0.0)
    st_elevation_leads: list[str] = Field(default_factory=list)
    st_depression_leads: list[str] = Field(default_factory=list)
    rhythm_classification: str
    stemi_criteria_met: bool = False
    clinical_interpretation: str


class VisualSaliencyResult(BaseModel):
    modality: str
    finding: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    heatmap_overlay_base64: str
    saliency_uri: str | None = None


class TriageAssessment(BaseModel):
    esi_level: int = Field(..., ge=1, le=5)
    news2_score: int = Field(..., ge=0, le=20)
    severity_tier: str = Field(..., description="CRITICAL | EMERGENT | URGENT | NON_URGENT")
    clinical_rationale: str
    immediate_protocol: str | None = None


class ProposedOrder(BaseModel):
    rxnorm_code: str
    medication: str
    recommended_dose: str
    safety_verification: str


class BlockedContraindication(BaseModel):
    medication: str
    reason: str
    severity: str = "HARD_STOP"


class PharmacologyCDSRecommendations(BaseModel):
    guideline_source: str
    proposed_orders: list[ProposedOrder] = Field(default_factory=list)
    blocked_contraindications: list[BlockedContraindication] = Field(default_factory=list)


class MultimodalAssessmentResponse(BaseModel):
    inference_id: UUID = Field(default_factory=uuid4)
    encounter_id: UUID = Field(default_factory=uuid4)
    model_ensemble_version: str = "mediscan-multimodal-v4.2.0"
    regulatory_classification: str = "CLINICAL_DECISION_SUPPORT_NON_AUTONOMOUS"
    abstained_ood: bool = Field(default=False, description="True if Out-of-Distribution or ambiguous input triggers abstention")
    ood_reason: str | None = None
    triage_assessment: TriageAssessment
    conformal_differential_diagnosis: list[ConformalDifferentialPrediction] = Field(default_factory=list)
    ecg_analysis: ECGAnalysisResult | None = None
    visual_saliency: VisualSaliencyResult | None = None
    pharmacology_cds_recommendations: PharmacologyCDSRecommendations
    audit_ledger_entry: dict[str, Any] | None = None
    requires_clinician_signature: bool = True
