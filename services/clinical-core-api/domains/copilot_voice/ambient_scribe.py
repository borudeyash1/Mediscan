"""
Real-Time Streaming Ambient Clinical Scribe & WebSocket Orchestrator.
Handles bi-directional audio/transcript streaming, speaker diarization,
incremental entity extraction, vocal biomarker analysis, and real-time clinical prompts.
"""

import base64
import json
from typing import Any, Optional
from uuid import uuid4
import structlog
from fastapi import WebSocket, WebSocketDisconnect

from .models import (
    SpeakerRole,
    TranscriptUtterance,
    ExtractedClinicalEntity,
    VocalBiomarkers,
    ClinicalInterviewPrompt,
    EvidenceLinkedSOAPNote,
)
from .vocal_biomarkers import VocalBiomarkerAnalyzer
from .clinical_questions_engine import ClinicalInterviewPromptEngine
from .soap_generator import EvidenceLinkedSOAPGenerator
from .coding_engine import AutonomousCodingEngine

logger = structlog.get_logger(__name__)


class AmbientScribeSession:
    """Manages active live consultation state for an encounter."""

    def __init__(self, encounter_id: str, clinical_subject_id: Optional[str] = None):
        self.encounter_id = encounter_id
        self.clinical_subject_id = clinical_subject_id
        self.utterances: list[TranscriptUtterance] = []
        self.extracted_entities: list[ExtractedClinicalEntity] = []
        self.vocal_analyzer = VocalBiomarkerAnalyzer()
        self.prompt_engine = ClinicalInterviewPromptEngine()
        self.coding_engine = AutonomousCodingEngine()
        self.soap_generator = EvidenceLinkedSOAPGenerator(coding_engine=self.coding_engine)

    def diarize_speaker(self, text: str, explicit_speaker: Optional[str] = None) -> SpeakerRole:
        """
        Diarize speaker role (CLINICIAN vs PATIENT).
        Respects explicit tag if provided; otherwise applies clinical conversational heuristics.
        """
        if explicit_speaker:
            clean = explicit_speaker.strip().upper()
            if "DOC" in clean or "CLINICIAN" in clean or "PHYSICIAN" in clean:
                return SpeakerRole.CLINICIAN
            if "PATIENT" in clean:
                return SpeakerRole.PATIENT
            if "FAMILY" in clean:
                return SpeakerRole.FAMILY_MEMBER

        lower = text.lower().strip()

        # Clinician dialogue cues: clinical questions, examination commands, care plans
        clinician_cues = [
            "how long", "what brings you in", "tell me about", "where does it hurt",
            "let me listen", "take a deep breath", "open your mouth", "blood pressure is",
            "we need to order", "i'm prescribing", "i will prescribe", "let's check",
            "any family history", "do you have any allergies", "are you taking",
        ]
        if any(cue in lower for cue in clinician_cues) or (text.endswith("?") and not any(w in lower for w in ["can i", "could i", "am i going to die"])):
            return SpeakerRole.CLINICIAN

        # Default to Patient
        return SpeakerRole.PATIENT

    def extract_entities_from_text(self, text: str, utterance_id: str) -> list[ExtractedClinicalEntity]:
        """
        Incremental assertion-aware clinical entity extraction.
        Distinguishes positive presentations from explicit denials.
        """
        entities: list[ExtractedClinicalEntity] = []
        lower = text.lower()

        # Known clinical entities
        symptom_lexicon = {
            "chest pain": "SYMPTOM",
            "pain in chest": "SYMPTOM",
            "angina": "SYMPTOM",
            "shortness of breath": "SYMPTOM",
            "short of breath": "SYMPTOM",
            "dyspnea": "SYMPTOM",
            "fever": "SYMPTOM",
            "chills": "SYMPTOM",
            "headache": "SYMPTOM",
            "cough": "SYMPTOM",
            "fatigue": "SYMPTOM",
            "tiredness": "SYMPTOM",
            "palpitations": "SYMPTOM",
            "dizzy": "SYMPTOM",
            "dizziness": "SYMPTOM",
            "nausea": "SYMPTOM",
            "vomiting": "SYMPTOM",
            "sweating": "SYMPTOM",
            "diaphoresis": "SYMPTOM",
        }

        # Check for negations in proximity
        negation_markers = ["no ", "not ", "denies ", "without ", "never ", "haven't had ", "didn't have "]
        contrastive_delimiters = [", but ", " but ", ". ", "; ", ", however ", " however "]

        for term, cat in symptom_lexicon.items():
            start_pos = lower.find(term)
            if start_pos != -1:
                end_pos = start_pos + len(term)
                # Check pre-window for negation
                window_start = max(0, start_pos - 35)
                pre_window = lower[window_start:start_pos]
                # Break negation scope if contrastive delimiter exists
                for delim in contrastive_delimiters:
                    if delim in pre_window:
                        pre_window = pre_window.split(delim)[-1]

                is_negated = any(marker in pre_window for marker in negation_markers)

                entity = ExtractedClinicalEntity(
                    term=term,
                    category=cat,
                    assertion_status="ABSENT/DENIED" if is_negated else "PRESENT",
                    is_negated=is_negated,
                    utterance_id=utterance_id,
                    start_char=start_pos,
                    end_char=end_pos,
                    confidence=0.98 if is_negated else 0.95,
                )
                entities.append(entity)

        return entities

    def process_turn(
        self,
        text: str,
        speaker_hint: Optional[str] = None,
        audio_base64: Optional[str] = None,
        duration_ms: int = 2500,
        timestamp_ms: int = 0,
    ) -> dict[str, Any]:
        """
        Process a single spoken turn.
        Extracts diarization, vocal biomarkers, clinical entities, and dynamic follow-up prompts.
        """
        utt_id = f"utt_{uuid4().hex[:8]}"
        role = self.diarize_speaker(text, speaker_hint)

        # 1. Vocal Biomarker Analysis
        if audio_base64:
            try:
                audio_bytes = base64.b64decode(audio_base64)
                biomarkers = self.vocal_analyzer.analyze_audio_frame(audio_bytes, known_word_count=len(text.split()))
            except Exception as e:
                logger.warning("vocal_biomarker.audio_decode_failed", error=str(e))
                biomarkers = self.vocal_analyzer.analyze_utterance_timing(text, duration_ms)
        else:
            biomarkers = self.vocal_analyzer.analyze_utterance_timing(text, duration_ms)

        # 2. Incremental Entity Extraction
        new_entities = self.extract_entities_from_text(text, utt_id)
        self.extracted_entities.extend(new_entities)

        # 3. Transcript Record
        utterance = TranscriptUtterance(
            utterance_id=utt_id,
            encounter_id=self.encounter_id,
            speaker=role,
            text=text,
            timestamp_ms=timestamp_ms,
            duration_ms=duration_ms,
            vocal_biomarkers=biomarkers,
            extracted_entities=new_entities,
        )
        self.utterances.append(utterance)

        # 4. Clinical Interview Prompt Generation
        is_patient = (role == SpeakerRole.PATIENT)
        suggested_prompts = self.prompt_engine.evaluate_utterance(text, is_patient=is_patient)

        return {
            "utterance": utterance.model_dump(mode="json"),
            "vocal_biomarkers": biomarkers.model_dump(mode="json"),
            "extracted_entities": [e.model_dump(mode="json") for e in new_entities],
            "suggested_prompts": [p.model_dump(mode="json") for p in suggested_prompts],
        }

    def finalize_soap(self) -> EvidenceLinkedSOAPNote:
        """Synthesize final evidence-linked SOAP note."""
        return self.soap_generator.generate_soap_note(
            encounter_id=self.encounter_id,
            utterances=self.utterances,
            clinical_subject_id=self.clinical_subject_id,
            extracted_entities=self.extracted_entities,
        )


class AmbientScribeSessionManager:
    """In-memory active session manager for WebSocket scribe streams."""

    def __init__(self):
        self._sessions: dict[str, AmbientScribeSession] = {}

    def get_or_create(self, encounter_id: str, clinical_subject_id: Optional[str] = None) -> AmbientScribeSession:
        if encounter_id not in self._sessions:
            self._sessions[encounter_id] = AmbientScribeSession(
                encounter_id=encounter_id, clinical_subject_id=clinical_subject_id
            )
        return self._sessions[encounter_id]

    def remove(self, encounter_id: str) -> None:
        self._sessions.pop(encounter_id, None)


scribe_session_manager = AmbientScribeSessionManager()


async def handle_ambient_scribe_ws(websocket: WebSocket, encounter_id: str) -> None:
    """
    Bi-directional streaming WebSocket handler (/ws/v2/ambient-scribe/{encounter_id}).
    Processes incoming audio/text chunks, emits incremental transcripts, biomarkers,
    entities, real-time interview prompts, and final SOAP notes.
    """
    await websocket.accept()
    session = scribe_session_manager.get_or_create(encounter_id)
    logger.info("ambient_scribe.ws_connected", encounter_id=encounter_id)

    try:
        # Send initial handshake confirmation
        await websocket.send_json({
            "event": "connected",
            "encounter_id": encounter_id,
            "status": "ready",
            "message": "Ambient Clinical Scribe stream established.",
        })

        while True:
            raw_msg = await websocket.receive_text()
            try:
                data = json.loads(raw_msg)
            except Exception:
                data = {"text": raw_msg}

            msg_type = data.get("type", data.get("action", "utterance"))

            if msg_type == "finalize_soap":
                soap_note = session.finalize_soap()
                await websocket.send_json({
                    "event": "soap_finalized",
                    "encounter_id": encounter_id,
                    "soap_note": soap_note.model_dump(mode="json"),
                })
                continue

            if msg_type == "reset":
                session = scribe_session_manager.get_or_create(encounter_id)
                session.utterances.clear()
                session.extracted_entities.clear()
                session.prompt_engine.reset_session()
                await websocket.send_json({"event": "reset_completed", "encounter_id": encounter_id})
                continue

            # Standard utterance or audio frame
            text = str(data.get("text", "")).strip()
            speaker_hint = data.get("speaker")
            audio_b64 = data.get("audio_base64")
            duration_ms = int(data.get("duration_ms", 2500))
            timestamp_ms = int(data.get("timestamp_ms", 0))

            if not text and not audio_b64:
                continue

            result = session.process_turn(
                text=text,
                speaker_hint=speaker_hint,
                audio_base64=audio_b64,
                duration_ms=duration_ms,
                timestamp_ms=timestamp_ms,
            )

            # Emit incremental transcript with vocal biomarkers
            await websocket.send_json({
                "event": "transcript_update",
                "encounter_id": encounter_id,
                "utterance": result["utterance"],
                "vocal_biomarkers": result["vocal_biomarkers"],
            })

            # Emit entities if extracted
            if result["extracted_entities"]:
                await websocket.send_json({
                    "event": "entities_extracted",
                    "encounter_id": encounter_id,
                    "entities": result["extracted_entities"],
                })

            # Emit clinical follow-up prompts if triggered
            if result["suggested_prompts"]:
                for prompt in result["suggested_prompts"]:
                    await websocket.send_json({
                        "event": "interview_prompt",
                        "encounter_id": encounter_id,
                        "prompt": prompt,
                    })

    except WebSocketDisconnect:
        logger.info("ambient_scribe.ws_disconnected", encounter_id=encounter_id)
    except Exception as e:
        logger.error("ambient_scribe.ws_error", encounter_id=encounter_id, error=str(e))
        try:
            await websocket.close()
        except Exception:
            pass
