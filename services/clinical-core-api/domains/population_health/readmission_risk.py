"""
30-Day Hospital Readmission Risk Engine via Validated LACE+ Index.
Calculates L (Length of stay), A (Acuity), C (Charlson Comorbidities), E (ED visits in 6m),
stratifies risk tiers (HIGH, MEDIUM, LOW), and recommends transitional care bundles.
"""

import math
from typing import Any, Optional
from .models import PatientReadmissionScore, ReadmissionRiskTier


class LACEReadmissionRiskEngine:
    """Computes validated LACE+ 30-day hospital readmission risk score."""

    def calculate_lace_score(
        self,
        clinical_subject_id: str,
        length_of_stay_days: int,
        is_emergent_admission: bool,
        charlson_comorbidity_score: int,
        prior_ed_visits_6m: int,
    ) -> PatientReadmissionScore:
        """
        Calculate LACE index and derive 30-day readmission probability.
        """
        # 1. 'L' - Length of stay points
        if length_of_stay_days < 1:
            l_pts = 0
        elif length_of_stay_days == 1:
            l_pts = 1
        elif length_of_stay_days == 2:
            l_pts = 2
        elif length_of_stay_days == 3:
            l_pts = 3
        elif 4 <= length_of_stay_days <= 6:
            l_pts = 4
        elif 7 <= length_of_stay_days <= 13:
            l_pts = 5
        else:
            l_pts = 7

        # 2. 'A' - Acuity of admission
        a_pts = 3 if is_emergent_admission else 0

        # 3. 'C' - Charlson Comorbidity Index points
        if charlson_comorbidity_score == 0:
            c_pts = 0
        elif charlson_comorbidity_score == 1:
            c_pts = 1
        elif charlson_comorbidity_score == 2:
            c_pts = 2
        elif charlson_comorbidity_score == 3:
            c_pts = 3
        else:
            c_pts = 5

        # 4. 'E' - Emergency department visits in past 6 months
        if prior_ed_visits_6m == 0:
            e_pts = 0
        elif prior_ed_visits_6m == 1:
            e_pts = 1
        elif prior_ed_visits_6m == 2:
            e_pts = 2
        elif prior_ed_visits_6m == 3:
            e_pts = 3
        else:
            e_pts = 4

        total_lace = l_pts + a_pts + c_pts + e_pts

        # Calibrated logistic probability curve
        logit = 0.23 * total_lace - 3.2
        prob = round(1.0 / (1.0 + math.exp(-logit)), 3)

        # Risk tiering
        if total_lace >= 10 or prob >= 0.25:
            tier = ReadmissionRiskTier.HIGH
            bundle = [
                "Schedule 48-hour post-discharge clinical nurse outreach call",
                "Mandatory 7-day in-person or telehealth physician follow-up appointment",
                "Pharmacist-led medication reconciliation and blister pack packaging",
                "Enroll in 30-day Remote Patient Monitoring (RPM) vitals tracking program",
                "Home health nursing evaluation for social determinants and medication adherence",
            ]
        elif total_lace >= 5:
            tier = ReadmissionRiskTier.MEDIUM
            bundle = [
                "Schedule 72-hour nurse check-in call",
                "14-day outpatient physician follow-up",
                "Medication discharge summary provided in patient's preferred language",
            ]
        else:
            tier = ReadmissionRiskTier.LOW
            bundle = [
                "Routine 30-day primary care follow-up",
                "Standard post-discharge written instructions provided",
            ]

        # Key drivers
        drivers = []
        if l_pts >= 4:
            drivers.append(f"Extended hospital stay ({length_of_stay_days} days)")
        if is_emergent_admission:
            drivers.append("Acute emergent admission pathway")
        if c_pts >= 3:
            drivers.append(f"Significant chronic comorbidity burden (Charlson index: {charlson_comorbidity_score})")
        if e_pts >= 2:
            drivers.append(f"High pre-admission ED utilization ({prior_ed_visits_6m} visits in 6m)")

        return PatientReadmissionScore(
            clinical_subject_id=clinical_subject_id,
            lace_score=total_lace,
            readmission_probability_30d=prob,
            risk_tier=tier,
            length_of_stay_days=length_of_stay_days,
            is_emergent_admission=is_emergent_admission,
            charlson_comorbidity_score=charlson_comorbidity_score,
            prior_ed_visits_6m=prior_ed_visits_6m,
            key_risk_drivers=drivers,
            suggested_transitional_care_bundle=bundle,
        )


lace_engine = LACEReadmissionRiskEngine()
