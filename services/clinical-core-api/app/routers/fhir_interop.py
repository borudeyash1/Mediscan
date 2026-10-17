"""
FHIR R4 Interoperability Hub, CDS Hooks & ABDM Gateway Router
==============================================================
Handles:
  - Compliant HL7 FHIR R4 REST endpoints (Bundle, Patient/$everything, Observation, MedicationRequest)
  - HL7 CDS Hooks (order-sign, order-select with sub-500ms safety cards)
  - HL7v2 Pipe/Bar Message Ingestion (ORU^R01, ADT^A01)
  - India Ayushman Bharat Digital Mission (ABDM) ABHA ID Verification
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from domains.hospital_interop.fhir_store import fhir_store
from domains.hospital_interop.cds_hooks_engine import cds_hooks_engine
from domains.hospital_interop.hl7v2_parser import hl7v2_parser
from domains.hospital_interop.abdm_adapter import (
    abdm_adapter,
    ABHAVerificationRequest,
    ABHAVerificationResponse,
)

router = APIRouter()


# ── Models ────────────────────────────────────────────────────

class FHIRBundleRequest(BaseModel):
    resourceType: str = "Bundle"
    type: str = "transaction"
    entry: list[dict[str, Any]] = []


class CDSHookRequest(BaseModel):
    hook: str = Field(..., description="patient-view | order-select | order-sign")
    hookInstance: str
    context: dict[str, Any]
    prefetch: Optional[dict[str, Any]] = None


class CDSCard(BaseModel):
    uuid: Optional[str] = None
    summary: str
    detail: Optional[str] = None
    indicator: str = Field(..., description="info | warning | critical")
    source: dict[str, Any]
    suggestions: list[dict[str, Any]] = []


class CDSHookResponse(BaseModel):
    cards: list[CDSCard] = []


class HL7MessageRequest(BaseModel):
    raw_message: str = Field(..., description="Pipe/bar delimited HL7v2 message string")


# ── FHIR R4 REST Endpoints ───────────────────────────────────

@router.post(
    "/Bundle",
    summary="FHIR R4 Transaction Bundle Ingestion",
)
async def ingest_fhir_bundle(bundle: FHIRBundleRequest):
    """
    Ingests an HL7 FHIR R4 Transaction Bundle containing Patient, Encounter,
    Observation, Condition, and MedicationRequest resources.
    Returns 201 Created transaction-response.
    """
    return fhir_store.process_bundle(bundle.model_dump())


@router.get(
    "/Patient/{patient_id}/$everything",
    summary="Retrieve Complete Longitudinal Patient Record",
)
async def patient_everything(patient_id: str):
    """Returns the complete longitudinal patient record as a FHIR searchset Bundle."""
    return fhir_store.get_patient_everything(str(patient_id))


@router.get(
    "/Patient/{patient_id}",
    summary="Read FHIR Patient Resource",
)
async def read_patient(patient_id: str):
    """Retrieves a single FHIR R4 Patient resource."""
    bundle = fhir_store.get_patient_everything(str(patient_id))
    for entry in bundle.get("entry", []):
        if entry.get("resource", {}).get("resourceType") == "Patient":
            return entry["resource"]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")


@router.get(
    "/Observation",
    summary="Search FHIR Observations",
)
async def search_observations(
    patient: Optional[str] = None,
    code: Optional[str] = None,
    _count: int = 50,
):
    """Searches FHIR R4 Observation resources by patient and/or LOINC code."""
    obs_list = fhir_store.search_observations(patient_id=patient, code=code)
    entries = [{"resource": o} for o in obs_list[:_count]]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": entries,
    }


@router.get(
    "/MedicationRequest",
    summary="Search FHIR Medication Requests",
)
async def search_medication_requests(patient: Optional[str] = None):
    """Searches active FHIR MedicationRequest resources."""
    bundle = fhir_store.get_patient_everything(str(patient)) if patient else {"entry": []}
    meds = [e for e in bundle.get("entry", []) if e.get("resource", {}).get("resourceType") == "MedicationRequest"]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(meds),
        "entry": meds,
    }


# ── CDS Hooks Endpoints ──────────────────────────────────────

@router.post(
    "/cds-services/mediscan-order-sign-safety",
    response_model=CDSHookResponse,
    summary="CDS Hooks Order-Sign Safety Evaluation",
)
async def cds_hook_order_sign(request: CDSHookRequest):
    """
    Invoked synchronously by Epic/Cerner before a prescription is signed.
    Returns CDS Cards containing deterministic contraindications and renal dosing adjustments.
    Responds strictly in <500ms SLA.
    """
    return cds_hooks_engine.evaluate_order_sign(request.model_dump())


@router.post(
    "/cds-services/mediscan-order-select-safety",
    response_model=CDSHookResponse,
    summary="CDS Hooks Order-Select Safety Evaluation",
)
async def cds_hook_order_select(request: CDSHookRequest):
    """Invoked when clinician selects a medication in the EHR order entry form."""
    return cds_hooks_engine.evaluate_order_sign(request.model_dump())


@router.get(
    "/cds-services",
    summary="CDS Hooks Service Discovery",
)
async def cds_service_discovery():
    """Returns the CDS Hooks service discovery document."""
    return {
        "services": [
            {
                "hook": "order-sign",
                "title": "MediScan Order Sign Safety Check",
                "description": "Real-time DDI, allergy, and renal/hepatic dosing safety evaluation",
                "id": "mediscan-order-sign-safety",
                "prefetch": {
                    "patient": "Patient/{{context.patientId}}",
                    "medications": "MedicationRequest?patient={{context.patientId}}&status=active",
                    "allergies": "AllergyIntolerance?patient={{context.patientId}}",
                    "conditions": "Condition?patient={{context.patientId}}",
                    "labs": "Observation?patient={{context.patientId}}&category=laboratory&_sort=-date&_count=20",
                },
            },
            {
                "hook": "order-select",
                "title": "MediScan Order Select Safety Check",
                "description": "Real-time drug selection warning and alternative guidance",
                "id": "mediscan-order-select-safety",
            },
        ]
    }


# ── HL7v2 & ABDM Endpoints ───────────────────────────────────

@router.post(
    "/api/v2/hl7/parse-message",
    summary="Parse Raw HL7v2 Pipe/Bar Message (ORU^R01 / ADT^A01)",
)
async def parse_hl7_message(payload: HL7MessageRequest):
    """Parses raw HL7v2 pipe-delimited message into structured objects and FHIR R4 resources."""
    try:
        return hl7v2_parser.parse_message(payload.raw_message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"HL7v2 Parsing Error: {str(e)}",
        )


@router.post(
    "/api/v2/abdm/verify-abha",
    response_model=ABHAVerificationResponse,
    summary="India ABDM ABHA ID Verification",
)
async def verify_abdm_abha(payload: ABHAVerificationRequest):
    """
    Verifies 14-digit ABHA Numbers and ABHA Addresses (@abdm / @sbx)
    against the Ayushman Bharat Digital Mission National Health Stack.
    """
    return abdm_adapter.verify_abha(payload.abha_identifier)
