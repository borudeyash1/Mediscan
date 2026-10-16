"""
Clinical Decision Support & Pharmacology Router
=================================================
The deterministic safety gatekeeper. Replaces drug_recommender.py.
Performs: DDI checking, drug-allergy cross-ref, renal/hepatic dosing,
eGFR-based contraindication evaluation, NEWS2/ESI triage scoring.
Integrates with Neo4j (RxNorm/SNOMED-CT) knowledge graph.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Ensure root workspace is in sys.path
_workspace_root = Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents) >= 5 else Path(__file__).resolve().parents[3]
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from libs.clinical_calculators.calculators import (
    BiologicalSex,
    calculate_ckd_epi_2021,
    calculate_cockcroft_gault,
    calculate_esi_v4,
    calculate_mosteller_bsa,
    calculate_news2,
    calculate_pediatric_dose_with_adult_ceiling,
    calculate_qsofa,
)
from services.clinical_core_api.domains.cds_pharmacology.gatekeeper import PharmacologyGatekeeper
from services.clinical_core_api.domains.cds_pharmacology.models import (
    ClinicalEntity,
    MedicationEvaluationRequest,
    StructuredLabObservation,
    TriageEvaluationInput,
    TriageEvaluationOutput,
    VitalSignsPayload,
)
from services.clinical_core_api.domains.cds_pharmacology.triage_engine import AssertionAwareTriageEngine

router = APIRouter()

_gatekeeper = PharmacologyGatekeeper()
_triage_engine = AssertionAwareTriageEngine()


# ── Request/Response Models ──────────────────────────────────

class MedicationOrderRequest(BaseModel):
    encounter_id: Optional[UUID] = None
    clinical_subject_id: Optional[UUID] = None
    proposed_rxnorm_code: Optional[str] = None
    proposed_drug_name: str
    proposed_dosage: Optional[str] = None
    proposed_route: str = "PO"
    dose_mg_per_kg: Optional[float] = None
    adult_max_single_dose_mg: Optional[float] = None
    patient_egfr: Optional[float] = None
    patient_serum_creatinine: Optional[float] = None
    patient_weight_kg: Optional[float] = None
    patient_height_cm: Optional[float] = None
    patient_age_years: Optional[int] = None
    patient_biological_sex: Optional[str] = None
    patient_pregnancy_status: str = "NOT_APPLICABLE"
    active_medications_rxnorm: List[str] = Field(default_factory=list)
    active_medications_names: List[str] = Field(default_factory=list)
    known_allergies_snomed: List[str] = Field(default_factory=list)
    known_allergies_names: List[str] = Field(default_factory=list)
    diagnosed_diseases: List[Dict[str, str]] = Field(default_factory=list)


class DDIAlertModel(BaseModel):
    interacting_drug_rxnorm: str
    interacting_drug_name: str
    severity: str = Field(..., description="CONTRAINDICATED | MAJOR | MODERATE | MINOR")
    mechanism: str
    clinical_management: str


class RenalAdjustmentModel(BaseModel):
    drug_name: str
    egfr_value: float
    egfr_cutoff: float
    is_hard_stop: bool
    recommended_action: str
    dosing_guidance: str


class MedicationSafetyResponse(BaseModel):
    cds_eval_id: UUID
    rxnorm_code: Optional[str] = None
    drug_name: str
    safety_verdict: str = Field(
        ..., description="PASSED_ALL_CHECKS | REQUIRES_ADJUSTMENT | HARD_STOP_CONTRAINDICATION"
    )
    hard_stop_reasons: List[str] = Field(default_factory=list)
    adjustment_reasons: List[str] = Field(default_factory=list)
    ddi_alerts: List[DDIAlertModel] = Field(default_factory=list)
    allergy_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    renal_adjustments: List[RenalAdjustmentModel] = Field(default_factory=list)
    disease_contraindications: List[Dict[str, Any]] = Field(default_factory=list)
    pediatric_dose_ceiling_check: Optional[Dict[str, Any]] = None
    clinician_action_required: str


class TriageScoreRequest(BaseModel):
    clinical_subject_id: Optional[UUID] = None
    heart_rate: Optional[int] = None
    systolic_bp: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature_celsius: Optional[float] = None
    spo2_percent: Optional[float] = None
    consciousness_avpu: Optional[str] = Field(None, description="ALERT | VOICE | PAIN | UNRESPONSIVE")
    supplemental_oxygen: bool = False
    hypercapnic_respiratory_failure: bool = False


class TriageScoreResponse(BaseModel):
    news2_score: int
    news2_category: str = Field(..., description="LOW | LOW_MEDIUM | MEDIUM | HIGH")
    is_critical: bool
    esi_level: int = Field(..., ge=1, le=5)
    component_scores: Dict[str, int]
    recommended_response: str


# ── Endpoints ─────────────────────────────────────────────────

@router.post(
    "/medication-safety-check",
    response_model=MedicationSafetyResponse,
    summary="Deterministic Medication Safety Evaluation (DDI, Allergy, Renal/Hepatic)",
)
async def medication_safety_check(request: MedicationOrderRequest):
    """
    Runs deterministic pharmacology checks against the knowledge graph & rules:
    - Drug-Drug Interactions (DDIs)
    - Drug-Allergy cross-reference (e.g. Penicillin -> Amox-Clav)
    - eGFR-based renal dose adjustment or contraindication (e.g. Metformin < 30)
    - Disease-drug contraindications (e.g. Dengue -> NSAIDs)
    - Pediatric weight/BSA dosing ceiling checks
    """
    # Build active medications list
    active_meds: list[dict[str, str]] = []
    for name in request.active_medications_names:
        active_meds.append({"name": name, "rxnorm_cui": ""})
    for rx in request.active_medications_rxnorm:
        active_meds.append({"name": rx, "rxnorm_cui": rx})

    # Build known allergies list
    allergies: list[dict[str, str]] = []
    for name in request.known_allergies_names:
        allergies.append({"name": name, "snomed_id": ""})
    for snomed in request.known_allergies_snomed:
        allergies.append({"name": snomed, "snomed_id": snomed})

    eval_req = MedicationEvaluationRequest(
        proposed_drug_name=request.proposed_drug_name,
        proposed_rxnorm_code=request.proposed_rxnorm_code,
        proposed_dosage=request.proposed_dosage,
        proposed_route=request.proposed_route,
        dose_mg_per_kg=request.dose_mg_per_kg,
        adult_max_single_dose_mg=request.adult_max_single_dose_mg,
        patient_age_years=request.patient_age_years,
        patient_weight_kg=request.patient_weight_kg,
        patient_height_cm=request.patient_height_cm,
        patient_biological_sex=request.patient_biological_sex,
        patient_egfr=request.patient_egfr,
        patient_serum_creatinine=request.patient_serum_creatinine,
        active_medications=active_meds,
        known_allergies=allergies,
        diagnosed_diseases=request.diagnosed_diseases,
    )

    eval_resp = _gatekeeper.evaluate_safety(eval_req)

    return MedicationSafetyResponse(
        cds_eval_id=eval_resp.cds_eval_id,
        rxnorm_code=eval_resp.proposed_rxnorm_code,
        drug_name=eval_resp.proposed_drug_name,
        safety_verdict=eval_resp.safety_verdict.value,
        hard_stop_reasons=eval_resp.hard_stop_reasons,
        adjustment_reasons=eval_resp.adjustment_reasons,
        ddi_alerts=[
            DDIAlertModel(
                interacting_drug_rxnorm=a.interacting_drug_rxnorm,
                interacting_drug_name=a.interacting_drug_name,
                severity=a.severity.value,
                mechanism=a.mechanism,
                clinical_management=a.clinical_management,
            )
            for a in eval_resp.ddi_alerts
        ],
        allergy_alerts=[a.model_dump() for a in eval_resp.allergy_alerts],
        renal_adjustments=[
            RenalAdjustmentModel(
                drug_name=r.drug_name,
                egfr_value=r.egfr_value,
                egfr_cutoff=r.egfr_cutoff,
                is_hard_stop=r.is_hard_stop,
                recommended_action=r.recommended_action,
                dosing_guidance=r.dosing_guidance,
            )
            for r in eval_resp.renal_alerts
        ],
        disease_contraindications=[d.model_dump() for d in eval_resp.disease_contraindications],
        pediatric_dose_ceiling_check=eval_resp.pediatric_ceiling.model_dump() if eval_resp.pediatric_ceiling else None,
        clinician_action_required=eval_resp.clinician_action_required,
    )


@router.post(
    "/triage-score",
    response_model=TriageScoreResponse,
    summary="Calculate NEWS2 & ESI Triage Scores",
)
async def calculate_triage_score(request: TriageScoreRequest):
    """
    Computes validated clinical triage scores:
    - NEWS2 (National Early Warning Score 2) Scale 1 & Scale 2
    - ESI (Emergency Severity Index v4)
    """
    news2 = calculate_news2(
        respiratory_rate=request.respiratory_rate,
        spo2_percent=request.spo2_percent,
        supplemental_oxygen=request.supplemental_oxygen,
        hypercapnic_respiratory_failure=request.hypercapnic_respiratory_failure,
        systolic_bp=request.systolic_bp,
        heart_rate=request.heart_rate,
        consciousness_avpu=request.consciousness_avpu or "ALERT",
        temperature_celsius=request.temperature_celsius,
    )

    esi = calculate_esi_v4(
        requires_immediate_lifesaving=(news2.total_score >= 11),
        is_high_risk_or_confused_or_severe_pain=(news2.total_score >= 7),
        expected_resources=2 if news2.total_score >= 5 else 1,
        vital_signs_danger_zone=(news2.total_score >= 5),
    )

    return TriageScoreResponse(
        news2_score=news2.total_score,
        news2_category=news2.category.value,
        is_critical=news2.is_critical,
        esi_level=int(esi.level.value),
        component_scores=news2.component_scores,
        recommended_response=news2.recommended_clinical_response,
    )


@router.post(
    "/assertion-triage",
    response_model=TriageEvaluationOutput,
    summary="Assertion-Aware Multi-Axial Triage Evaluator",
)
async def evaluate_assertion_triage(request: TriageEvaluationInput):
    """
    Evaluates clinical entities with assertion context (PRESENT vs ABSENT vs FAMILY_HISTORY)
    alongside structured LOINC lab thresholds and physiological vital signs.
    """
    return _triage_engine.evaluate_triage(request)


@router.post(
    "/egfr-calculate",
    summary="Calculate CKD-EPI 2021 eGFR & Cockcroft-Gault CrCl",
)
async def calculate_egfr(
    serum_creatinine_mg_dl: float,
    age_years: int,
    biological_sex: str,
    weight_kg: Optional[float] = None,
):
    """
    Calculates CKD-EPI 2021 (race-free) eGFR and Cockcroft-Gault CrCl from serum creatinine.
    """
    egfr_res = calculate_ckd_epi_2021(
        serum_creatinine_mg_dl=serum_creatinine_mg_dl,
        age_years=age_years,
        biological_sex=biological_sex,
    )

    response: dict[str, Any] = {
        "egfr_ml_min_1_73m2": egfr_res.egfr_ml_min_1_73m2,
        "equation": egfr_res.equation,
        "ckd_stage": egfr_res.ckd_stage,
        "stage_description": egfr_res.stage_description,
        "is_kidney_failure": egfr_res.is_kidney_failure,
        "requires_dose_adjustment": egfr_res.requires_dose_adjustment,
        "contraindicated_metformin": egfr_res.contraindicated_metformin,
        "inputs": {
            "serum_creatinine_mg_dl": serum_creatinine_mg_dl,
            "age_years": age_years,
            "biological_sex": biological_sex,
        },
    }

    if weight_kg is not None and weight_kg > 0:
        crcl_res = calculate_cockcroft_gault(
            serum_creatinine_mg_dl=serum_creatinine_mg_dl,
            age_years=age_years,
            weight_kg=weight_kg,
            biological_sex=biological_sex,
        )
        response["cockcroft_gault_crcl_ml_min"] = crcl_res.crcl_ml_min

    return response


@router.post(
    "/pediatric-dosing",
    summary="Calculate Pediatric Dose with Adult Ceiling Hard-Stop",
)
async def calculate_pediatric_dosing(
    weight_kg: float,
    dose_mg_per_kg: float,
    adult_max_single_dose_mg: float,
    height_cm: Optional[float] = None,
    dose_mg_per_m2: Optional[float] = None,
):
    """
    Computes weight-based or BSA-based pediatric dosing capped strictly by adult maximum ceiling.
    """
    res = calculate_pediatric_dose_with_adult_ceiling(
        weight_kg=weight_kg,
        dose_mg_per_kg=dose_mg_per_kg,
        adult_max_single_dose_mg=adult_max_single_dose_mg,
        height_cm=height_cm,
        dose_mg_per_m2=dose_mg_per_m2,
    )
    return {
        "calculated_dose_mg": res.calculated_dose_mg,
        "final_dose_mg": res.final_dose_mg,
        "adult_max_ceiling_mg": res.adult_max_ceiling_mg,
        "is_capped_by_adult_ceiling": res.is_capped_by_adult_ceiling,
        "dosing_basis": res.dosing_basis,
        "weight_kg": res.weight_kg,
        "warnings": res.warnings,
    }
