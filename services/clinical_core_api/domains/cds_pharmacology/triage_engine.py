"""
Assertion-Aware Deterministic Triage Engine
===========================================
Replaces legacy severity_detector.py naive substring matching.

Differentiates:
- PRESENT (Active condition/symptom)
- ABSENT / NEGATED (Explicitly denied or ruled out)
- HISTORICAL (Resolved past condition)
- FAMILY_HISTORY (Relative has condition; patient does not)
- HYPOTHETICAL (Scenario / risk discussion)

Fuses:
1. Assertion-gated clinical entities (zero false-positives from negations)
2. Validated NEWS2 score (Scale 1 and Scale 2 for hypercapnia)
3. Emergency Severity Index (ESI v4)
4. qSOFA sepsis screening
5. LOINC-mapped structured critical lab thresholds (glucose, troponin, potassium, platelets, SpO2, BP, creatinine)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import os
import sys
from pathlib import Path

# Ensure root workspace is in sys.path
_workspace_root = Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents) >= 5 else Path(__file__).resolve().parents[2]
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from libs.clinical_calculators.calculators import (
    NEWS2Category,
    calculate_esi_v4,
    calculate_news2,
    calculate_qsofa,
)
from services.clinical_core_api.domains.cds_pharmacology.models import (
    ClinicalEntity,
    StructuredLabObservation,
    TriageEvaluationInput,
    TriageEvaluationOutput,
    TriageSeverityLevel,
    VitalSignsPayload,
)


# ── Critical & Urgent Symptom Knowledge Lexicon ───────────────

CRITICAL_SYMPTOM_PATTERNS = {
    "cardiac_ischemia": [
        "chest pain", "substernal chest pain", "st elevation", "myocardial infarction",
        "crushing chest pain", "radiating chest pain", "angina", "heart attack",
    ],
    "stroke_neurologic": [
        "stroke", "facial droop", "hemiparesis", "unilateral weakness",
        "aphasia", "loss of consciousness", "thunderclap headache", "coma",
    ],
    "respiratory_failure": [
        "respiratory arrest", "severe dyspnea", "stridor", "cyanosis",
        "inability to speak", "gasping", "apnea",
    ],
    "severe_shock_vascular": [
        "anaphylaxis", "aortic dissection", "cardiac arrest", "pulseless",
        "massive hematemesis", "uncontrolled arterial bleed", "septic shock",
    ],
}

URGENT_SYMPTOM_PATTERNS = {
    "moderate_distress": [
        "dyspnea", "wheezing", "shortness of breath", "high fever", "rigors",
        "tachypnea", "tachycardia", "orthopnea", "syncope", "melena",
        "abdominal pain", "severe pain", "bloody stool", "oliguria",
    ],
}

# Non-urgent / mild symptoms
MILD_SYMPTOM_PATTERNS = [
    "mild headache", "headache", "rhinorrhea", "runny nose", "sore throat",
    "mild cough", "fatigue", "dry skin", "constipation", "insomnia", "mild rash",
]


# ── LOINC Critical Lab Threshold Definitions ───────────────────

LOINC_CRITICAL_THRESHOLDS = {
    # Serum Glucose (LOINC 2345-7, 14749-6)
    "2345-7": {"name": "Glucose", "crit_low": 54.0, "crit_high": 400.0, "unit": "mg/dL"},
    "14749-6": {"name": "Glucose", "crit_low": 54.0, "crit_high": 400.0, "unit": "mg/dL"},
    # Troponin T / I (LOINC 6598-7, 10839-9)
    "6598-7": {"name": "Troponin T", "crit_low": None, "crit_high": 0.04, "unit": "ng/mL"},
    "10839-9": {"name": "Troponin I", "crit_low": None, "crit_high": 0.04, "unit": "ng/mL"},
    # Potassium (LOINC 2823-3)
    "2823-3": {"name": "Potassium", "crit_low": 2.8, "crit_high": 6.0, "unit": "mmol/L"},
    # Platelets (LOINC 777-3)
    "777-3": {"name": "Platelets", "crit_low": 20000.0, "crit_high": None, "unit": "/uL"},
    # SpO2 (LOINC 59408-5)
    "59408-5": {"name": "Oxygen Saturation", "crit_low": 88.0, "crit_high": None, "unit": "%"},
    # Systolic BP (LOINC 8480-6)
    "8480-6": {"name": "Systolic BP", "crit_low": 80.0, "crit_high": 200.0, "unit": "mmHg"},
    # Serum Creatinine (LOINC 2160-0)
    "2160-0": {"name": "Creatinine", "crit_low": None, "crit_high": 4.0, "unit": "mg/dL"},
}


class AssertionAwareTriageEngine:
    """
    Deterministic triage decision support engine replacing naive regex/substring
    severity detection.
    """

    def __init__(self):
        self.critical_patterns = CRITICAL_SYMPTOM_PATTERNS
        self.urgent_patterns = URGENT_SYMPTOM_PATTERNS
        self.loinc_thresholds = LOINC_CRITICAL_THRESHOLDS

    def _matches_any(self, text: str, patterns: list[str]) -> bool:
        norm = text.strip().lower()
        for p in patterns:
            # Whole word or exact phrase match, not loose random substring
            if re.search(r"\b" + re.escape(p) + r"\b", norm):
                return True
        return False

    def evaluate_triage(self, input_data: TriageEvaluationInput) -> TriageEvaluationOutput:
        """
        Executes multi-axial clinical triage:
        1. Assertion-gated entity classification
        2. Critical lab biomarker threshold evaluation
        3. Physiological vital sign scoring (NEWS2 & qSOFA)
        4. Emergency Severity Index (ESI v4) synthesis
        """
        triggering_factors: list[str] = []
        suppressed_factors: list[str] = []

        has_critical_present_symptom = False
        has_urgent_present_symptom = False
        has_mild_present_symptom = False

        # ── 1. Evaluate Clinical Entities with Assertion Awareness ──
        for entity in input_data.clinical_entities:
            term = entity.term.strip()
            term_lower = term.lower()

            # Check if entity is negated or not currently active in patient
            if entity.is_negated():
                suppressed_factors.append(
                    f"NEGATED: Patient denies / absent '{term}' [Assertion: {entity.assertion}]"
                )
                continue

            if entity.is_historical_or_family():
                suppressed_factors.append(
                    f"NON-ACUTE CONTEXT: '{term}' [Assertion: {entity.assertion}] — excluded from acute triage elevation"
                )
                continue

            # If PRESENT: Check symptom severity
            if entity.is_present():
                is_crit = False
                for cat, pats in self.critical_patterns.items():
                    if self._matches_any(term_lower, pats):
                        has_critical_present_symptom = True
                        is_crit = True
                        triggering_factors.append(
                            f"ACUTE CRITICAL SYMPTOM: '{term}' matches {cat.replace('_', ' ').title()}"
                        )
                        break

                if not is_crit:
                    for cat, pats in self.urgent_patterns.items():
                        if self._matches_any(term_lower, pats):
                            has_urgent_present_symptom = True
                            triggering_factors.append(
                                f"ACUTE URGENT SYMPTOM: '{term}' matches {cat.replace('_', ' ').title()}"
                            )
                            break

                if not is_crit and not has_urgent_present_symptom:
                    has_mild_present_symptom = True

        # ── 2. Evaluate Structured Lab Critical Thresholds ──────────
        has_critical_lab = False
        lab_details: list[dict] = []

        for lab in input_data.lab_observations:
            loinc = lab.loinc_code.strip()
            val = float(lab.value)
            thresh = self.loinc_thresholds.get(loinc)

            direction = "NORMAL"
            is_crit = False

            if thresh:
                if thresh["crit_low"] is not None and val < thresh["crit_low"]:
                    is_crit = True
                    direction = "CRITICAL_LOW"
                    has_critical_lab = True
                    triggering_factors.append(
                        f"CRITICAL LAB VALUE: {thresh['name']} ({loinc}) = {val} {lab.unit} "
                        f"[Panic Low Threshold < {thresh['crit_low']}]"
                    )
                elif thresh["crit_high"] is not None and val > thresh["crit_high"]:
                    is_crit = True
                    direction = "CRITICAL_HIGH"
                    has_critical_lab = True
                    triggering_factors.append(
                        f"CRITICAL LAB VALUE: {thresh['name']} ({loinc}) = {val} {lab.unit} "
                        f"[Panic High Threshold > {thresh['crit_high']}]"
                    )

            lab_details.append({
                "loinc": loinc,
                "name": lab.test_name,
                "value": val,
                "unit": lab.unit,
                "critical": is_crit,
                "direction": direction,
            })

        # ── 3. Evaluate Physiological Vital Signs (NEWS2 & qSOFA) ───
        vitals = input_data.vital_signs or VitalSignsPayload()

        news2_res = calculate_news2(
            respiratory_rate=vitals.respiratory_rate,
            spo2_percent=vitals.spo2_percent,
            supplemental_oxygen=vitals.supplemental_oxygen,
            hypercapnic_respiratory_failure=vitals.hypercapnic_respiratory_failure,
            systolic_bp=vitals.systolic_bp,
            heart_rate=vitals.heart_rate,
            consciousness_avpu=vitals.consciousness_avpu,
            temperature_celsius=vitals.temperature_celsius,
        )

        qsofa_res = calculate_qsofa(
            respiratory_rate=vitals.respiratory_rate or 16,
            systolic_bp=vitals.systolic_bp or 120,
            altered_mentation=(vitals.consciousness_avpu.upper() not in ("ALERT", "A")),
        )

        if news2_res.is_critical:
            triggering_factors.append(
                f"HIGH PHYSIOLOGICAL RISK: NEWS2 Score = {news2_res.total_score} (Category: {news2_res.category.value})"
            )

        if qsofa_res.is_high_risk_sepsis:
            triggering_factors.append(
                f"SEPSIS RISK: qSOFA Score = {qsofa_res.score} (>= 2 criteria met)"
            )

        # ── 4. Synthesize ESI Level & Triage Severity ───────────────
        # Step A: Resuscitation (ESI 1)
        requires_lifesaving = (
            vitals.consciousness_avpu.upper() in ("UNRESPONSIVE", "U")
            or (vitals.respiratory_rate is not None and vitals.respiratory_rate <= 6)
            or (vitals.spo2_percent is not None and vitals.spo2_percent < 80.0)
        )

        # Step B: Emergent / High Risk (ESI 2)
        is_emergent_risk = (
            has_critical_present_symptom
            or has_critical_lab
            or news2_res.total_score >= 7
            or qsofa_res.is_high_risk_sepsis
            or (vitals.consciousness_avpu.upper() in ("VOICE", "PAIN", "CONFUSION"))
        )

        # Step C: Resource estimation
        expected_resources = 0
        if input_data.lab_observations:
            expected_resources += 1
        if has_urgent_present_symptom:
            expected_resources += 2
        elif has_mild_present_symptom:
            expected_resources += 1

        esi_res = calculate_esi_v4(
            requires_immediate_lifesaving=requires_lifesaving,
            is_high_risk_or_confused_or_severe_pain=is_emergent_risk,
            expected_resources=expected_resources,
            vital_signs_danger_zone=(news2_res.total_score >= 5),
        )

        # Map to overarching Triage Severity Level
        if esi_res.level == 1:
            severity = TriageSeverityLevel.RESUSCITATION
            action = "ACTIVATE RESUSCITATION TEAM: Continuous cardiac/SpO2 monitoring, immediate IV access, airway prep."
        elif esi_res.level == 2:
            severity = TriageSeverityLevel.EMERGENT
            action = "IMMEDIATE PHYSICIAN ASSESSMENT: Urgent bed placement, STAT bedside diagnostics, continuous monitoring."
        elif esi_res.level == 3:
            severity = TriageSeverityLevel.URGENT
            action = "EXPEDITED CLINICAL REVIEW: Place in urgent queue; initiate diagnostic workup."
        elif esi_res.level == 4:
            severity = TriageSeverityLevel.LESS_URGENT
            action = "STANDARD CLINICAL EVALUATION: Routine triage queue; single diagnostic or therapeutic resource."
        else:
            severity = TriageSeverityLevel.NON_URGENT
            action = "ROUTINE EVALUATION / AMBULATORY CARE: Patient education, prescription refill, or discharge instructions."

        is_critical = severity in (TriageSeverityLevel.RESUSCITATION, TriageSeverityLevel.EMERGENT)

        return TriageEvaluationOutput(
            evaluation_id=uuid4(),
            severity_level=severity,
            is_critical=is_critical,
            news2_total=news2_res.total_score,
            news2_category=news2_res.category.value,
            esi_level=int(esi_res.level.value),
            qsofa_score=qsofa_res.score,
            is_high_risk_sepsis=qsofa_res.is_high_risk_sepsis,
            triggering_factors=triggering_factors,
            suppressed_factors=suppressed_factors,
            recommended_clinical_action=action,
            component_breakdown={
                "news2_components": news2_res.component_scores,
                "news2_scale": news2_res.scale_used,
                "qsofa_criteria": qsofa_res.criteria_met,
                "esi_rationale": esi_res.decision_rationale,
                "labs_evaluated": lab_details,
            },
        )
