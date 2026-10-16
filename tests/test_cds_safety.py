"""
MediScan Enterprise — Clinical Safety, Triage & Pharmacology CDS Test Suite
=============================================================================
Verification Gate 2: Deterministic Clinical Math, Triage & Pharmacology Audit

Tests:
1. Physiological Calculator Precision (CKD-EPI 2021 eGFR, Cockcroft-Gault, NEWS2, ESI v4, qSOFA, Mosteller BSA, Pediatric Ceilings)
2. Property-Based Safety Invariants (Hypothesis: Ceilings never breached, eGFR positivity)
3. Negation & Context Immunity Triage (Replacing severity_detector.py naive substring bug)
4. Neuro-Symbolic Pharmacology Gatekeeper (Replacing drug_recommender.py prescribing hazard):
   - Test A: Dengue Fever NSAID Hard-Stop
   - Test B: Renal Failure Metformin Hard-Stop & Sitagliptin Dose-Adjustment
   - Test C: Penicillin Allergy Cross-Reactivity Hard-Stop on Amoxicillin-Clavulanate
   - Test D: Critical Drug-Drug Interactions (Warfarin + Rivaroxaban / Aspirin)
   - Test E: Asthma Non-Selective Beta-Blocker Hard-Stop
"""

import math
import sys
from pathlib import Path

# Add project root to sys.path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pytest
from hypothesis import given, strategies as st, settings

from libs.clinical_calculators.calculators import (
    BiologicalSex,
    NEWS2Category,
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
    SafetyVerdict,
    StructuredLabObservation,
    TriageEvaluationInput,
    TriageSeverityLevel,
    VitalSignsPayload,
)
from services.clinical_core_api.domains.cds_pharmacology.triage_engine import AssertionAwareTriageEngine


# ═══════════════════════════════════════════════════════════════════════
# 1. PHYSIOLOGICAL CALCULATORS: PRECISION & CLINICAL VALIDITY
# ═══════════════════════════════════════════════════════════════════════

class TestPhysiologicalCalculators:
    """Rigorous mathematical tests for validated physiological equations."""

    def test_ckd_epi_2021_64yo_male_severe_decrease(self):
        """
        Verification Gate 2 Specification:
        64yo Male with Creatinine 2.4 mg/dL -> eGFR calculated accurately
        (~28.4 to 29.4 mL/min/1.73m^2) and staged as CKD Stage G4 (Severely decreased).
        """
        res = calculate_ckd_epi_2021(
            serum_creatinine_mg_dl=2.4,
            age_years=64,
            biological_sex="MALE",
        )
        assert 28.0 <= res.egfr_ml_min_1_73m2 <= 30.0
        assert res.ckd_stage == "G4"
        assert "Severely decreased" in res.stage_description
        assert res.requires_dose_adjustment is True
        assert res.contraindicated_metformin is True
        assert res.is_kidney_failure is False

    def test_ckd_epi_2021_female_normal_and_failure(self):
        """Test female parameters and stage G1 vs G5."""
        # 30yo Female, Scr 0.6 -> Normal G1
        normal_res = calculate_ckd_epi_2021(0.6, 30, BiologicalSex.FEMALE)
        assert normal_res.egfr_ml_min_1_73m2 >= 90.0
        assert normal_res.ckd_stage == "G1"
        assert normal_res.contraindicated_metformin is False

        # 75yo Female, Scr 4.5 -> Kidney failure G5
        failure_res = calculate_ckd_epi_2021(4.5, 75, "FEMALE")
        assert failure_res.egfr_ml_min_1_73m2 < 15.0
        assert failure_res.ckd_stage == "G5"
        assert failure_res.is_kidney_failure is True

    def test_cockcroft_gault_crcl(self):
        """Test Cockcroft-Gault formula for male and female."""
        # 64yo Male, 70kg, Scr 2.4 -> (140-64)*70 / (72*2.4) = 5320 / 172.8 = 30.79 mL/min
        cg_male = calculate_cockcroft_gault(
            serum_creatinine_mg_dl=2.4,
            age_years=64,
            weight_kg=70.0,
            biological_sex="MALE",
        )
        assert round(cg_male.crcl_ml_min, 1) == 30.8
        assert cg_male.is_impaired is True

        # Female factor 0.85 -> 30.79 * 0.85 = 26.17 mL/min
        cg_female = calculate_cockcroft_gault(
            serum_creatinine_mg_dl=2.4,
            age_years=64,
            weight_kg=70.0,
            biological_sex="FEMALE",
        )
        assert round(cg_female.crcl_ml_min, 1) == 26.2

    def test_news2_critical_patient_score(self):
        """
        Verification Gate 2 Specification:
        Patient with:
        - RR 26 (score 3)
        - SpO2 89% on room air (score 3)
        - Supplemental O2 False (score 0)
        - Systolic BP 85 mmHg (score 3)
        - HR 135 bpm (score 3)
        - Temp 38.9°C (score 1)
        - Alert (score 0)
        -> Total = 3+3+0+3+3+1+0 = 13 >= 11 (CRITICAL / High Clinical Risk).
        """
        res = calculate_news2(
            respiratory_rate=26,
            spo2_percent=89.0,
            supplemental_oxygen=False,
            systolic_bp=85,
            heart_rate=135,
            temperature_celsius=38.9,
            consciousness_avpu="ALERT",
        )
        assert res.total_score == 13
        assert res.total_score >= 11
        assert res.category == NEWS2Category.HIGH
        assert res.is_critical is True
        assert "EMERGENCY / HIGH RISK" in res.recommended_clinical_response

    def test_news2_scale_2_hypercapnic(self):
        """Test Scale 2 for hypercapnic respiratory failure (target 88-92%)."""
        # SpO2 90% on room air in hypercapnic patient should score 0 on Scale 2
        res = calculate_news2(
            respiratory_rate=16,
            spo2_percent=90.0,
            supplemental_oxygen=False,
            hypercapnic_respiratory_failure=True,
            systolic_bp=120,
            heart_rate=72,
            temperature_celsius=37.0,
        )
        assert res.component_scores.get("oxygen_saturation") == 0
        assert res.total_score == 0
        assert res.category == NEWS2Category.LOW

    def test_qsofa_sepsis_scoring(self):
        """Test qSOFA sepsis criteria (RR >= 22, SBP <= 100, AMS)."""
        # All 3 met -> score 3, high risk
        high_risk = calculate_qsofa(respiratory_rate=24, systolic_bp=90, altered_mentation=True)
        assert high_risk.score == 3
        assert high_risk.is_high_risk_sepsis is True

        # Normal -> score 0
        normal = calculate_qsofa(respiratory_rate=14, systolic_bp=125, altered_mentation=False)
        assert normal.score == 0
        assert normal.is_high_risk_sepsis is False

    def test_pediatric_dosing_ceiling_enforcement(self):
        """
        Verification Gate 2 Specification:
        A 45 kg pediatric patient calculated on mg/kg regimen never exceeds
        the hardcoded adult maximum single dose.
        """
        # 45 kg child dosed at 20 mg/kg -> calculated = 900 mg
        # Adult max single dose = 500 mg
        # Must be strictly capped at 500 mg
        dose_res = calculate_pediatric_dose_with_adult_ceiling(
            weight_kg=45.0,
            dose_mg_per_kg=20.0,
            adult_max_single_dose_mg=500.0,
        )
        assert dose_res.calculated_dose_mg == 900.0
        assert dose_res.final_dose_mg == 500.0
        assert dose_res.is_capped_by_adult_ceiling is True
        assert len(dose_res.warnings) == 1
        assert "SAFETY CEILING TRIGGERED" in dose_res.warnings[0]

        # Case where calculated dose is below ceiling
        safe_dose = calculate_pediatric_dose_with_adult_ceiling(
            weight_kg=15.0,
            dose_mg_per_kg=10.0,
            adult_max_single_dose_mg=500.0,
        )
        assert safe_dose.calculated_dose_mg == 150.0
        assert safe_dose.final_dose_mg == 150.0
        assert safe_dose.is_capped_by_adult_ceiling is False

    def test_mosteller_bsa_calculation(self):
        """Test Mosteller BSA formula: sqrt(h*w/3600)."""
        bsa = calculate_mosteller_bsa(height_cm=180.0, weight_kg=80.0)
        expected = math.sqrt((180.0 * 80.0) / 3600.0)
        assert bsa.bsa_m2 == round(expected, 3)


# ═══════════════════════════════════════════════════════════════════════
# 2. PROPERTY-BASED TESTS (HYPOTHESIS)
# ═══════════════════════════════════════════════════════════════════════

class TestPropertyBasedSafetyInvariants:
    """Hypothesis property-based generative safety tests."""

    @given(
        weight=st.floats(min_value=1.0, max_value=120.0),
        mg_per_kg=st.floats(min_value=0.1, max_value=100.0),
        adult_ceiling=st.floats(min_value=10.0, max_value=2000.0),
    )
    @settings(max_examples=100)
    def test_pediatric_dose_never_exceeds_adult_ceiling(self, weight, mg_per_kg, adult_ceiling):
        """Invariant: Final pediatric dose <= adult_max_single_dose_mg unconditionally."""
        res = calculate_pediatric_dose_with_adult_ceiling(
            weight_kg=weight,
            dose_mg_per_kg=mg_per_kg,
            adult_max_single_dose_mg=adult_ceiling,
        )
        assert res.final_dose_mg <= adult_ceiling + 1e-6
        if res.calculated_dose_mg > adult_ceiling:
            assert res.is_capped_by_adult_ceiling is True
            assert res.final_dose_mg == adult_ceiling

    @given(
        scr=st.floats(min_value=0.2, max_value=15.0),
        age=st.integers(min_value=18, max_value=105),
        sex=st.sampled_from(["MALE", "FEMALE"]),
    )
    @settings(max_examples=100)
    def test_egfr_strictly_positive_and_monotonic_with_creatinine(self, scr, age, sex):
        """Invariant: eGFR is always strictly positive (> 0) and decreases as Scr rises."""
        res = calculate_ckd_epi_2021(scr, age, sex)
        assert res.egfr_ml_min_1_73m2 > 0.0

        higher_scr_res = calculate_ckd_epi_2021(scr + 1.0, age, sex)
        assert higher_scr_res.egfr_ml_min_1_73m2 <= res.egfr_ml_min_1_73m2


# ═══════════════════════════════════════════════════════════════════════
# 3. ASSERTION-AWARE TRIAGE: NEGATION & CONTEXT IMMUNITY
# ═══════════════════════════════════════════════════════════════════════

class TestAssertionAwareTriageEngine:
    """Tests replacing legacy severity_detector.py naive substring matching."""

    @pytest.fixture
    def engine(self):
        return AssertionAwareTriageEngine()

    def test_negation_and_family_history_immunity(self, engine):
        """
        Verification Gate 2 Specification:
        Pass:
        - {"term": "chest pain", "assertion": "ABSENT"}
        - {"term": "stroke", "assertion": "FAMILY_HISTORY"}
        - {"term": "mild headache", "assertion": "PRESENT"}
        Assert:
        - Resulting severity is NOT CRITICAL.
        - De-escalated into suppressed_factors.
        """
        payload = TriageEvaluationInput(
            clinical_entities=[
                ClinicalEntity(term="chest pain", assertion="ABSENT"),
                ClinicalEntity(term="stroke", assertion="FAMILY_HISTORY"),
                ClinicalEntity(term="mild headache", assertion="PRESENT"),
            ],
            vital_signs=VitalSignsPayload(
                heart_rate=76,
                systolic_bp=122,
                respiratory_rate=14,
                temperature_celsius=36.8,
                spo2_percent=98.0,
                consciousness_avpu="ALERT",
            ),
        )

        output = engine.evaluate_triage(payload)

        # Legacy substring bug flagged "stroke" & "chest pain" as CRITICAL emergency!
        # Our engine must NOT be critical!
        assert output.is_critical is False
        assert output.severity_level in (TriageSeverityLevel.LESS_URGENT, TriageSeverityLevel.NON_URGENT)
        assert output.esi_level >= 4
        assert len(output.suppressed_factors) >= 2
        assert any("chest pain" in s for s in output.suppressed_factors)
        assert any("stroke" in s for s in output.suppressed_factors)

    def test_active_critical_symptom_triggers_emergent_severity(self, engine):
        """When chest pain is PRESENT, emergent severity must trigger."""
        payload = TriageEvaluationInput(
            clinical_entities=[
                ClinicalEntity(term="crushing chest pain", assertion="PRESENT"),
                ClinicalEntity(term="diaphoresis", assertion="PRESENT"),
            ],
            vital_signs=VitalSignsPayload(
                heart_rate=98,
                systolic_bp=135,
                respiratory_rate=18,
                spo2_percent=96.0,
                consciousness_avpu="ALERT",
            ),
        )

        output = engine.evaluate_triage(payload)
        assert output.is_critical is True
        assert output.severity_level == TriageSeverityLevel.EMERGENT
        assert output.esi_level == 2
        assert any("chest pain" in f.lower() for f in output.triggering_factors)

    def test_critical_lab_thresholds_trigger_escalation(self, engine):
        """Panic lab values (Troponin, Glucose, Potassium) must trigger emergent triage."""
        # Critical Troponin T = 0.15 ng/mL (Cutoff > 0.04)
        payload = TriageEvaluationInput(
            clinical_entities=[
                ClinicalEntity(term="mild indigestion", assertion="PRESENT")
            ],
            lab_observations=[
                StructuredLabObservation(
                    loinc_code="6598-7",
                    test_name="Troponin T",
                    value=0.15,
                    unit="ng/mL",
                )
            ],
        )

        output = engine.evaluate_triage(payload)
        assert output.is_critical is True
        assert output.severity_level == TriageSeverityLevel.EMERGENT
        assert any("Troponin T" in f for f in output.triggering_factors)


# ═══════════════════════════════════════════════════════════════════════
# 4. NEURO-SYMBOLIC PHARMACOLOGY SAFETY GATEKEEPER
# ═══════════════════════════════════════════════════════════════════════

class TestPharmacologyGatekeeper:
    """Tests replacing legacy drug_recommender.py prescribing hazards."""

    @pytest.fixture
    def gatekeeper(self):
        return PharmacologyGatekeeper()

    def test_gate_a_dengue_fever_nsaid_hard_stop(self, gatekeeper):
        """
        Verification Gate 2 Specification (Test A - Dengue):
        Assert that Aspirin and Ibuprofen (NSAIDs) are HARD_STOP blocked
        due to hemorrhage / thrombocytopenia risk in Dengue Fever.
        """
        for nsaid in ["Aspirin", "Ibuprofen"]:
            req = MedicationEvaluationRequest(
                proposed_drug_name=nsaid,
                diagnosed_diseases=[
                    {"name": "Dengue Fever", "icd11": "1D20", "snomed_id": "38362002"}
                ],
            )
            resp = gatekeeper.evaluate_safety(req)
            assert resp.safety_verdict == SafetyVerdict.HARD_STOP_CONTRAINDICATION
            assert len(resp.disease_contraindications) >= 1
            assert "BLEEDING HAZARD" in resp.disease_contraindications[0].clinical_hazard
            assert any("DENGUE" in reason.upper() for reason in resp.hard_stop_reasons)

    def test_gate_b_renal_failure_metformin_and_sitagliptin(self, gatekeeper):
        """
        Verification Gate 2 Specification (Test B - Renal Failure):
        Assert that for a patient with eGFR = 22 mL/min/1.73m^2 (CKD Stage G4):
        - Metformin is HARD_STOP blocked (lactic acidosis risk).
        - Sitagliptin is dose-adjusted (reduce to 25 mg daily).
        """
        # 1. Metformin check
        metformin_req = MedicationEvaluationRequest(
            proposed_drug_name="Metformin",
            patient_egfr=22.0,
        )
        metformin_resp = gatekeeper.evaluate_safety(metformin_req)
        assert metformin_resp.safety_verdict == SafetyVerdict.HARD_STOP_CONTRAINDICATION
        assert any("METFORMIN" in r.upper() and "EGFR" in r.upper() for r in metformin_resp.hard_stop_reasons)

        # 2. Sitagliptin check
        sitagliptin_req = MedicationEvaluationRequest(
            proposed_drug_name="Sitagliptin",
            patient_egfr=22.0,
        )
        sitagliptin_resp = gatekeeper.evaluate_safety(sitagliptin_req)
        assert sitagliptin_resp.safety_verdict == SafetyVerdict.REQUIRES_ADJUSTMENT
        assert len(sitagliptin_resp.hard_stop_reasons) == 0
        assert len(sitagliptin_resp.renal_alerts) == 1
        assert sitagliptin_resp.renal_alerts[0].is_hard_stop is False
        assert "25 mg daily" in sitagliptin_resp.renal_alerts[0].dosing_guidance

    def test_gate_c_penicillin_allergy_cross_reactivity_hard_stop(self, gatekeeper):
        """
        Verification Gate 2 Specification (Test C - Allergy Cross-Reactivity):
        Assert that a patient with documented Penicillin allergy (SNOMED: 91936005)
        receives a HARD_STOP block on Amoxicillin-Clavulanate.
        """
        req = MedicationEvaluationRequest(
            proposed_drug_name="Amoxicillin-Clavulanate",
            known_allergies=[
                {"name": "Penicillin", "snomed_id": "91936005"}
            ],
        )
        resp = gatekeeper.evaluate_safety(req)
        assert resp.safety_verdict == SafetyVerdict.HARD_STOP_CONTRAINDICATION
        assert len(resp.allergy_alerts) >= 1
        assert resp.allergy_alerts[0].cross_reactivity_class == "PENICILLIN"
        assert resp.allergy_alerts[0].is_hard_stop is True
        assert any("PENICILLIN" in r.upper() for r in resp.hard_stop_reasons)

    def test_gate_d_drug_drug_interactions(self, gatekeeper):
        """Test critical and major drug-drug interactions."""
        # Warfarin + Rivaroxaban -> CONTRAINDICATED
        ddi_req1 = MedicationEvaluationRequest(
            proposed_drug_name="Rivaroxaban",
            active_medications=[{"name": "Warfarin", "rxnorm_cui": "11289"}],
        )
        resp1 = gatekeeper.evaluate_safety(ddi_req1)
        assert resp1.safety_verdict == SafetyVerdict.HARD_STOP_CONTRAINDICATION
        assert any("DDI CONTRAINDICATION" in r for r in resp1.hard_stop_reasons)

        # Lisinopril + Spironolactone -> MAJOR (hyperkalemia)
        ddi_req2 = MedicationEvaluationRequest(
            proposed_drug_name="Spironolactone",
            active_medications=[{"name": "Lisinopril", "rxnorm_cui": "29046"}],
        )
        resp2 = gatekeeper.evaluate_safety(ddi_req2)
        assert resp2.safety_verdict == SafetyVerdict.REQUIRES_ADJUSTMENT
        assert any("hyperkalemia" in a.mechanism.lower() for a in resp2.ddi_alerts)

    def test_gate_e_asthma_beta_blocker_contraindication(self, gatekeeper):
        """Test non-selective beta-blocker contraindication in asthma."""
        req = MedicationEvaluationRequest(
            proposed_drug_name="Carvedilol",
            diagnosed_diseases=[{"name": "Acute Asthma Exacerbation", "snomed_id": "304527002"}],
        )
        resp = gatekeeper.evaluate_safety(req)
        assert resp.safety_verdict == SafetyVerdict.HARD_STOP_CONTRAINDICATION
        assert any("BRONCHOSPASM" in r for r in resp.hard_stop_reasons)

    def test_safe_medication_passes_all_checks(self, gatekeeper):
        """Verify normal safe medication order passes all checks."""
        req = MedicationEvaluationRequest(
            proposed_drug_name="Acetaminophen",
            proposed_dosage="500 mg PO Q6H",
            patient_egfr=85.0,
            active_medications=[{"name": "Loratadine"}],
            known_allergies=[{"name": "Penicillin", "snomed_id": "91936005"}],
            diagnosed_diseases=[{"name": "Tension Headache"}],
        )
        resp = gatekeeper.evaluate_safety(req)
        assert resp.safety_verdict == SafetyVerdict.PASSED_ALL_CHECKS
        assert len(resp.hard_stop_reasons) == 0
        assert len(resp.adjustment_reasons) == 0
        assert "VERIFIED SAFE" in resp.clinician_action_required


# ═══════════════════════════════════════════════════════════════════════
# 5. FASTAPI REST API INTEGRATION TESTS (/api/v2/cds/*)
# ═══════════════════════════════════════════════════════════════════════

class TestFastAPICDSEndpoints:
    """Verifies that the clinical-core-api FastAPI router handles CDS requests."""

    @pytest.fixture
    def client(self):
        sys.path.insert(0, str(Path("services/clinical-core-api").resolve()))
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_api_egfr_endpoint(self, client):
        r = client.post(
            "/api/v2/cds/egfr-calculate",
            params={
                "serum_creatinine_mg_dl": 2.4,
                "age_years": 64,
                "biological_sex": "MALE",
                "weight_kg": 70.0,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert 28.0 <= data["egfr_ml_min_1_73m2"] <= 30.0
        assert data["ckd_stage"] == "G4"
        assert data["cockcroft_gault_crcl_ml_min"] == 30.8

    def test_api_dengue_aspirin_hard_stop(self, client):
        r = client.post(
            "/api/v2/cds/medication-safety-check",
            json={
                "proposed_drug_name": "Aspirin",
                "diagnosed_diseases": [{"name": "Dengue Fever", "icd11": "1D20", "snomed_id": "38362002"}],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["safety_verdict"] == "HARD_STOP_CONTRAINDICATION"
        assert len(data["disease_contraindications"]) >= 1

    def test_api_pediatric_dosing_ceiling(self, client):
        r = client.post(
            "/api/v2/cds/pediatric-dosing",
            params={
                "weight_kg": 45.0,
                "dose_mg_per_kg": 20.0,
                "adult_max_single_dose_mg": 500.0,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["calculated_dose_mg"] == 900.0
        assert data["final_dose_mg"] == 500.0
        assert data["is_capped_by_adult_ceiling"] is True

    def test_api_assertion_triage_negation_immunity(self, client):
        r = client.post(
            "/api/v2/cds/assertion-triage",
            json={
                "clinical_entities": [
                    {"term": "chest pain", "assertion": "ABSENT"},
                    {"term": "stroke", "assertion": "FAMILY_HISTORY"},
                    {"term": "mild headache", "assertion": "PRESENT"},
                ],
                "vital_signs": {
                    "heart_rate": 72,
                    "systolic_bp": 120,
                    "respiratory_rate": 14,
                    "temperature_celsius": 36.8,
                    "spo2_percent": 98.0,
                    "consciousness_avpu": "ALERT",
                },
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["is_critical"] is False
        assert data["severity_level"] in ("LESS_URGENT", "NON_URGENT")
