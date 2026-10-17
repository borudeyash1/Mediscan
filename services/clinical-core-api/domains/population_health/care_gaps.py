"""
Chronic Disease Care-Gap & HEDIS Quality Measure Identifier.
Surveils patient cohorts for overdue metabolic screenings (HbA1c, UACR, Retinal Exams).
"""

from datetime import datetime, timezone
from typing import Any, Optional
from .models import CareGapMeasure


class ChronicCareGapEngine:
    """Identifies overdue HEDIS quality measures across longitudinal patient panels."""

    def evaluate_patient_care_gaps(
        self,
        clinical_subject_id: str,
        conditions: list[str],
        labs: dict[str, Any],
        vitals: dict[str, float],
    ) -> list[CareGapMeasure]:
        """
        Evaluate active conditions and lab dates to detect overdue preventive care measures.
        """
        gaps: list[CareGapMeasure] = []
        cond_text = " ".join([c.lower() for c in conditions])

        is_diabetic = "diabetes" in cond_text or "t2dm" in cond_text
        is_hypertensive = "hypertension" in cond_text or "htn" in cond_text or "high blood pressure" in cond_text

        # 1. Diabetes: Overdue HbA1c screening
        if is_diabetic:
            last_hba1c_days = labs.get("hba1c_days_ago", 240)  # Default 8 months ago
            if last_hba1c_days > 180:
                gaps.append(
                    CareGapMeasure(
                        clinical_subject_id=clinical_subject_id,
                        measure_id="HEDIS-CDC-A1C",
                        measure_name="Comprehensive Diabetes Care: Glycated Hemoglobin (HbA1c) Testing",
                        status="OVERDUE",
                        days_overdue=last_hba1c_days - 180,
                        recommended_clinical_outreach=(
                            "Schedule diagnostic HbA1c blood draw; order home blood glucose monitoring review "
                            "and assess glycemic control."
                        ),
                    )
                )

            # 2. Diabetes: Overdue Kidney Health Evaluation (UACR)
            last_uacr_days = labs.get("uacr_days_ago", 410)  # Default ~14 months ago
            if last_uacr_days > 365:
                gaps.append(
                    CareGapMeasure(
                        clinical_subject_id=clinical_subject_id,
                        measure_id="HEDIS-KED-NEPHRO",
                        measure_name="Kidney Health Evaluation for Patients with Diabetes (UACR + eGFR)",
                        status="OVERDUE",
                        days_overdue=last_uacr_days - 365,
                        recommended_clinical_outreach=(
                            "Order annual spot Urine Albumin-to-Creatinine Ratio (UACR) and serum creatinine "
                            "to screen for diabetic nephropathy and stage CKD."
                        ),
                    )
                )

            # 3. Diabetes: Retinal Eye Exam
            last_eye_exam_days = labs.get("retinal_exam_days_ago", 450)
            if last_eye_exam_days > 365:
                gaps.append(
                    CareGapMeasure(
                        clinical_subject_id=clinical_subject_id,
                        measure_id="HEDIS-EED-EYE",
                        measure_name="Eye Exam for Patients with Diabetes (Diabetic Retinopathy Screening)",
                        status="OVERDUE",
                        days_overdue=last_eye_exam_days - 365,
                        recommended_clinical_outreach=(
                            "Refer patient to Optometry / Ophthalmology for annual dilated retinal exam "
                            "or AI fundus photography."
                        ),
                    )
                )

        # 4. Hypertension: Blood pressure control
        if is_hypertensive:
            sbp = vitals.get("systolic_bp", 145.0)
            dbp = vitals.get("diastolic_bp", 92.0)
            if sbp >= 140.0 or dbp >= 90.0:
                gaps.append(
                    CareGapMeasure(
                        clinical_subject_id=clinical_subject_id,
                        measure_id="HEDIS-CBP-BP",
                        measure_name="Controlling High Blood Pressure (< 140/90 mmHg)",
                        status="OVERDUE",
                        days_overdue=60,
                        recommended_clinical_outreach=(
                            f"Current BP ({int(sbp)}/{int(dbp)} mmHg) is above clinical guideline threshold. "
                            "Initiate antihypertensive dose titration (ACEi/ARB or CCB) and schedule 30-day BP recheck."
                        ),
                    )
                )

        return gaps


care_gap_engine = ChronicCareGapEngine()
