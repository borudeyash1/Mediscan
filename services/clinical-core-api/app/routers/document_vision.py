"""
Document Vision & Lab Report Parser Router
============================================
Handles: PDF/image ingestion, OCR, layout segmentation, table extraction,
and mapping outputs to structured LOINC codes and UCUM units.
Replaces the MVP's broken report_processor.py.
"""

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from domains.document_vision.models import (
    AbnormalFlag,
    AssertionType,
    ExtractedEntity,
    ExtractedLabResult,
    TemporalityType,
)
from domains.document_vision.pipeline import DocumentVisionPipeline

router = APIRouter()
pipeline = DocumentVisionPipeline()


# ── Request / Response Models ─────────────────────────────────

class ClinicalTextExtractionRequest(BaseModel):
    text: str = Field(..., description="Raw clinical text or progress note")
    source_filename: str = Field(default="clinical_note.txt")
    clinical_subject_id: str = Field(default="urn:uuid:patient-primary")


class DocumentExtractionResponse(BaseModel):
    document_id: UUID
    document_type: str = Field(
        ..., description="LAB_REPORT | PRESCRIPTION | CLINICAL_NOTE | DISCHARGE_SUMMARY | RADIOLOGY_REPORT | UNKNOWN"
    )
    source_filename: str
    extracted_text: str
    structured_results: list[ExtractedLabResult] = []
    entities: list[ExtractedEntity] = []
    fhir_observations: list[dict[str, Any]] = Field(
        default_factory=list, description="Generated FHIR R4 Observation resources"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0)


# ── Endpoints ─────────────────────────────────────────────────

@router.post(
    "/extract-lab-report",
    response_model=DocumentExtractionResponse,
    summary="Extract Structured Lab Results from PDF/Image",
)
async def extract_lab_report(
    file: UploadFile = File(..., description="PDF, JPEG, or PNG of lab report"),
    clinical_subject_id: UUID | None = None,
    tenant_id: UUID | None = None,
):
    """
    Ingests a lab report document (PDF, smartphone photo, scanned image).
    Performs de-skewing, layout segmentation, table extraction, and OCR,
    mapping outputs to structured LOINC codes and numeric UCUM units.
    """
    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/tiff",
        "text/plain",
        "application/octet-stream",
    ]
    filename = file.filename or "unknown.pdf"
    content_type = file.content_type or "application/octet-stream"

    if content_type not in allowed_types and not any(
        filename.lower().endswith(ext) for ext in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".txt"]
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}",
        )

    file_bytes = await file.read()
    subject_id = f"urn:uuid:{clinical_subject_id}" if clinical_subject_id else "urn:uuid:patient-primary"

    result = pipeline.process_document(
        content=file_bytes,
        filename=filename,
        mime_type=content_type,
        subject_id=subject_id,
    )

    return DocumentExtractionResponse(
        document_id=result.document_id,
        document_type=result.document_type,
        source_filename=result.source_filename,
        extracted_text=result.extracted_text,
        structured_results=result.structured_results,
        entities=result.entities,
        fhir_observations=result.fhir_observations,
        confidence_score=result.confidence_score,
    )


@router.post(
    "/extract-text-notes",
    response_model=DocumentExtractionResponse,
    summary="Extract Structured Labs and Entities from Raw Clinical Text",
)
async def extract_text_notes(
    request: ClinicalTextExtractionRequest,
):
    """
    Ingests raw clinical text (such as progress notes, HPI, or legacy reports).
    Preserves exact numeric values, extracts LOINC biomarkers, and resolves
    negation/temporality across all clinical concepts.
    """
    result = pipeline.process_document(
        content=request.text,
        filename=request.source_filename,
        mime_type="text/plain",
        subject_id=request.clinical_subject_id,
    )

    return DocumentExtractionResponse(
        document_id=result.document_id,
        document_type=result.document_type,
        source_filename=result.source_filename,
        extracted_text=result.extracted_text,
        structured_results=result.structured_results,
        entities=result.entities,
        fhir_observations=result.fhir_observations,
        confidence_score=result.confidence_score,
    )


@router.post(
    "/extract-prescription",
    response_model=DocumentExtractionResponse,
    summary="Extract Medication Orders from Handwritten/Printed Prescription",
)
async def extract_prescription(
    file: UploadFile = File(...),
    clinical_subject_id: UUID | None = None,
):
    """
    Specialized OCR pipeline for handwritten/printed prescriptions.
    Maps recognized medications to RxNorm CUIs and dosage structures.
    """
    file_bytes = await file.read()
    filename = file.filename or "prescription.png"
    subject_id = f"urn:uuid:{clinical_subject_id}" if clinical_subject_id else "urn:uuid:patient-primary"

    result = pipeline.process_document(
        content=file_bytes,
        filename=filename,
        mime_type=file.content_type,
        subject_id=subject_id,
    )

    return DocumentExtractionResponse(
        document_id=result.document_id,
        document_type="PRESCRIPTION",
        source_filename=result.source_filename,
        extracted_text=result.extracted_text,
        structured_results=result.structured_results,
        entities=result.entities,
        fhir_observations=result.fhir_observations,
        confidence_score=result.confidence_score,
    )
