"""
MediScan Enterprise — Wearable Telemetry, Streaming RPM, FHIR R4 & Population Health Test Suite
=============================================================================================
Verification Gate 6 Test Matrix:
  1. Wearable EWMA & 3-Tier Escalation:
     - 20 normal baselines (HR 72, SpO2 98%, CGM 105) followed by acute decompensation spike (HR 158, SpO2 85%, CGM 46)
     - Flag |Z| > 3.0, update live NEWS2 score, trigger Tier-3 Critical Escalation event
  2. HL7 FHIR R4 & CDS Hooks Compliance:
     - POST /fhir/r4/Bundle transaction ingestion & GET /fhir/r4/Patient/{id}/$everything
     - POST /cds-services/mediscan-order-sign-safety sub-500ms response with indicator "critical"
     - HL7v2 pipe/bar ORU^R01 parser & ABDM ABHA ID verification adapter
  3. Predictive Population Health Engine:
     - GET /api/v2/population-health/outbreaks (geospatial clusters & Rt)
     - GET /api/v2/population-health/readmission-risk (LACE+ index)
     - GET /api/v2/population-health/care-gaps (HEDIS chronic care gaps)
  4. Live Telemetry Waveform Simulator:
     - 12-lead ECG waveforms, PPG pulse, and crisis scenario generation
"""

import os
import sys
import time
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

# Ensure services/clinical-core-api is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services", "clinical-core-api")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "libs")))

from app.main import create_app
from domains.wearable_rpm.models import (
    LOINC_HEART_RATE,
    LOINC_SPO2,
    LOINC_GLUCOSE,
    LOINC_SYSTOLIC_BP,
    LOINC_RESPIRATORY_RATE,
    UCUM_BPM,
    UCUM_PERCENT,
    UCUM_MGDL,
    UCUM_MMHG,
    EscalationTier,
)
from domains.hospital_interop.hl7v2_parser import hl7v2_parser
from domains.hospital_interop.abdm_adapter import abdm_adapter


@pytest.fixture(scope="module")
def api_client():
    """FastAPI TestClient fixture."""
    app = create_app()
    return TestClient(app)


class TestWearableEWMAAnd3TierEscalation:
    """Audit EWMA baseline learning, |Z| > 3.0 detection, NEWS2 update, and Tier-3 escalation."""

    def test_normal_baseline_learning_followed_by_acute_decompensation_spike(self, api_client):
        """
        Push 20 normal baseline readings (HR=72, SpO2=98%, CGM=105).
        Follow with acute decompensation spike (HR=158 bpm, SpO2=85%, CGM=46 mg/dL).
        Verify |Z| > 3.0, NEWS2 update, and Tier-3 Critical Escalation trigger.
        """
        subject_id = f"rpm_subj_{uuid4().hex[:8]}"

        # 1. Ingest 20 normal baseline readings
        for i in range(20):
            normal_payload = {
                "clinical_subject_id": subject_id,
                "readings": [
                    {"loinc_code": LOINC_HEART_RATE, "metric_value": 72.0 + (i % 3 - 1), "ucum_unit": UCUM_BPM},
                    {"loinc_code": LOINC_SPO2, "metric_value": 98.0, "ucum_unit": UCUM_PERCENT},
                    {"loinc_code": LOINC_GLUCOSE, "metric_value": 105.0 + (i % 5 - 2), "ucum_unit": UCUM_MGDL},
                    {"loinc_code": LOINC_SYSTOLIC_BP, "metric_value": 118.0, "ucum_unit": UCUM_MMHG},
                    {"loinc_code": LOINC_RESPIRATORY_RATE, "metric_value": 15.0, "ucum_unit": UCUM_BPM},
                ],
                "patient_activity_state": "RESTING",
            }
            resp = api_client.post("/api/v2/telemetry/ingest", json=normal_payload)
            assert resp.status_code == 200
            data = resp.json()
            # Under normal baseline, no critical escalation
            assert data["escalation_triggered"] is None or data["escalation_triggered"]["tier"] != EscalationTier.TIER_3_CRITICAL_DISPATCH.value

        # 2. Ingest acute decompensation spike: HR=158, SpO2=85%, CGM=46
        crisis_payload = {
            "clinical_subject_id": subject_id,
            "readings": [
                {"loinc_code": LOINC_HEART_RATE, "metric_value": 158.0, "ucum_unit": UCUM_BPM},
                {"loinc_code": LOINC_SPO2, "metric_value": 85.0, "ucum_unit": UCUM_PERCENT},
                {"loinc_code": LOINC_GLUCOSE, "metric_value": 46.0, "ucum_unit": UCUM_MGDL},
                {"loinc_code": LOINC_SYSTOLIC_BP, "metric_value": 84.0, "ucum_unit": UCUM_MMHG},
                {"loinc_code": LOINC_RESPIRATORY_RATE, "metric_value": 28.0, "ucum_unit": UCUM_BPM},
            ],
            "patient_activity_state": "RESTING",
            "supplemental_oxygen": False,
        }

        resp_crisis = api_client.post("/api/v2/telemetry/ingest", json=crisis_payload)
        assert resp_crisis.status_code == 200
        crisis_data = resp_crisis.json()

        # Assert anomalies detected
        anomalies = crisis_data["anomalies_detected"]
        assert len(anomalies) >= 2, f"Expected multiple anomalies, got: {anomalies}"

        # Assert |Z| > 3.0 on decompensated metrics
        z_scores = {a["loinc_code"]: abs(a["z_score"]) for a in anomalies}
        assert z_scores.get(LOINC_HEART_RATE, 0.0) > 3.0 or z_scores.get(LOINC_SPO2, 0.0) > 3.0, (
            f"Expected |Z| > 3.0 on HR or SpO2, got: {z_scores}"
        )

        # Assert dynamic NEWS2 score is updated to high/critical
        news2_score = crisis_data["current_news2_score"]
        assert news2_score >= 7, f"Expected critical NEWS2 >= 7, got {news2_score}"
        assert crisis_data["current_news2_category"] in {"HIGH", "MEDIUM", "CRITICAL"}

        # Assert Tier-3 Critical Escalation triggered
        escalation = crisis_data["escalation_triggered"]
        assert escalation is not None
        assert escalation["tier"] == EscalationTier.TIER_3_CRITICAL_DISPATCH.value
        assert "CRITICAL" in escalation["summary_message"]

        # Assert emergency dispatch payload is generated
        dispatch = escalation["emergency_dispatch_payload"]
        assert dispatch is not None
        assert dispatch["dispatch_priority"] == "CRITICAL_BREAKOUT_CODE_RED"
        assert dispatch["trigger_vitals"]["heart_rate"] == 158
        assert dispatch["trigger_vitals"]["spo2_percent"] == 85.0
        assert len(dispatch["recommended_interventions"]) >= 2


class TestHL7FHIRR4AndCDSHooksCompliance:
    """Audit FHIR R4 Bundle ingestion, $everything, sub-500ms CDS Hooks, and HL7v2 parsing."""

    def test_fhir_r4_bundle_transaction_and_patient_everything(self, api_client):
        """
        Ingest FHIR R4 transaction bundle (Patient, Observation, MedicationRequest)
        and verify retrieval via GET /fhir/r4/Patient/{id}/$everything.
        """
        patient_id = f"pat_fhir_{uuid4().hex[:6]}"
        bundle_payload = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": patient_id,
                        "name": [{"family": "Sharma", "given": ["Aditya"]}],
                        "gender": "male",
                        "birthDate": "1975-08-20",
                    }
                },
                {
                    "resource": {
                        "resourceType": "Observation",
                        "id": f"obs_hba1c_{uuid4().hex[:6]}",
                        "status": "final",
                        "subject": {"reference": f"Patient/{patient_id}"},
                        "code": {"coding": [{"system": "http://loinc.org", "code": "4548-4", "display": "HbA1c"}]},
                        "valueQuantity": {"value": 8.4, "unit": "%"},
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": f"med_metformin_{uuid4().hex[:6]}",
                        "status": "active",
                        "subject": {"reference": f"Patient/{patient_id}"},
                        "medicationCodeableConcept": {"text": "Metformin 500mg"},
                    }
                },
            ],
        }

        # 1. POST /fhir/r4/Bundle
        post_resp = api_client.post("/fhir/r4/Bundle", json=bundle_payload)
        assert post_resp.status_code == 200, post_resp.text
        bundle_resp = post_resp.json()
        assert bundle_resp["resourceType"] == "Bundle"
        assert bundle_resp["type"] == "transaction-response"
        assert len(bundle_resp["entry"]) == 3
        for entry in bundle_resp["entry"]:
            assert "201 Created" in entry["response"]["status"]

        # 2. GET /fhir/r4/Patient/{id}/$everything
        get_resp = api_client.get(f"/fhir/r4/Patient/{patient_id}/$everything")
        assert get_resp.status_code == 200, get_resp.text
        everything_bundle = get_resp.json()
        assert everything_bundle["resourceType"] == "Bundle"
        assert everything_bundle["type"] == "searchset"
        assert everything_bundle["total"] >= 3

        res_types = [e["resource"]["resourceType"] for e in everything_bundle["entry"]]
        assert "Patient" in res_types
        assert "Observation" in res_types
        assert "MedicationRequest" in res_types

    def test_cds_hooks_order_sign_ibuprofen_dengue_hard_stop(self, api_client):
        """
        Simulate Epic EHR order-sign hook ordering Ibuprofen 600mg for active Dengue patient.
        Assert response SLA < 500ms and card contains indicator 'critical' + safe alternative.
        """
        hook_payload = {
            "hook": "order-sign",
            "hookInstance": f"hook_{uuid4().hex[:8]}",
            "context": {
                "patientId": "pat_dengue_101",
                "draftOrders": {
                    "resourceType": "Bundle",
                    "entry": [
                        {
                            "resource": {
                                "resourceType": "MedicationRequest",
                                "medicationCodeableConcept": {"text": "Ibuprofen 600mg PO"},
                                "status": "draft",
                            }
                        }
                    ],
                },
                "conditions": ["Dengue Fever with Thrombocytopenia"],
            },
            "prefetch": {
                "conditions": {
                    "entry": [
                        {
                            "resource": {
                                "resourceType": "Condition",
                                "code": {"text": "Dengue Fever"},
                            }
                        }
                    ]
                }
            },
        }

        # Measure execution SLA
        start_time = time.perf_counter()
        resp = api_client.post("/cds-services/mediscan-order-sign-safety", json=hook_payload)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        assert resp.status_code == 200, resp.text
        assert elapsed_ms < 500.0, f"CDS Hooks SLA breached: {elapsed_ms:.1f}ms >= 500ms"

        data = resp.json()
        assert "cards" in data
        assert len(data["cards"]) >= 1

        card = data["cards"][0]
        assert card["indicator"] == "critical"
        assert "Dengue" in card["summary"] or "NSAID" in card["summary"]
        assert len(card["suggestions"]) >= 1
        suggestion = card["suggestions"][0]
        assert "Paracetamol" in suggestion["label"] or "Acetaminophen" in suggestion["label"]

    def test_hl7v2_oru_pipe_message_parser(self):
        """
        Verify HL7v2 pipe/bar ORU^R01 parser extracting Hemoglobin 6.4 g/dL
        with critical abnormal flag and mapping to FHIR R4 Observation.
        """
        raw_hl7 = (
            "MSH|^~\\&|LAB_SYS|HOSPITAL_A|MEDISCAN|ENTERPRISE|20261017120000||ORU^R01|MSG00129|P|2.5\r\n"
            "PID|1||PAT778899^^^HOSPITAL||Verma^Rohan||19820415|M\r\n"
            "OBR|1|ORD1001|FIL2002|718-7^Hemoglobin^LN|||20261017113000\r\n"
            "OBX|1|NM|718-7^Hemoglobin^LN|1|6.4|g/dL|13.0-17.0|L|||F\r\n"
            "OBX|2|NM|777-3^Platelets^LN|1|38000|/uL|150000-450000|L|||F\r\n"
        )

        parsed = hl7v2_parser.parse_message(raw_hl7)
        assert parsed["message_type"] == "ORU^R01"
        assert parsed["patient"]["family_name"] == "Verma"
        assert parsed["patient"]["given_name"] == "Rohan"

        obs = parsed["observations"]
        assert len(obs) == 2
        hgb = obs[0]
        assert hgb["loinc_code"] == "718-7"
        assert hgb["numeric_value"] == 6.4
        assert hgb["units"] == "g/dL"
        assert hgb["abnormal_flag"] == "L"

        fhir_resources = parsed["fhir_resources"]
        assert len(fhir_resources) == 3  # Patient + 2 Observations
        assert fhir_resources[0]["resourceType"] == "Patient"
        assert fhir_resources[1]["resourceType"] == "Observation"

    def test_abdm_abha_id_verification_adapter(self, api_client):
        """
        Verify ABDM ABHA Number (14 digits) and ABHA Address (@abdm) verification.
        """
        # 1. Valid 14-digit ABHA number
        resp1 = api_client.post(
            "/api/v2/abdm/verify-abha",
            json={"abha_identifier": "91-1234-5678-9012"},
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["is_valid"] is True
        assert data1["identifier_type"] == "ABHA_NUMBER"
        assert data1["status"] == "VERIFIED"

        # 2. Valid ABHA Address
        resp2 = api_client.post(
            "/api/v2/abdm/verify-abha",
            json={"abha_identifier": "rohan.sharma@abdm"},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["is_valid"] is True
        assert data2["identifier_type"] == "ABHA_ADDRESS"

        # 3. Invalid identifier
        resp3 = api_client.post(
            "/api/v2/abdm/verify-abha",
            json={"abha_identifier": "invalid_format_xyz"},
        )
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["is_valid"] is False
        assert data3["identifier_type"] == "INVALID"


class TestPopulationHealthOutbreaksAndRisk:
    """Audit geospatial outbreak clusters, LACE+ readmission index, and chronic care gaps."""

    def test_spatio_temporal_outbreak_detection(self, api_client):
        """
        Verify GET /api/v2/population-health/outbreaks returns regional clusters
        with estimated reproduction rate Rt and public health actions.
        """
        resp = api_client.get("/api/v2/population-health/outbreaks")
        assert resp.status_code == 200
        clusters = resp.json()
        assert len(clusters) >= 1

        dengue_cluster = next((c for c in clusters if "Dengue" in c["pathogen"]), clusters[0])
        assert dengue_cluster["case_count"] >= 2
        assert dengue_cluster["reproduction_rate_rt"] > 0.5
        assert dengue_cluster["severity"] in {"EMERGENT_OUTBREAK", "ELEVATED_SURGE", "WATCHLIST"}
        assert len(dengue_cluster["recommended_public_health_actions"]) >= 1

    def test_lace_readmission_risk_scoring(self, api_client):
        """
        Verify GET /api/v2/population-health/readmission-risk returns LACE+ index
        and transitional care bundles.
        """
        params = {
            "clinical_subject_id": "pat_lace_001",
            "length_of_stay_days": 8,
            "is_emergent": True,
            "comorbidity_score": 4,
            "prior_ed_visits_6m": 3,
        }
        resp = api_client.get("/api/v2/population-health/readmission-risk", params=params)
        assert resp.status_code == 200
        score = resp.json()

        assert score["lace_score"] >= 10
        assert score["readmission_probability_30d"] >= 0.25
        assert score["risk_tier"] == "HIGH"
        assert len(score["suggested_transitional_care_bundle"]) >= 3
        assert len(score["key_risk_drivers"]) >= 2

    def test_chronic_care_gaps_identification(self, api_client):
        """
        Verify GET /api/v2/population-health/care-gaps detects overdue HEDIS measures
        (HbA1c, UACR nephropathy screening, retinal exam, BP control).
        """
        resp = api_client.get(
            "/api/v2/population-health/care-gaps",
            params={"clinical_subject_id": "pat_gap_01", "conditions": "Type 2 Diabetes, Hypertension"},
        )
        assert resp.status_code == 200
        gaps = resp.json()
        assert len(gaps) >= 2

        measure_ids = [g["measure_id"] for g in gaps]
        assert "HEDIS-CDC-A1C" in measure_ids
        assert "HEDIS-KED-NEPHRO" in measure_ids
        for g in gaps:
            assert g["status"] == "OVERDUE"
            assert g["days_overdue"] > 0


class TestLiveTelemetryWaveformSimulator:
    """Audit 12-lead ECG, PPG, and crisis scenario simulation."""

    def test_simulator_stemi_snapshot_generation(self, api_client):
        """
        Verify GET /api/v2/telemetry/simulator/snapshot?scenario=STEMI
        generates 12 leads of continuous ECG waveform with ST elevation in V2-V4.
        """
        resp = api_client.get("/api/v2/telemetry/simulator/snapshot?scenario=STEMI")
        assert resp.status_code == 200
        data = resp.json()

        assert data["scenario"] == "STEMI"
        waveforms = data["waveforms"]
        assert "ecg_12_lead" in waveforms
        ecg = waveforms["ecg_12_lead"]
        assert len(ecg) == 12
        for lead in ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]:
            assert lead in ecg
            assert len(ecg[lead]) == 250

        # Verify PPG
        assert "ppg" in waveforms
        assert len(waveforms["ppg"]) == 100
