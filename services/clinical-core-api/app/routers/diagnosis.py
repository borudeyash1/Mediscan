"""
Multimodal Diagnostic Orchestrator Router
==========================================
Handles: Cross-modal fusion diagnosis across text, labs, imaging, and waveforms.
Computes calibrated probabilities with conformal prediction intervals,
SHAP feature attributions, NEWS2/ESI triage, and CDS pharmacology gating.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from domains.multimodal_diagnosis.models import (
    ClinicalEntityInput,
    ConformalDifferentialPrediction,
    ECGAnalysisResult,
    ImagingWaveformRef,
    MultimodalAssessmentRequest,
    MultimodalAssessmentResponse,
    PatientContext,
    PharmacologyCDSRecommendations,
    SHAPFeatureAttribution,
    TriageAssessment,
    VisualSaliencyResult,
    VitalLabInput,
)
from domains.multimodal_diagnosis.orchestrator import MultimodalDiagnosticOrchestrator
from domains.multimodal_diagnosis.audit_ledger import ImmutableAuditLedger

router = APIRouter()


# ── Endpoints ─────────────────────────────────────────────────

@router.post(
    "/encounters/{encounter_id}/multimodal-assess",
    response_model=MultimodalAssessmentResponse,
    summary="Run Multimodal Diagnostic Assessment with Conformal Prediction",
)
@router.post(
    "/diagnosis/encounters/{encounter_id}/multimodal-assess",
    response_model=MultimodalAssessmentResponse,
    summary="Run Multimodal Diagnostic Assessment (Direct Alias)",
    include_in_schema=False,
)
async def multimodal_assessment(encounter_id: UUID, request: MultimodalAssessmentRequest):
    """
    Orchestrates specialist diagnostic foundation models across all input
    modalities (text, labs, imaging, waveforms). Returns calibrated differential
    diagnosis with conformal prediction intervals and explainability artifacts.
    """
    response = MultimodalDiagnosticOrchestrator.execute_assessment(
        encounter_id=encounter_id,
        request=request,
    )
    return response


@router.get(
    "/inferences/{inference_id}",
    summary="Retrieve Diagnostic Inference Audit Record",
)
@router.get(
    "/diagnosis/inferences/{inference_id}",
    summary="Retrieve Diagnostic Inference Audit Record (Direct Alias)",
    include_in_schema=False,
)
async def get_inference_record(inference_id: UUID):
    """Retrieves a stored AI diagnostic inference for audit trail review."""
    inf_str = str(inference_id)
    if inf_str in ImmutableAuditLedger._in_memory_inferences:
        return ImmutableAuditLedger._in_memory_inferences[inf_str]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inference record not found")


@router.post(
    "/inferences/{inference_id}/clinician-feedback",
    summary="Submit Clinician Feedback on AI Inference (RLHF)",
)
@router.post(
    "/diagnosis/inferences/{inference_id}/clinician-feedback",
    summary="Submit Clinician Feedback (Direct Alias)",
    include_in_schema=False,
)
async def submit_clinician_feedback(
    inference_id: UUID,
    disposition: str,
    feedback_notes: str | None = None,
):
    """
    Records clinician concurrence/rejection of AI inference output.
    Used for RLHF training data collection and regulatory post-market surveillance.
    """
    inf_str = str(inference_id)
    if inf_str in ImmutableAuditLedger._in_memory_inferences:
        ImmutableAuditLedger._in_memory_inferences[inf_str]["clinician_disposition"] = disposition
        ImmutableAuditLedger._in_memory_inferences[inf_str]["clinician_feedback_notes"] = feedback_notes
    return {"inference_id": inference_id, "disposition": disposition, "recorded": True}
