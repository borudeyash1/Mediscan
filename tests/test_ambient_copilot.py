"""
MediScan Enterprise — Voice AI, Ambient Clinical Scribe & Hybrid RAG Test Suite
=============================================================================
Verification Gate 5 Test Matrix:
  1. WebSocket Ambient Scribe Streaming (diarization, vocal biomarkers, entity extraction, prompts)
  2. Evidence-Linked SOAP Note Generation (100% claim provenance linking)
  3. Anti-Hallucination Medical Code Gate (deterministic stripping of fake codes)
  4. Hybrid RAG Clinical Guideline Copilot (inline citations over KDIGO, ADA, AHA/ACC)
  5. Audio Frame Signal Processing (VAD, pause ratio, respiratory distress index)
"""

import os
import sys
from uuid import uuid4
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure services/clinical-core-api is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services", "clinical-core-api")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "libs")))

from app.main import create_app
from domains.copilot_voice.models import (
    SpeakerRole,
    TranscriptUtterance,
    VocalBiomarkers,
    CopilotAskRequest,
)
from domains.copilot_voice.vocal_biomarkers import VocalBiomarkerAnalyzer
from domains.copilot_voice.coding_engine import AutonomousCodingEngine, VALID_CODE_LEXICON
from domains.copilot_voice.soap_generator import EvidenceLinkedSOAPGenerator
from domains.copilot_voice.rag_copilot import HybridRAGCopilot


@pytest.fixture(scope="module")
def api_client():
    """FastAPI TestClient instance."""
    app = create_app()
    return TestClient(app)


class TestWebSocketAmbientScribe:
    """Audit real-time bi-directional WebSocket ambient consultation streaming."""

    def test_ambient_scribe_stream_dialogue_and_biomarkers(self, api_client):
        """
        Connect to /ws/v2/ambient-scribe/{encounter_id}.
        Stream multi-turn dialogue with positive symptoms and explicit negations.
        Assert diarization, incremental entities, vocal biomarkers, and real-time prompts.
        """
        encounter_id = f"enc_stream_{uuid4().hex[:8]}"

        with api_client.websocket_connect(f"/ws/v2/ambient-scribe/{encounter_id}") as ws:
            # 1. Handshake verification
            init_msg = ws.receive_json()
            assert init_msg["event"] == "connected"
            assert init_msg["status"] == "ready"

            # 2. Turn 1: Clinician greeting
            ws.send_json({
                "type": "utterance",
                "text": "Hello Mr. Davis, what brings you into the emergency clinic today?",
                "speaker": "CLINICIAN",
                "duration_ms": 3200,
            })
            resp1 = ws.receive_json()
            assert resp1["event"] == "transcript_update"
            assert resp1["utterance"]["speaker"] == "CLINICIAN"
            assert resp1["vocal_biomarkers"]["speech_rate_wpm"] > 0
            assert 0.0 <= resp1["vocal_biomarkers"]["pause_ratio"] <= 1.0

            # 3. Turn 2: Patient describes severe symptoms
            ws.send_json({
                "type": "utterance",
                "text": "Doctor, I have severe crushing chest pain going down my left arm and I'm very short of breath.",
                "speaker": "PATIENT",
                "duration_ms": 4500,
            })
            # Receives transcript_update, entities_extracted, and interview_prompts
            events_received = []
            for _ in range(4):
                ev = ws.receive_json()
                events_received.append(ev)

            event_types = [e["event"] for e in events_received]
            assert "transcript_update" in event_types
            assert "entities_extracted" in event_types
            assert "interview_prompt" in event_types

            # Verify entities extracted
            entity_event = next(e for e in events_received if e["event"] == "entities_extracted")
            terms = [ent["term"] for ent in entity_event["entities"]]
            assert "chest pain" in terms
            assert any("short" in t or "dyspnea" in t for t in terms)

            # Verify vocal biomarkers returned in real time
            transcript_ev = next(e for e in events_received if e["event"] == "transcript_update")
            bm = transcript_ev["vocal_biomarkers"]
            assert bm["speech_rate_wpm"] > 0
            assert "respiratory_cadence_score" in bm
            assert 0.0 <= bm["respiratory_cadence_score"] <= 1.0

            # Verify clinical prompt emitted
            prompt_events = [e for e in events_received if e["event"] == "interview_prompt"]
            prompt_triggers = [pe["prompt"]["trigger_symptom"] for pe in prompt_events]
            assert "Chest Pain" in prompt_triggers

            # 4. Turn 3: Patient with explicit negations
            ws.send_json({
                "type": "utterance",
                "text": "I have no fever and denies cough, but feeling dizzy.",
                "speaker": "PATIENT",
                "duration_ms": 3000,
            })
            # Collect events: transcript_update, entities_extracted, interview_prompt
            negation_events = []
            for _ in range(3):
                ev = ws.receive_json()
                negation_events.append(ev)

            entity_ev_neg = next((e for e in negation_events if e["event"] == "entities_extracted"), None)
            assert entity_ev_neg is not None
            fever_ent = next((ent for ent in entity_ev_neg["entities"] if ent["term"] == "fever"), None)
            assert fever_ent is not None
            assert fever_ent["is_negated"] is True
            assert fever_ent["assertion_status"] == "ABSENT/DENIED"

            # 5. Finalize SOAP Note over WebSocket
            ws.send_json({"type": "finalize_soap"})
            soap_resp = ws.receive_json()
            assert soap_resp["event"] == "soap_finalized"
            soap_note = soap_resp["soap_note"]
            assert "subjective" in soap_note
            assert "objective" in soap_note
            assert "assessment" in soap_note
            assert "plan" in soap_note

            # Assert every subjective statement has an evidence span
            for claim in soap_note["subjective"]["claims"]:
                assert "source_evidence_span" in claim
                assert claim["source_evidence_span"]["utterance_id"].startswith("utt_")
                assert len(claim["source_evidence_span"]["text"]) > 0


class TestEvidenceLinkedSOAPAndCodeVerification:
    """Audit structured SOAP synthesis and claim-to-utterance evidence linking."""

    def test_evidence_linked_soap_generation_provenance(self):
        """
        Verify that 100% of claims in Subjective, Objective, Assessment, Plan
        contain non-null, valid source_evidence_span linking to real utterances.
        """
        generator = EvidenceLinkedSOAPGenerator()
        enc_id = "enc_audit_001"

        utterances = [
            TranscriptUtterance(
                utterance_id="utt_001",
                encounter_id=enc_id,
                speaker=SpeakerRole.CLINICIAN,
                text="What symptoms brought you into the hospital today?",
                timestamp_ms=0,
                duration_ms=2000,
            ),
            TranscriptUtterance(
                utterance_id="utt_002",
                encounter_id=enc_id,
                speaker=SpeakerRole.PATIENT,
                text="I have severe substernal chest pain radiating to my left arm for the past 90 minutes.",
                timestamp_ms=2500,
                duration_ms=4000,
            ),
            TranscriptUtterance(
                utterance_id="utt_003",
                encounter_id=enc_id,
                speaker=SpeakerRole.PATIENT,
                text="I have no fever, no cough, and no history of asthma.",
                timestamp_ms=7000,
                duration_ms=3000,
            ),
            TranscriptUtterance(
                utterance_id="utt_004",
                encounter_id=enc_id,
                speaker=SpeakerRole.CLINICIAN,
                text="Your blood pressure is 158/96 mmHg and heart rate is 108 bpm.",
                timestamp_ms=10500,
                duration_ms=3000,
            ),
            TranscriptUtterance(
                utterance_id="utt_005",
                encounter_id=enc_id,
                speaker=SpeakerRole.CLINICIAN,
                text="We will obtain an urgent 12-lead ECG and administer Aspirin 325 mg immediately.",
                timestamp_ms=14000,
                duration_ms=3500,
            ),
        ]

        soap = generator.generate_soap_note(
            encounter_id=enc_id,
            utterances=utterances,
            clinical_subject_id="pat_9988",
        )

        # Check sections exist
        assert soap.subjective.summary
        assert len(soap.subjective.claims) >= 2
        assert soap.objective.summary
        assert len(soap.objective.claims) >= 1
        assert soap.assessment.summary
        assert len(soap.assessment.claims) >= 1
        assert soap.plan.summary
        assert len(soap.plan.claims) >= 1

        # Check provenance for all claims across all 4 sections
        all_sections = [soap.subjective, soap.objective, soap.assessment, soap.plan]
        valid_utt_ids = {u.utterance_id for u in utterances}

        for sec in all_sections:
            for claim in sec.claims:
                assert claim.source_evidence_span is not None, f"Claim '{claim.statement}' has null evidence span"
                assert claim.source_evidence_span.utterance_id in valid_utt_ids, (
                    f"Claim utterance_id {claim.source_evidence_span.utterance_id} not in real utterances"
                )
                assert len(claim.source_evidence_span.text) > 0

        # Verify automated medical coding assigned
        assert len(soap.verified_icd10_codes) >= 1
        assert len(soap.verified_icd11_codes) >= 1
        assert len(soap.verified_snomed_codes) >= 1
        assert len(soap.verified_cpt_codes) >= 1

        # Verify codes are strictly valid
        icd10_vals = [c.code for c in soap.verified_icd10_codes]
        assert "I21.0" in icd10_vals or "R07.9" in icd10_vals


class TestAntiHallucinationMedicalCoding:
    """Audit deterministic medical coding post-processor and fake code rejection."""

    def test_strip_hallucinated_and_fake_codes(self):
        """
        Inject fake codes (e.g. Z99.9999_FAKE, FAKE_CPT_99999, BAD_SNOMED) into candidate list.
        Prove the post-processor strips them while keeping valid certified codes.
        """
        engine = AutonomousCodingEngine()

        candidate_input = [
            {"code": "I21.0", "code_system": "ICD-10-CM"},
            {"code": "Z99.9999_FAKE", "code_system": "ICD-10-CM"},    # Fake ICD-10
            {"code": "XYZ.999_INVALID", "code_system": "ICD-10-CM"},  # Hallucination
            {"code": "E11.22", "code_system": "ICD-10-CM"},
            {"code": "22298006", "code_system": "SNOMED-CT"},
            {"code": "SNOMED_999999999_FAKE", "code_system": "SNOMED-CT"}, # Fake SNOMED
            {"code": "99215", "code_system": "CPT"},
            {"code": "CPT_FAKE_00000", "code_system": "CPT"},         # Fake CPT
            {"code": "BA41.0", "code_system": "ICD-11"},
            {"code": "ICD11_FAKE_99", "code_system": "ICD-11"},       # Fake ICD-11
        ]

        verified_codes = engine.filter_and_verify_codes(candidate_input)
        verified_code_strs = [c.code for c in verified_codes]

        # Assert fakes are stripped
        assert "Z99.9999_FAKE" not in verified_code_strs
        assert "XYZ.999_INVALID" not in verified_code_strs
        assert "SNOMED_999999999_FAKE" not in verified_code_strs
        assert "CPT_FAKE_00000" not in verified_code_strs
        assert "ICD11_FAKE_99" not in verified_code_strs

        # Assert valid codes are preserved and flagged verified
        assert "I21.0" in verified_code_strs
        assert "E11.22" in verified_code_strs
        assert "22298006" in verified_code_strs
        assert "99215" in verified_code_strs
        assert "BA41.0" in verified_code_strs

        for c in verified_codes:
            assert c.is_verified is True
            assert len(c.description) > 0


class TestHybridRAGGuidelineCopilot:
    """Audit Hybrid RAG endpoint and authoritative clinical citations."""

    def test_rag_guideline_ask_diabetes_ckd3b_target_bp(self, api_client):
        """
        Call POST /api/v2/copilot/ask with:
        'What is the target blood pressure and first-line pharmacotherapy for a patient with Type 2 Diabetes and CKD Stage 3b?'
        Verify Qdrant returns relevant guideline chunks and the response includes inline citations.
        """
        payload = {
            "query": "What is the target blood pressure and first-line pharmacotherapy for a patient with Type 2 Diabetes and CKD Stage 3b?",
            "guideline_sources": ["KDIGO", "ADA", "AHA", "ACC", "NICE"],
            "top_k": 4,
        }

        resp = api_client.post("/api/v2/copilot/ask", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "answer" in data
        assert "citations" in data
        assert len(data["citations"]) >= 1

        answer_text = data["answer"]
        # Verify clinical accuracy: Target BP (< 130/80 or < 120) and RAS blockade (ACEi/ARB) + SGLT2i
        assert "130/80" in answer_text or "120" in answer_text
        assert "ACE" in answer_text or "ARB" in answer_text
        assert "SGLT2" in answer_text or "Empagliflozin" in answer_text

        # Verify inline citations exist in text
        assert "[" in answer_text and "]" in answer_text
        has_kdigo_or_ada_citation = any(
            "KDIGO" in c["guideline_title"] or "ADA" in c["guideline_title"] or "AHA" in c["guideline_title"]
            for c in data["citations"]
        )
        assert has_kdigo_or_ada_citation is True

        # Verify patient specific safety guidance
        assert len(data["patient_specific_recommendations"]) >= 1
        rec_text = " ".join(data["patient_specific_recommendations"]).lower()
        assert "potassium" in rec_text or "nsaid" in rec_text or "egfr" in rec_text


class TestVocalBiomarkersAcousticProcessor:
    """Audit signal processing for audio frames and speech cadence metrics."""

    def test_audio_frame_biomarker_extraction(self):
        """
        Synthesize 16kHz PCM audio buffers and verify speech rate, pause ratio,
        and respiratory distress index extraction.
        """
        analyzer = VocalBiomarkerAnalyzer(sample_rate=16000)

        # 1. Normal fluent speech: 3 seconds with bursts and moderate pause
        t = np.linspace(0, 3.0, 48000, dtype=np.float32)
        fluent_audio = (np.sin(2 * np.pi * 220 * t) * 16000).astype(np.int16)
        # Add intermittent silence (500ms pause)
        fluent_audio[16000:24000] = 0

        bm_fluent = analyzer.analyze_audio_frame(fluent_audio.tobytes(), known_word_count=8)
        assert bm_fluent.speech_rate_wpm > 50.0
        assert 0.10 <= bm_fluent.pause_ratio <= 0.60
        assert 0.0 <= bm_fluent.respiratory_distress_index <= 0.60
        assert bm_fluent.respiratory_cadence_score >= 0.40

        # 2. Dyspneic short-burst speech: high pause ratio, short burst fragments
        dyspneic_audio = np.zeros(48000, dtype=np.int16)
        # Short burst 1 (300ms)
        dyspneic_audio[2000:6800] = (np.sin(2 * np.pi * 300 * t[:4800]) * 18000).astype(np.int16)
        # Long pause, short burst 2 (400ms)
        dyspneic_audio[25000:31400] = (np.sin(2 * np.pi * 300 * t[:6400]) * 18000).astype(np.int16)

        bm_dyspneic = analyzer.analyze_audio_frame(dyspneic_audio.tobytes(), known_word_count=3)
        assert bm_dyspneic.pause_ratio > 0.40
        assert bm_dyspneic.respiratory_distress_index > 0.35
