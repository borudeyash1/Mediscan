"""
Validated Deterministic Physiological Calculators (Zero-Hallucination Math)
==========================================================================
Clinical Decision Support equations for renal function, triage risk scores,
and pediatric weight-based dosing with adult hard ceilings.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class BiologicalSex(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class NEWS2Category(str, Enum):
    LOW = "LOW"
    LOW_MEDIUM = "LOW_MEDIUM"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ESILevel(int, Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5


class ConsciousnessAVPU(str, Enum):
    ALERT = "ALERT"
    CONFUSION = "CONFUSION"
    VOICE = "VOICE"
    PAIN = "PAIN"
    UNRESPONSIVE = "UNRESPONSIVE"


@dataclass(frozen=True)
class EGFRResult:
    egfr_ml_min_1_73m2: float
    equation: str
    ckd_stage: str
    stage_description: str
    is_kidney_failure: bool
    requires_dose_adjustment: bool
    contraindicated_metformin: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CrClResult:
    crcl_ml_min: float
    equation: str
    is_impaired: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NEWS2Result:
    total_score: int
    category: NEWS2Category
    is_critical: bool
    component_scores: Dict[str, int]
    recommended_clinical_response: str
    scale_used: str


@dataclass(frozen=True)
class QSOFAResult:
    score: int
    is_high_risk_sepsis: bool
    criteria_met: Dict[str, bool]
    recommendation: str


@dataclass(frozen=True)
class ESIResult:
    level: ESILevel
    category_name: str
    decision_rationale: str
    immediate_intervention_required: bool


@dataclass(frozen=True)
class BSAResult:
    bsa_m2: float
    equation: str


@dataclass(frozen=True)
class PediatricDoseResult:
    calculated_dose_mg: float
    final_dose_mg: float
    adult_max_ceiling_mg: float
    is_capped_by_adult_ceiling: bool
    dosing_basis: str
    weight_kg: float
    warnings: list[str] = field(default_factory=list)


def calculate_ckd_epi_2021(
    serum_creatinine_mg_dl: float,
    age_years: int,
    biological_sex: BiologicalSex | str,
) -> EGFRResult:
    """
    Computes 2021 CKD-EPI (Race-Free) eGFR equation:
    eGFR = 142 * min(Scr/kappa, 1)^alpha * max(Scr/kappa, 1)^-1.200 * 0.9938^Age * (1.012 if female else 1.0)
    """
    if serum_creatinine_mg_dl <= 0:
        raise ValueError("Serum creatinine must be strictly positive (> 0 mg/dL).")
    if age_years < 18:
        raise ValueError("CKD-EPI 2021 is validated for adults >= 18 years. Use Schwartz equation for pediatrics.")

    if isinstance(biological_sex, BiologicalSex):
        sex = biological_sex
    else:
        sex_str = str(biological_sex).split(".")[-1].strip().upper()
        sex = BiologicalSex(sex_str)
    is_female = (sex == BiologicalSex.FEMALE)

    kappa = 0.7 if is_female else 0.9
    alpha = -0.241 if is_female else -0.302
    sex_factor = 1.012 if is_female else 1.0

    scr = float(serum_creatinine_mg_dl)
    ratio = scr / kappa
    min_term = min(ratio, 1.0) ** alpha
    max_term = max(ratio, 1.0) ** (-1.200)
    age_term = 0.9938 ** age_years

    egfr = 142.0 * min_term * max_term * age_term * sex_factor
    egfr_rounded = round(egfr, 1)

    if egfr_rounded >= 90.0:
        stage = "G1"
        description = "Normal or high GFR"
    elif egfr_rounded >= 60.0:
        stage = "G2"
        description = "Mildly decreased GFR"
    elif egfr_rounded >= 45.0:
        stage = "G3a"
        description = "Mildly to moderately decreased GFR"
    elif egfr_rounded >= 30.0:
        stage = "G3b"
        description = "Moderately to severely decreased GFR"
    elif egfr_rounded >= 15.0:
        stage = "G4"
        description = "Severely decreased GFR"
    else:
        stage = "G5"
        description = "Kidney failure (End-stage renal disease)"

    return EGFRResult(
        egfr_ml_min_1_73m2=egfr_rounded,
        equation="CKD-EPI 2021 (Race-Free)",
        ckd_stage=stage,
        stage_description=description,
        is_kidney_failure=(egfr_rounded < 15.0),
        requires_dose_adjustment=(egfr_rounded < 60.0),
        contraindicated_metformin=(egfr_rounded < 30.0),
        details={
            "serum_creatinine": scr,
            "age": age_years,
            "biological_sex": sex.value,
            "kappa": kappa,
            "alpha": alpha,
            "sex_multiplier": sex_factor,
        },
    )


def calculate_cockcroft_gault(
    serum_creatinine_mg_dl: float,
    age_years: int,
    weight_kg: float,
    biological_sex: BiologicalSex | str,
) -> CrClResult:
    """
    Computes Cockcroft-Gault Creatinine Clearance:
    CrCl (mL/min) = [ (140 - Age) * Weight (kg) ] / [ 72 * Scr (mg/dL) ] * (0.85 if female else 1.0)
    """
    if serum_creatinine_mg_dl <= 0:
        raise ValueError("Serum creatinine must be strictly positive.")
    if weight_kg <= 0:
        raise ValueError("Weight must be strictly positive.")

    if isinstance(biological_sex, BiologicalSex):
        sex = biological_sex
    else:
        sex_str = str(biological_sex).split(".")[-1].strip().upper()
        sex = BiologicalSex(sex_str)
    is_female = (sex == BiologicalSex.FEMALE)
    factor = 0.85 if is_female else 1.0

    raw_crcl = ((140.0 - float(age_years)) * float(weight_kg)) / (72.0 * float(serum_creatinine_mg_dl))
    crcl = round(raw_crcl * factor, 1)

    return CrClResult(
        crcl_ml_min=crcl,
        equation="Cockcroft-Gault CrCl",
        is_impaired=(crcl < 60.0),
        details={
            "serum_creatinine": serum_creatinine_mg_dl,
            "age": age_years,
            "weight_kg": weight_kg,
            "sex": sex.value,
            "female_factor": factor,
        },
    )


def calculate_news2(
    respiratory_rate: Optional[int] = None,
    spo2_percent: Optional[float] = None,
    supplemental_oxygen: bool = False,
    hypercapnic_respiratory_failure: bool = False,
    systolic_bp: Optional[int] = None,
    heart_rate: Optional[int] = None,
    consciousness_avpu: Optional[ConsciousnessAVPU | str] = ConsciousnessAVPU.ALERT,
    temperature_celsius: Optional[float] = None,
) -> NEWS2Result:
    """
    Computes Royal College of Physicians (RCP) NEWS2 score.
    """
    scores: Dict[str, int] = {}

    if respiratory_rate is not None:
        rr = int(respiratory_rate)
        if rr <= 8:
            scores["respiratory_rate"] = 3
        elif 9 <= rr <= 11:
            scores["respiratory_rate"] = 1
        elif 12 <= rr <= 20:
            scores["respiratory_rate"] = 0
        elif 21 <= rr <= 24:
            scores["respiratory_rate"] = 2
        else:
            scores["respiratory_rate"] = 3

    scale_used = "Scale 2 (Hypercapnic / Target 88-92%)" if hypercapnic_respiratory_failure else "Scale 1 (Standard)"
    if spo2_percent is not None:
        spo2 = float(spo2_percent)
        if hypercapnic_respiratory_failure:
            if spo2 <= 83:
                scores["oxygen_saturation"] = 3
            elif 84 <= spo2 <= 85:
                scores["oxygen_saturation"] = 2
            elif 86 <= spo2 <= 87:
                scores["oxygen_saturation"] = 1
            elif 88 <= spo2 <= 92:
                scores["oxygen_saturation"] = 0
            elif 93 <= spo2 <= 94:
                scores["oxygen_saturation"] = 1 if supplemental_oxygen else 0
            elif 95 <= spo2 <= 96:
                scores["oxygen_saturation"] = 2 if supplemental_oxygen else 0
            else:
                scores["oxygen_saturation"] = 3 if supplemental_oxygen else 0
        else:
            if spo2 <= 91:
                scores["oxygen_saturation"] = 3
            elif 92 <= spo2 <= 93:
                scores["oxygen_saturation"] = 2
            elif 94 <= spo2 <= 95:
                scores["oxygen_saturation"] = 1
            else:
                scores["oxygen_saturation"] = 0

    scores["supplemental_oxygen"] = 2 if supplemental_oxygen else 0

    if systolic_bp is not None:
        sbp = int(systolic_bp)
        if sbp <= 90:
            scores["systolic_bp"] = 3
        elif 91 <= sbp <= 100:
            scores["systolic_bp"] = 2
        elif 101 <= sbp <= 110:
            scores["systolic_bp"] = 1
        elif 111 <= sbp <= 219:
            scores["systolic_bp"] = 0
        else:
            scores["systolic_bp"] = 3

    if heart_rate is not None:
        hr = int(heart_rate)
        if hr <= 40:
            scores["heart_rate"] = 3
        elif 41 <= hr <= 50:
            scores["heart_rate"] = 1
        elif 51 <= hr <= 90:
            scores["heart_rate"] = 0
        elif 91 <= hr <= 110:
            scores["heart_rate"] = 1
        elif 111 <= hr <= 130:
            scores["heart_rate"] = 2
        else:
            scores["heart_rate"] = 3

    if consciousness_avpu is not None:
        if isinstance(consciousness_avpu, ConsciousnessAVPU):
            avpu_str = consciousness_avpu.value.upper()
        else:
            avpu_str = str(consciousness_avpu).split(".")[-1].strip().upper()
        if avpu_str in ("ALERT", "A"):
            scores["consciousness"] = 0
        else:
            scores["consciousness"] = 3

    if temperature_celsius is not None:
        temp = float(temperature_celsius)
        if temp <= 35.0:
            scores["temperature"] = 3
        elif 35.1 <= temp <= 36.0:
            scores["temperature"] = 1
        elif 36.1 <= temp <= 38.0:
            scores["temperature"] = 0
        elif 38.1 <= temp <= 39.0:
            scores["temperature"] = 1
        else:
            scores["temperature"] = 2

    total = sum(scores.values())

    has_extreme_single = any(v == 3 for k, v in scores.items() if k != "supplemental_oxygen")
    if total >= 7:
        category = NEWS2Category.HIGH
        response = "EMERGENCY / HIGH RISK: Immediate clinical assessment by critical care team / outreach team with continuous vital signs monitoring."
    elif total >= 5:
        category = NEWS2Category.MEDIUM
        response = "URGENT / MEDIUM RISK: Urgent clinical review by a senior clinician with competence in acute illness assessment; hourly monitoring minimum."
    elif has_extreme_single:
        category = NEWS2Category.LOW_MEDIUM
        response = "LOW-MEDIUM RISK: Extreme score in a single physiological parameter. Urgent ward-level clinical review; increase monitoring to 4-hourly minimum."
    else:
        category = NEWS2Category.LOW
        response = "LOW RISK: Routine ward-level clinical monitoring; minimum 12-hourly observations."

    return NEWS2Result(
        total_score=total,
        category=category,
        is_critical=(total >= 7 or category == NEWS2Category.HIGH),
        component_scores=scores,
        recommended_clinical_response=response,
        scale_used=scale_used,
    )


def calculate_qsofa(
    respiratory_rate: int,
    systolic_bp: int,
    altered_mentation: bool,
) -> QSOFAResult:
    crit_rr = (respiratory_rate >= 22)
    crit_sbp = (systolic_bp <= 100)
    crit_ams = bool(altered_mentation)

    score = sum([1 if crit_rr else 0, 1 if crit_sbp else 0, 1 if crit_ams else 0])
    is_high_risk = (score >= 2)

    rec = (
        "HIGH RISK OF SEPSIS DECOMPENSATION: Score >= 2. Obtain STAT blood cultures, serum lactate, "
        "initiate broad-spectrum antimicrobials, IV fluid resuscitation, and evaluate for ICU admission."
        if is_high_risk
        else "Low qSOFA score (< 2). Continue serial monitoring if infection is suspected."
    )

    return QSOFAResult(
        score=score,
        is_high_risk_sepsis=is_high_risk,
        criteria_met={
            "tachypnea_rr_gte_22": crit_rr,
            "hypotension_sbp_lte_100": crit_sbp,
            "altered_mentation": crit_ams,
        },
        recommendation=rec,
    )


def calculate_esi_v4(
    requires_immediate_lifesaving: bool = False,
    is_high_risk_or_confused_or_severe_pain: bool = False,
    expected_resources: int = 0,
    vital_signs_danger_zone: bool = False,
) -> ESIResult:
    if requires_immediate_lifesaving:
        return ESIResult(
            level=ESILevel.LEVEL_1,
            category_name="Resuscitation",
            decision_rationale="Requires immediate life-saving intervention (airway, breathing, circulation, arrest, profound shock).",
            immediate_intervention_required=True,
        )

    if is_high_risk_or_confused_or_severe_pain or vital_signs_danger_zone:
        return ESIResult(
            level=ESILevel.LEVEL_2,
            category_name="Emergent",
            decision_rationale="High-risk clinical situation, severe altered mental status, severe acute distress, or vitals in danger zone.",
            immediate_intervention_required=False,
        )

    if expected_resources >= 2:
        return ESIResult(
            level=ESILevel.LEVEL_3,
            category_name="Urgent",
            decision_rationale=f"Stable vitals, multiple hospital resources expected ({expected_resources} resources).",
            immediate_intervention_required=False,
        )
    elif expected_resources == 1:
        return ESIResult(
            level=ESILevel.LEVEL_4,
            category_name="Less Urgent",
            decision_rationale="Single diagnostic or therapeutic resource expected.",
            immediate_intervention_required=False,
        )
    else:
        return ESIResult(
            level=ESILevel.LEVEL_5,
            category_name="Non-Urgent",
            decision_rationale="No resources needed beyond clinical evaluation / prescription / discharge advice.",
            immediate_intervention_required=False,
        )


def calculate_mosteller_bsa(height_cm: float, weight_kg: float) -> BSAResult:
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must both be strictly positive.")
    raw_bsa = math.sqrt((height_cm * weight_kg) / 3600.0)
    return BSAResult(bsa_m2=round(raw_bsa, 3), equation="Mosteller BSA")


def calculate_pediatric_dose_with_adult_ceiling(
    weight_kg: float,
    dose_mg_per_kg: float,
    adult_max_single_dose_mg: float,
    height_cm: Optional[float] = None,
    dose_mg_per_m2: Optional[float] = None,
) -> PediatricDoseResult:
    if weight_kg <= 0:
        raise ValueError("Weight must be strictly positive.")
    if adult_max_single_dose_mg <= 0:
        raise ValueError("Adult maximum single dose must be strictly positive.")

    warnings: list[str] = []

    if dose_mg_per_m2 is not None and height_cm is not None:
        bsa_res = calculate_mosteller_bsa(height_cm, weight_kg)
        raw_dose = bsa_res.bsa_m2 * dose_mg_per_m2
        basis = f"BSA-based ({dose_mg_per_m2} mg/m2 over {bsa_res.bsa_m2} m2)"
    else:
        raw_dose = weight_kg * dose_mg_per_kg
        basis = f"Weight-based ({dose_mg_per_kg} mg/kg for {weight_kg} kg)"

    # Hard ceiling enforcement: final dose must strictly never exceed adult ceiling
    is_capped = (raw_dose >= adult_max_single_dose_mg)
    if is_capped:
        final_dose = float(adult_max_single_dose_mg)
    else:
        final_dose = round(raw_dose, 2)
        if final_dose > adult_max_single_dose_mg:
            final_dose = float(adult_max_single_dose_mg)

    if is_capped:
        warnings.append(
            f"SAFETY CEILING TRIGGERED: Calculated dose ({round(raw_dose, 1)} mg) exceeds "
            f"adult maximum single dose ({adult_max_single_dose_mg} mg). Capped to {adult_max_single_dose_mg} mg."
        )

    return PediatricDoseResult(
        calculated_dose_mg=round(raw_dose, 2),
        final_dose_mg=final_dose,
        adult_max_ceiling_mg=adult_max_single_dose_mg,
        is_capped_by_adult_ceiling=is_capped,
        dosing_basis=basis,
        weight_kg=weight_kg,
        warnings=warnings,
    )
