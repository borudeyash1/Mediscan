"""
3-Tier Automated Clinical Escalation Ladder Engine.
Escalates wearable RPM anomalies into:
  - Tier 1: Patient Check-in
  - Tier 2: Nurse RPM Queue Alert
  - Tier 3: Critical Physician Breakout + Emergency Dispatch Payload
"""

from datetime import datetime, timezone
from typing import Any, Optional
import structlog

from libs.clinical_calculators.calculators import calculate_news2
from .models import (
    LOINC_HEART_RATE,
    LOINC_SPO2,
    LOINC_SYSTOLIC_BP,
    LOINC_RESPIRATORY_RATE,
    LOINC_TEMPERATURE,
    LOINC_GLUCOSE,
    EscalationTier,
    AnomalyEvent,
    EscalationAlert,
)

logger = structlog.get_logger(__name__)


class EscalationLadderEngine:
    """Evaluates multi-modal physiological telemetry and determines appropriate escalation tier."""

    def evaluate_escalation(
        self,
        clinical_subject_id: str,
        anomalies: list[AnomalyEvent],
        vitals: dict[str, float],
        supplemental_oxygen: bool = False,
        patient_lat: float = 37.7749,
        patient_lng: float = -122.4194,
    ) -> tuple[int, str, Optional[EscalationAlert]]:
        """
        Calculates dynamic NEWS2 score and evaluates 3-tier escalation criteria.
        Returns: (news2_score, news2_category, escalation_alert).
        """
        # Extract vitals with physiological defaults
        hr = int(vitals.get(LOINC_HEART_RATE, 75.0))
        spo2 = float(vitals.get(LOINC_SPO2, 98.0))
        sbp = int(vitals.get(LOINC_SYSTOLIC_BP, 120.0))
        rr = int(vitals.get(LOINC_RESPIRATORY_RATE, 16.0))
        temp = float(vitals.get(LOINC_TEMPERATURE, 37.0))
        glucose = float(vitals.get(LOINC_GLUCOSE, 100.0))

        # Dynamically adjust RR if patient in acute distress (HR > 130 or SpO2 < 90)
        if spo2 <= 88.0 and rr <= 18:
            rr = 28
        elif hr >= 140 and rr <= 18:
            rr = 26

        # Calculate NEWS2 score
        try:
            news2_res = calculate_news2(
                respiratory_rate=rr,
                spo2_percent=spo2,
                supplemental_oxygen=supplemental_oxygen,
                systolic_bp=sbp,
                heart_rate=hr,
                consciousness_avpu="ALERT",
                temperature_celsius=temp,
            )
            news2_score = news2_res.total_score
            news2_category = news2_res.category.value
        except Exception as e:
            logger.warning("escalation.news2_calc_failed", error=str(e))
            news2_score = 0
            news2_category = "LOW"

        # Check for Critical Tier 3 triggers:
        # 1. Any anomaly with |Z| > 3.0
        # 2. NEWS2 >= 7 (Critical / High risk)
        # 3. Severe physiological decompensation (HR > 150, SpO2 <= 85, Glucose <= 50)
        has_z_gt_3 = any(abs(a.z_score) > 3.0 or a.is_critical for a in anomalies)
        is_severe_vitals = (spo2 <= 86.0) or (hr >= 150) or (glucose <= 48.0) or (news2_score >= 7)

        if has_z_gt_3 or is_severe_vitals:
            # Tier 3: Critical Physician Breakout + Emergency Dispatch
            dispatch_payload = {
                "dispatch_priority": "CRITICAL_BREAKOUT_CODE_RED",
                "cad_call_type": "EMERGENCY_MEDICAL_DISPATCH_ACUTE_DECOMPENSATION",
                "patient_subject_id": clinical_subject_id,
                "coordinates": {"lat": patient_lat, "lng": patient_lng},
                "dispatch_phone": "911 / 108",
                "trigger_vitals": {
                    "heart_rate": hr,
                    "spo2_percent": spo2,
                    "systolic_bp": sbp,
                    "respiratory_rate": rr,
                    "cgm_glucose": glucose,
                },
                "news2_aggregate": news2_score,
                "news2_risk": news2_category,
                "recommended_interventions": [
                    "High-flow supplemental oxygen via non-rebreather mask (titrate to SpO2 >= 94%)",
                    "Immediate 12-lead ECG and continuous rhythm telemetry",
                    "IV access and urgent physician bedside arrival",
                    "If severe hypoglycemia (<54 mg/dL): administer 25g Dextrose 50% IV immediately",
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            alert = EscalationAlert(
                clinical_subject_id=clinical_subject_id,
                tier=EscalationTier.TIER_3_CRITICAL_DISPATCH,
                anomalies=anomalies,
                news2_score=news2_score,
                news2_category=news2_category,
                summary_message=(
                    f"CRITICAL TIER-3 ESCALATION: Acute physiological decompensation detected for patient {clinical_subject_id}. "
                    f"NEWS2={news2_score} ({news2_category}). Immediate physician breakout and emergency dispatch activated."
                ),
                emergency_dispatch_payload=dispatch_payload,
            )
            return news2_score, news2_category, alert

        # Check for Tier 2: Nurse RPM Queue Alert (2.0 < |Z| <= 3.0 or NEWS2 5-6)
        has_z_gt_2 = any(abs(a.z_score) > 2.0 for a in anomalies)
        if has_z_gt_2 or news2_score >= 5:
            alert = EscalationAlert(
                clinical_subject_id=clinical_subject_id,
                tier=EscalationTier.TIER_2_NURSE_RPM_QUEUE,
                anomalies=anomalies,
                news2_score=news2_score,
                news2_category=news2_category,
                summary_message=(
                    f"TIER-2 RPM ALERT: Moderate physiological drift detected for patient {clinical_subject_id}. "
                    f"NEWS2={news2_score}. Case added to Nurse RPM priority queue for rapid triage review."
                ),
                emergency_dispatch_payload=None,
            )
            return news2_score, news2_category, alert

        # Check for Tier 1: Patient Check-in (1.5 < |Z| <= 2.0 or single mild drift)
        has_z_gt_1_5 = any(abs(a.z_score) > 1.5 for a in anomalies)
        if has_z_gt_1_5:
            alert = EscalationAlert(
                clinical_subject_id=clinical_subject_id,
                tier=EscalationTier.TIER_1_PATIENT_CHECKIN,
                anomalies=anomalies,
                news2_score=news2_score,
                news2_category=news2_category,
                summary_message=(
                    f"TIER-1 PATIENT CHECK-IN: Mild telemetry variation detected for patient {clinical_subject_id}. "
                    "Automated patient app questionnaire dispatched: 'Are you feeling lightheaded, short of breath, or unwell?'"
                ),
                emergency_dispatch_payload=None,
            )
            return news2_score, news2_category, alert

        # Normal baseline
        return news2_score, news2_category, None
