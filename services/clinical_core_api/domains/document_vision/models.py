"""
MediScan Enterprise — Document Vision Domain Models
===================================================
Pydantic v2 schemas for Clinical Document Vision, OCR, Lab Results,
FHIR R4 Observation Serialization, and Negation-Aware NER Entities.
"""

from enum import Enum
from typing import Any, Tuple
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AssertionType(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HYPOTHETICAL = "HYPOTHETICAL"
    FAMILY_HISTORY = "FAMILY_HISTORY"


class TemporalityType(str, Enum):
    ACUTE = "ACUTE"
    CHRONIC = "CHRONIC"
    RESOLVED = "RESOLVED"


class AbnormalFlag(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"
    CRITICAL_LOW = "CRITICAL_LOW"


class ExtractedEntity(BaseModel):
    """Clinical entity extracted with negation, temporality, and char offsets."""
    term: str = Field(..., description="Canonical extracted term or phrase")
    snomed_code: str | None = Field(default=None, description="SNOMED-CT Concept ID")
    assertion: AssertionType = Field(default=AssertionType.PRESENT)
    temporality: TemporalityType = Field(default=TemporalityType.ACUTE)
    source_span: Tuple[int, int] = Field(..., description="Character offsets [start, end] in original text")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class ExtractedLabResult(BaseModel):
    """Numeric-preserving extracted laboratory biomarker observation."""
    test_name: str = Field(..., description="Name of test or analyte")
    loinc_code: str | None = Field(default=None, description="Official LOINC identifier")
    value: float | None = Field(default=None, description="Exact numerical float value")
    value_string: str | None = Field(default=None, description="String representation if composite, e.g. 140/90")
    systolic: float | None = Field(default=None, description="Systolic component for Blood Pressure")
    diastolic: float | None = Field(default=None, description="Diastolic component for Blood Pressure")
    unit: str | None = Field(default=None, description="Normalized UCUM unit")
    reference_range: str | None = Field(default=None, description="Extracted reference interval string")
    flag: AbnormalFlag | None = Field(default=None, description="NORMAL | HIGH | LOW | CRITICAL_HIGH | CRITICAL_LOW")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    source_span: Tuple[int, int] | None = Field(default=None, description="[start, end] character offsets")


class DocumentVisionResult(BaseModel):
    """Unified result containing raw text, structured labs, entities, and FHIR observations."""
    document_id: UUID = Field(default_factory=uuid4)
    document_type: str = Field(default="LAB_REPORT", description="LAB_REPORT | CLINICAL_NOTE | PRESCRIPTION")
    source_filename: str = Field(default="clinical_document.txt")
    extracted_text: str = Field(..., description="Full raw extracted clinical text")
    structured_results: list[ExtractedLabResult] = Field(default_factory=list)
    entities: list[ExtractedEntity] = Field(default_factory=list)
    fhir_observations: list[dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
