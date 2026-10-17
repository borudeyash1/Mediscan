"""
MediScan Enterprise — Multimodal Diagnostic & Conformal Inference Test Suite
=============================================================================
VERIFICATION GATE 4: MULTIMODAL INFERENCE, CONFORMAL CALIBRATION & AUDIT LEDGER

Tests:
1. No-Pickle & No-Random Security Audit:
   Static scan across codebase verifying zero untrusted pickle.load() and zero random.random()
   in clinical diagnostic scoring.
2. Conformal Prediction & Calibration Check:
   Asserts that every differential prediction includes calibrated probability p in (0, 1),
   valid 95% conformal interval [lower, upper] with lower <= p <= upper, ICD-11 code, and SNOMED code.
3. SHAP Feature Attribution Verification:
   Asserts that all differential predictions contain non-empty feature attributions.
4. Visual Saliency (Grad-CAM) & 12-Lead ECG Analysis:
   Asserts that CXR generates valid base64 data URI overlay and ECG processor extracts HR, QTc,
   and ST elevation criteria.
5. Out-of-Distribution (OOD) & Abstention Check:
   Asserts that ambiguous single-symptom input ("mild tiredness") flags abstained_ood: True
   and outputs concrete rule_out_workup without hallucinating disease.
6. End-to-End Orchestration & Immutable Audit Ledger:
   Asserts that POST /api/v2/encounters/{id}/multimodal-assess generates full CDS response
   and appends cryptographic SHA-256 hash-chained entry to immutable_audit_ledger.
"""

import base64
import io
import re
import sys
from pathlib import Path
from uuid import UUID, uuid4

# Add project root and clinical-core-api to sys.path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

_api_path = _root / "services" / "clinical-core-api"
if str(_api_path) not in sys.path:
    sys.path.insert(0, str(_api_path))

import pytest
from PIL import Image

from services.clinical_core_api.domains.multimodal_diagnosis.audit_ledger import ImmutableAuditLedger
from services.clinical_core_api.domains.multimodal_diagnosis.classifier import NeuroSymbolicDiagnosticClassifier
from services.clinical_core_api.domains.multimodal_diagnosis.conformal_calibrator import ConformalPredictionCalibrator
from services.clinical_core_api.domains.multimodal_diagnosis.ecg_processor import ECGSignalProcessor
from services.clinical_core_api.domains.multimodal_diagnosis.imaging_analyzer import MedicalImagingAnalyzer
from services.clinical_core_api.domains.multimodal_diagnosis.models import (
    ClinicalEntityInput,
    ImagingWaveformRef,
    MultimodalAssessmentRequest,
    PatientContext,
    VitalLabInput,
)
from services.clinical_core_api.domains.multimodal_diagnosis.orchestrator import MultimodalDiagnosticOrchestrator


# ═══════════════════════════════════════════════════════════════════════
# 1. NO-PICKLE & NO-RANDOM SECURITY AUDIT
# ═══════════════════════════════════════════════════════════════════════

class TestSecurityAuditNoPickleNoRandom:
    """Verifies that zero untrusted pickles and zero random numbers exist in diagnostic code."""

    def test_no_untrusted_pickle_load_in_domains(self):
        """Scans codebase for pickle.load / pickle.loads to prevent RCE vulnerability."""
        domains_dir = _api_path / "domains"
        pickle_usages: list[str] = []

        for py_file in domains_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if "pickle.load" in content:
                pickle_usages.append(str(py_file))

        assert len(pickle_usages) == 0, f"Found untrusted pickle.load in: {pickle_usages}"

    def test_no_random_in_diagnostic_probabilities(self):
        """Verifies that diagnostic inference uses deterministic math, not random generators."""
        multimodal_dir = _api_path / "domains" / "multimodal_diagnosis"
        random_usages: list[str] = []

        for py_file in multimodal_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            # Look for random.random(), Math.random(), np.random
            if re.search(r"\b(?:random\.random|Math\.random|np\.random)\b", content):
                random_usages.append(str(py_file))

        assert len(random_usages) == 0, f"Found illegal random probability generator in: {random_usages}"


# ═══════════════════════════════════════════════════════════════════════
# 2. CONFORMAL PREDICTION & CALIBRATION TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestConformalPredictionAndCalibration:
    """Verifies calibrated probabilities, finite-sample 95% conformal intervals, and codes."""

    def test_stemi_cardiac_case_conformal_differential(self):
        patient = PatientContext(
            age_years=64,
            biological_sex="MALE",
            weight_kg=82.5,
            latest_egfr_ml_min=28.4,
            known_allergies_snomed=["91936005"],
        )
        entities = [
            ClinicalEntityInput(snomed_code="29857009", term="Substernal chest pain", assertion="PRESENT"),
            ClinicalEntityInput(snomed_code="426976000", term="Pain radiating to left arm", assertion="PRESENT"),
            ClinicalEntityInput(snomed_code="386661004", term="Fever", assertion="ABSENT"),
        ]
        labs = [
            VitalLabInput(loinc_code="6598-7", name="Troponin T.cardiac", value=0.42, unit="ng/mL", reference_high=0.014),
            VitalLabInput(loinc_code="8480-6", name="Systolic BP", value=168.0, unit="mm[Hg]"),
            VitalLabInput(loinc_code="8867-4", name="Heart Rate", value=112.0, unit="/min"),
        ]
        ecg_markers = ["ST_ELEVATION", "V1_V4_ELEVATION"]

        predictions = NeuroSymbolicDiagnosticClassifier.predict_differential(
            patient_context=patient,
            entities=entities,
            labs=labs,
            ecg_markers=ecg_markers,
            top_k=5,
        )

        assert len(predictions) >= 3

        # Rank 1 must be STEMI
        top_pred = predictions[0]
        assert "Myocardial Infarction" in top_pred.condition or "STEMI" in top_pred.condition
        assert top_pred.icd11_code == "BA41.0"
        assert top_pred.snomed_code == "54329005"
        assert top_pred.calibrated_probability >= 0.85

        # Check all predictions in differential meet mathematical conformal bounds
        for pred in predictions:
            p = pred.calibrated_probability
            lower, upper = pred.conformal_95_interval
            assert 0.0 < p < 1.0, f"Probability {p} must be strictly in (0, 1)"
            assert lower <= p <= upper, f"Conformal invariant breached: lower ({lower}) <= p ({p}) <= upper ({upper})"
            assert pred.icd11_code != ""
            assert pred.snomed_code != ""


# ═══════════════════════════════════════════════════════════════════════
# 3. SHAP ATTRIBUTIONS VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

class TestSHAPFeatureAttributions:
    """Verifies that every prediction includes non-empty, clinically grounded feature attributions."""

    def test_shap_attributions_non_empty_and_valid(self):
        patient = PatientContext(age_years=52, biological_sex="FEMALE")
        entities = [
            ClinicalEntityInput(snomed_code="29857009", term="chest pain", assertion="PRESENT"),
            ClinicalEntityInput(snomed_code="386661004", term="fever", assertion="ABSENT"),
        ]
        labs = [
            VitalLabInput(loinc_code="6598-7", name="Troponin T", value=0.35, unit="ng/mL", reference_high=0.014),
        ]

        predictions = NeuroSymbolicDiagnosticClassifier.predict_differential(
            patient_context=patient,
            entities=entities,
            labs=labs,
            top_k=3,
        )

        for pred in predictions:
            assert len(pred.shap_attributions) > 0, f"Prediction {pred.condition} must have SHAP attributions"
            for attr in pred.shap_attributions:
                assert attr.feature_name != ""
                assert attr.modality in ["LAB", "VITAL", "SYMPTOM", "ECG", "IMAGING", "DEMOGRAPHIC"]
                assert attr.direction in ["INCREASES_RISK", "DECREASES_RISK"]
                assert isinstance(attr.attribution_score, float)


# ═══════════════════════════════════════════════════════════════════════
# 4. VISUAL SALIENCY (GRAD-CAM) & 12-LEAD ECG ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

class TestVisualSaliencyAndECGAnalysis:
    """Verifies CXR Grad-CAM heatmap generation and 12-lead ECG interval & STEMI analysis."""

    def test_cxr_gradcam_overlay_generation(self):
        # Generate synthetic grayscale CXR image
        img = Image.new("L", (256, 256), color=120)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        cxr_bytes = buf.getvalue()

        saliency = MedicalImagingAnalyzer.analyze_cxr(
            image_input=cxr_bytes,
            finding_hint="Right lower lobe consolidation",
        )

        assert saliency.modality == "DICOM_CXR"
        assert saliency.confidence > 0.8
        assert saliency.heatmap_overlay_base64.startswith("data:image/png;base64,")

        # Verify decoding the base64 URI produces a valid PIL image
        raw_b64 = saliency.heatmap_overlay_base64.split(",")[1]
        decoded = base64.b64decode(raw_b64)
        overlay_img = Image.open(io.BytesIO(decoded))
        assert overlay_img.format == "PNG"
        assert overlay_img.size == (256, 256)

    def test_12_lead_ecg_stemi_criteria_and_intervals(self):
        # Multi-lead ECG dictionary with ST elevation in V2, V3, V4
        ecg_data = {
            "V1": [0.0, 0.05, 0.0],
            "V2": [0.0, 0.25, 0.22, 0.0],  # > 2mm ST elevation
            "V3": [0.0, 0.30, 0.28, 0.0],  # > 2mm ST elevation
            "V4": [0.0, 0.22, 0.20, 0.0],  # > 2mm ST elevation
            "I": [0.0, -0.15, 0.0],        # reciprocal depression
        }

        ecg_res = ECGSignalProcessor.analyze_ecg(
            samples_or_leads=ecg_data,
            heart_rate_hint=112.0,
        )

        assert ecg_res.heart_rate_bpm == 112.0
        assert ecg_res.pr_interval_ms == 160.0
        assert ecg_res.qrs_duration_ms == 92.0
        assert ecg_res.qtc_interval_ms > 0
        assert ecg_res.stemi_criteria_met is True
        assert "V2" in ecg_res.st_elevation_leads
        assert "V3" in ecg_res.st_elevation_leads
        assert "V4" in ecg_res.st_elevation_leads
        assert "STEMI" in ecg_res.rhythm_classification


# ═══════════════════════════════════════════════════════════════════════
# 5. OUT-OF-DISTRIBUTION (OOD) & ABSTENTION CHECK
# ═══════════════════════════════════════════════════════════════════════

class TestOODAbstentionDetector:
    """Verifies that ambiguous single-symptom input triggers abstention and rule-out workup."""

    def test_ambiguous_mild_tiredness_triggers_ood_abstention(self):
        encounter_id = uuid4()
        patient = PatientContext(age_years=35, biological_sex="FEMALE")
        # Single vague symptom without any labs, vitals, or imaging
        entities = [
            ClinicalEntityInput(snomed_code="84229001", term="mild tiredness", assertion="PRESENT"),
        ]

        req = MultimodalAssessmentRequest(
            clinical_subject_id=uuid4(),
            patient_context=patient,
            extracted_clinical_entities=entities,
            structured_vitals_labs=[],
            imaging_waveform_refs=[],
        )

        response = MultimodalDiagnosticOrchestrator.execute_assessment(
            encounter_id=encounter_id,
            request=req,
        )

        # Assert abstained_ood is True!
        assert response.abstained_ood is True
        assert response.ood_reason is not None
        assert "uncertainty" in response.ood_reason.lower() or "insufficient" in response.ood_reason.lower()

        # Top predictions must NOT be high confidence
        for pred in response.conformal_differential_diagnosis:
            assert pred.calibrated_probability <= 0.25, "OOD input must not yield high confidence prediction"
            assert len(pred.rule_out_workup) > 0, "OOD must provide concrete rule-out workup recommendations"
            assert any("CBC" in w or "TSH" in w or "Metabolic" in w for w in pred.rule_out_workup)


# ═══════════════════════════════════════════════════════════════════════
# 6. IMMUTABLE AUDIT LEDGER & END-TO-END ORCHESTRATION TEST
# ═══════════════════════════════════════════════════════════════════════

class TestEndToEndOrchestrationAndAuditLedger:
    """Verifies Section 6.1 contract, cryptographic hash-chaining, and pharmacology gating."""

    def test_end_to_end_assessment_and_audit_chain_integrity(self):
        encounter_id = uuid4()
        tenant_id = uuid4()

        req = MultimodalAssessmentRequest(
            clinical_subject_id=uuid4(),
            tenant_id=tenant_id,
            patient_context=PatientContext(
                age_years=64,
                biological_sex="MALE",
                weight_kg=82.5,
                latest_egfr_ml_min=28.4,
                active_medications_rxnorm=["860975", "197361"],
                known_allergies_snomed=["91936005"],  # Penicillin allergy
            ),
            extracted_clinical_entities=[
                ClinicalEntityInput(snomed_code="29857009", term="Substernal chest pain", assertion="PRESENT", onset_hours=3.0),
                ClinicalEntityInput(snomed_code="426976000", term="Pain radiating to left arm", assertion="PRESENT", onset_hours=2.0),
                ClinicalEntityInput(snomed_code="386661004", term="Fever", assertion="ABSENT"),
            ],
            structured_vitals_labs=[
                VitalLabInput(loinc_code="8480-6", name="Systolic BP", value=168.0, unit="mm[Hg]"),
                VitalLabInput(loinc_code="8867-4", name="Heart Rate", value=112.0, unit="/min"),
                VitalLabInput(loinc_code="6598-7", name="Troponin T.cardiac", value=0.42, unit="ng/mL", reference_high=0.014),
            ],
            imaging_waveform_refs=[
                ImagingWaveformRef(
                    modality="ECG_12_LEAD",
                    s3_uri="s3://mediscan-prod-us-phi/ecg/enc-8821.dcm",
                    waveform_samples=[[0.0, 0.25, 0.22, 0.0]],  # V2-V4 ST elevation
                ),
                ImagingWaveformRef(
                    modality="DICOM_CXR",
                    s3_uri="s3://mediscan-prod-us-phi/cxr/enc-8821.dcm",
                ),
            ],
        )

        response = MultimodalDiagnosticOrchestrator.execute_assessment(
            encounter_id=encounter_id,
            request=req,
        )

        # 1. Contract & Triage verification
        assert response.inference_id is not None
        assert response.encounter_id == encounter_id
        assert response.triage_assessment.severity_tier == "CRITICAL"
        assert response.triage_assessment.immediate_protocol == "ACTIVATE_STEMI_CATH_LAB_PROTOCOL"

        # 2. Pharmacology CDS verification
        cds = response.pharmacology_cds_recommendations
        assert len(cds.proposed_orders) >= 1
        # Aspirin proposed
        assert any(o.rxnorm_code == "1191" for o in cds.proposed_orders)
        # Penicillin allergy blocked with HARD_STOP
        assert any("Penicillin" in b.reason and b.severity == "HARD_STOP" for b in cds.blocked_contraindications)
        # Renal enoxaparin blocked due to eGFR 28.4
        assert any("RENAL_IMPAIRMENT" in b.reason and b.severity == "HARD_STOP" for b in cds.blocked_contraindications)

        # 3. Cryptographic Hash-Chain Verification
        assert response.audit_ledger_entry is not None
        assert response.audit_ledger_entry["current_row_hash"] != ""
        assert len(response.audit_ledger_entry["current_row_hash"]) == 64

        # Verify the entire ledger's hash-chain validity
        assert ImmutableAuditLedger.verify_chain_integrity() is True

    def test_fastapi_endpoint_post_multimodal_assess(self):
        """Verifies HTTP call to POST /api/v2/encounters/{id}/multimodal-assess."""
        from fastapi.testclient import TestClient
        from app.main import create_app  # type: ignore[import-not-found]

        app = create_app()
        client = TestClient(app)

        enc_id = str(uuid4())
        payload = {
            "clinical_subject_id": str(uuid4()),
            "patient_context": {
                "age_years": 64,
                "biological_sex": "MALE",
                "weight_kg": 82.5,
                "pregnancy_status": "NOT_APPLICABLE",
                "latest_egfr_ml_min": 28.4,
                "active_medications_rxnorm": ["860975"],
                "known_allergies_snomed": ["91936005"],
            },
            "extracted_clinical_entities": [
                {"snomed_code": "29857009", "term": "Substernal chest pain", "assertion": "PRESENT"},
            ],
            "structured_vitals_labs": [
                {"loinc_code": "6598-7", "name": "Troponin T.cardiac", "value": 0.42, "unit": "ng/mL", "reference_high": 0.014},
            ],
            "imaging_waveform_refs": [
                {"modality": "DICOM_CXR", "s3_uri": "s3://mediscan-prod-us-phi/cxr/enc-8821.dcm"},
            ],
        }

        resp = client.post(f"/api/v2/encounters/{enc_id}/multimodal-assess", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["encounter_id"] == enc_id
        assert data["regulatory_classification"] == "CLINICAL_DECISION_SUPPORT_NON_AUTONOMOUS"
        assert len(data["conformal_differential_diagnosis"]) >= 1
        assert "triage_assessment" in data
        assert "audit_ledger_entry" in data
        assert data["audit_ledger_entry"]["current_row_hash"] != ""
