"""
Pydantic v2 Models for Voice AI, Ambient Scribe, SOAP Generation, and Hybrid RAG Copilot.
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class SpeakerRole(str, Enum):
    CLINICIAN = "CLINICIAN"
    PATIENT = "PATIENT"
    FAMILY_MEMBER = "FAMILY_MEMBER"
    SYSTEM = "SYSTEM"


class VocalCadenceCategory(str, Enum):
    NORMAL = "NORMAL"
    TACHYPNEIC_SHORT_PHRASES = "TACHYPNEIC_SHORT_PHRASES"
    BRADYPNEIC_HESITANT = "BRADYPNEIC_HESITANT"
    DYSPNEIC_DISTRESS = "DYSPNEIC_DISTRESS"


class VocalBiomarkers(BaseModel):
    """Real-time vocal acoustic & temporal biomarker metrics."""
    speech_rate_wpm: float = Field(..., ge=0.0, description="Words spoken per minute")
    pause_ratio: float = Field(..., ge=0.0, le=1.0, description="Ratio of pause/silence time to total frame time")
    respiratory_distress_index: float = Field(
        ..., ge=0.0, le=1.0, description="Composite respiratory distress index (0.0 = calm, 1.0 = severe dyspnea)"
    )
    respiratory_cadence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Cadence regularity score (short fragmented bursts lower score)"
    )
    classification: VocalCadenceCategory = Field(default=VocalCadenceCategory.NORMAL)
    mean_pause_duration_ms: float = Field(default=0.0, ge=0.0)
    burst_count: int = Field(default=1, ge=0)


class ExtractedClinicalEntity(BaseModel):
    """Clinical entity extracted incrementally from dialogue."""
    term: str
    category: str = Field(..., description="SYMPTOM, LAB, VITAL, MEDICATION, ALLERGY, HISTORY")
    assertion_status: str = Field(default="PRESENT", description="PRESENT, ABSENT/DENIED, FAMILY_HISTORY, HYPOTHETICAL")
    is_negated: bool = Field(default=False)
    utterance_id: str
    start_char: int = 0
    end_char: int = 0
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class ClinicalInterviewPrompt(BaseModel):
    """Dynamic real-time clinical follow-up interview prompt for the clinician."""
    prompt_id: str = Field(default_factory=lambda: f"prompt_{uuid4().hex[:8]}")
    trigger_symptom: str
    suggested_question: str
    clinical_rationale: str
    urgency: str = Field(default="HIGH", description="CRITICAL, HIGH, MEDIUM, ROUTINE")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceEvidenceSpan(BaseModel):
    """Exact source citation linking a claim back to an utterance or lab report."""
    utterance_id: str = Field(..., description="Unique identifier of the transcript utterance")
    speaker: SpeakerRole
    text: str = Field(..., description="Exact quoted text from transcript")
    start_char: int = Field(default=0, ge=0)
    end_char: int = Field(default=0, ge=0)
    timestamp_ms: Optional[int] = Field(default=None, description="Audio offset in milliseconds")


class SOAPClaim(BaseModel):
    """Individual clinical statement with mandatory evidence attribution."""
    statement: str
    source_evidence_span: SourceEvidenceSpan
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    category_tag: Optional[str] = None


class StructuredSOAPSection(BaseModel):
    """Structured SOAP section containing granular claims and narrative summary."""
    summary: str
    claims: list[SOAPClaim] = Field(default_factory=list)


class VerifiedMedicalCode(BaseModel):
    """Deterministically verified medical code with zero hallucination guarantee."""
    code: str
    code_system: str = Field(..., description="ICD-10-CM, ICD-11, SNOMED-CT, CPT")
    description: str
    is_verified: bool = Field(default=True, description="Strictly verified against canonical medical lexicon")
    evidence_utterance_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    hcc_category: Optional[str] = None


class TranscriptUtterance(BaseModel):
    """Single turn utterance in the ambient clinical conversation."""
    utterance_id: str = Field(default_factory=lambda: f"utt_{uuid4().hex[:8]}")
    encounter_id: str
    speaker: SpeakerRole
    text: str
    timestamp_ms: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=1000, ge=0)
    audio_base64: Optional[str] = None
    vocal_biomarkers: Optional[VocalBiomarkers] = None
    extracted_entities: list[ExtractedClinicalEntity] = Field(default_factory=list)


class EvidenceLinkedSOAPNote(BaseModel):
    """Complete Evidence-Linked SOAP Note conforming to SaMD clinical documentation integrity."""
    encounter_id: str
    clinical_subject_id: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    subjective: StructuredSOAPSection
    objective: StructuredSOAPSection
    assessment: StructuredSOAPSection
    plan: StructuredSOAPSection
    verified_icd10_codes: list[VerifiedMedicalCode] = Field(default_factory=list)
    verified_icd11_codes: list[VerifiedMedicalCode] = Field(default_factory=list)
    verified_snomed_codes: list[VerifiedMedicalCode] = Field(default_factory=list)
    verified_cpt_codes: list[VerifiedMedicalCode] = Field(default_factory=list)
    clinician_digital_signature: Optional[str] = None


class GuidelineCitation(BaseModel):
    """Authoritative citation from indexed clinical practice guidelines."""
    source_authority: str = Field(..., description="AHA, ACC, KDIGO, ADA, NICE, GOLD, GINA, ICMR")
    guideline_title: str
    section: str
    evidence_level: str = Field(default="Class I, Level A")
    chunk_text: str
    similarity_score: float = Field(default=0.92, ge=0.0, le=1.0)


class CopilotAskRequest(BaseModel):
    """Request payload for Hybrid RAG Clinical Guideline Copilot."""
    query: str
    clinical_subject_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    patient_context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Active FHIR chart snapshot: conditions, vitals, eGFR, meds, allergies",
    )
    guideline_sources: list[str] = Field(
        default=["KDIGO", "ADA", "AHA", "ACC", "NICE", "GOLD"],
        description="Guideline bodies to filter search against",
    )
    top_k: int = Field(default=5, ge=1, le=20)


class CopilotAskResponse(BaseModel):
    """Evidence-grounded response with inline citations."""
    query: str
    answer: str
    citations: list[GuidelineCitation] = Field(default_factory=list)
    patient_specific_recommendations: list[str] = Field(default_factory=list)
    active_guidelines_consulted: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
