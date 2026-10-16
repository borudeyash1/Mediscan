"""
Pydantic Schemas and Domain Types for CDS Pharmacology & Triage Engine
======================================================================
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ClinicalAssertion(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    NEGATED = "NEGATED"              # Alias for ABSENT
    HISTORICAL = "HISTORICAL"
    FAMILY_HISTORY = "FAMILY_HISTORY"
    HYPOTHETICAL = "HYPOTHETICAL"


class TriageSeverityLevel(str, Enum):
    RESUSCITATION = "RESUSCITATION"  # ESI 1 / Immediate life threat
    EMERGENT = "EMERGENT"            # ESI 2 / High risk, severe
    URGENT = "URGENT"                # ESI 3 / Moderate
    LESS_URGENT = "LESS_URGENT"      # ESI 4 / Mild
    NON_URGENT = "NON_URGENT"        # ESI 5 / Minimal


class ClinicalEntity(BaseModel):
    term: str = Field(..., description="Extracted clinical symptom, sign, or condition")
    assertion: str = Field(
        default="PRESENT",
        description="PRESENT | ABSENT | NEGATED | HISTORICAL | FAMILY_HISTORY | HYPOTHETICAL",
    )
    snomed_code: Optional[str] = None
    temporality: Optional[str] = "ACUTE"
    source_span: Optional[List[int]] = None

    def is_present(self) -> bool:
        normalized = self.assertion.strip().upper()
        return normalized in ("PRESENT", "CONFIRMED", "ACTIVE")

    def is_negated(self) -> bool:
        normalized = self.assertion.strip().upper()
        return normalized in ("ABSENT", "NEGATED", "DENIED", "RULED_OUT", "NOT_PRESENT")

    def is_historical_or_family(self) -> bool:
        normalized = self.assertion.strip().upper()
        return normalized in ("HISTORICAL", "PAST", "FAMILY_HISTORY", "HYPOTHETICAL")


class StructuredLabObservation(BaseModel):
    loinc_code: str
    test_name: str
    value: float
    unit: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    is_critical: bool = False
    critical_direction: Optional[str] = None  # CRITICAL_LOW | CRITICAL_HIGH | NORMAL


class VitalSignsPayload(BaseModel):
    heart_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature_celsius: Optional[float] = None
    spo2_percent: Optional[float] = None
    supplemental_oxygen: bool = False
    hypercapnic_respiratory_failure: bool = False
    consciousness_avpu: str = "ALERT"


class TriageEvaluationInput(BaseModel):
    clinical_subject_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    chief_complaint: Optional[str] = None
    clinical_entities: List[ClinicalEntity] = Field(default_factory=list)
    vital_signs: Optional[VitalSignsPayload] = None
    lab_observations: List[StructuredLabObservation] = Field(default_factory=list)
    age_years: Optional[int] = None
    biological_sex: Optional[str] = None


class TriageEvaluationOutput(BaseModel):
    evaluation_id: UUID = Field(default_factory=uuid4)
    severity_level: TriageSeverityLevel
    is_critical: bool
    news2_total: int
    news2_category: str
    esi_level: int
    qsofa_score: int
    is_high_risk_sepsis: bool
    triggering_factors: List[str] = Field(default_factory=list)
    suppressed_factors: List[str] = Field(
        default_factory=list,
        description="Entities with ABSENT, FAMILY_HISTORY or HISTORICAL assertions that were safely de-escalated",
    )
    recommended_clinical_action: str
    component_breakdown: Dict[str, Any] = Field(default_factory=dict)


# ── Pharmacology Gatekeeper Models ─────────────────────────────

class SafetyVerdict(str, Enum):
    PASSED_ALL_CHECKS = "PASSED_ALL_CHECKS"
    REQUIRES_ADJUSTMENT = "REQUIRES_ADJUSTMENT"
    HARD_STOP_CONTRAINDICATION = "HARD_STOP_CONTRAINDICATION"


class DDISeverity(str, Enum):
    CONTRAINDICATED = "CONTRAINDICATED"
    MAJOR = "MAJOR"
    MODERATE = "MODERATE"
    MINOR = "MINOR"


class DDIAlert(BaseModel):
    interacting_drug_rxnorm: str
    interacting_drug_name: str
    severity: DDISeverity
    mechanism: str
    clinical_management: str


class AllergyAlert(BaseModel):
    allergen_name: str
    allergen_snomed: str
    cross_reactivity_class: str
    reaction_risk: str
    is_hard_stop: bool = True
    clinical_rationale: str


class RenalAdjustmentAlert(BaseModel):
    drug_name: str
    egfr_value: float
    egfr_cutoff: float
    is_hard_stop: bool
    recommended_action: str
    dosing_guidance: str


class DiseaseContraindicationAlert(BaseModel):
    disease_name: str
    disease_icd11_or_snomed: str
    drug_name: str
    severity: str = "HARD_STOP_CONTRAINDICATION"
    clinical_hazard: str


class PediatricCeilingCheck(BaseModel):
    weight_kg: float
    calculated_dose_mg: float
    final_dose_mg: float
    adult_max_ceiling_mg: float
    is_capped: bool
    dosing_basis: str


class MedicationEvaluationRequest(BaseModel):
    proposed_drug_name: str
    proposed_rxnorm_code: Optional[str] = None
    proposed_dosage: Optional[str] = None
    proposed_route: str = "PO"
    dose_mg_per_kg: Optional[float] = None
    adult_max_single_dose_mg: Optional[float] = None
    patient_age_years: Optional[int] = None
    patient_weight_kg: Optional[float] = None
    patient_height_cm: Optional[float] = None
    patient_biological_sex: Optional[str] = None
    patient_egfr: Optional[float] = None
    patient_serum_creatinine: Optional[float] = None
    active_medications: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of active medications with name and/or rxnorm_cui",
    )
    known_allergies: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of documented allergies with name and/or snomed_id",
    )
    diagnosed_diseases: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of active diagnoses with name and/or icd11/snomed_id",
    )


class MedicationEvaluationResponse(BaseModel):
    cds_eval_id: UUID = Field(default_factory=uuid4)
    proposed_drug_name: str
    proposed_rxnorm_code: Optional[str] = None
    safety_verdict: SafetyVerdict
    hard_stop_reasons: List[str] = Field(default_factory=list)
    adjustment_reasons: List[str] = Field(default_factory=list)
    ddi_alerts: List[DDIAlert] = Field(default_factory=list)
    allergy_alerts: List[AllergyAlert] = Field(default_factory=list)
    renal_alerts: List[RenalAdjustmentAlert] = Field(default_factory=list)
    disease_contraindications: List[DiseaseContraindicationAlert] = Field(default_factory=list)
    pediatric_ceiling: Optional[PediatricCeilingCheck] = None
    clinician_action_required: str
