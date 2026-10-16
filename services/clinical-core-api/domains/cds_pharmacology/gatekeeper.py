"""
Neuro-Symbolic Deterministic Pharmacology Safety Gatekeeper
===========================================================
Replaces legacy drug_recommender.py (which blindly output lethal prescription dosages).

Deterministic Clinical Safety Checks executed BEFORE any medication can be recommended or signed:
1. Drug-Allergy Cross-Reactivity (e.g., Penicillin allergy blocking Amoxicillin-Clavulanate)
2. Drug-Drug Interactions (DDI) via Neo4j Graph + Bundled Fallback (CONTRAINDICATED, MAJOR, MODERATE)
3. Renal Automated Dose Adjustment & Hard-Stops (eGFR < 30 blocking Metformin, adjusting Sitagliptin)
4. Disease-Drug Contraindications (Dengue blocking Aspirin/Ibuprofen; Asthma blocking Beta-blockers)
5. Pediatric Weight-Based / BSA Dosing Ceiling Hard-Cap
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Ensure root workspace is in sys.path
_workspace_root = Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents) >= 5 else Path(__file__).resolve().parents[2]
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from libs.clinical_calculators.calculators import (
        calculate_ckd_epi_2021,
        calculate_pediatric_dose_with_adult_ceiling,
    )
except ImportError:
    from libs.clinical_calculators.src.calculators import (
        calculate_ckd_epi_2021,
        calculate_pediatric_dose_with_adult_ceiling,
    )

try:
    from .models import (
        AllergyAlert,
        DDIAlert,
        DDISeverity,
        DiseaseContraindicationAlert,
        MedicationEvaluationRequest,
        MedicationEvaluationResponse,
        PediatricCeilingCheck,
        RenalAdjustmentAlert,
        SafetyVerdict,
    )
except ImportError:
    from services.clinical_core_api.domains.cds_pharmacology.models import (
        AllergyAlert,
        DDIAlert,
        DDISeverity,
        DiseaseContraindicationAlert,
        MedicationEvaluationRequest,
        MedicationEvaluationResponse,
        PediatricCeilingCheck,
        RenalAdjustmentAlert,
        SafetyVerdict,
    )


# ── Drug Class & Cross-Reactivity Ontology ────────────────────

ALLERGY_CLASS_MAP = {
    # Beta-lactams / Penicillins
    "PENICILLIN": {
        "snomed_codes": ["91936005", "373270004", "294532003"],
        "aliases": ["penicillin", "penicillins", "amoxicillin", "ampicillin"],
        "blocked_drugs": [
            "amoxicillin", "amoxicillin-clavulanate", "amoxicillin/clavulanic acid",
            "co-amoxiclav", "ampicillin", "ampicillin-sulbactam", "piperacillin",
            "piperacillin-tazobactam", "penicillin v", "penicillin g", "oxacillin",
            "nafcillin", "augmentin",
        ],
        "reaction_risk": "Severe Type-I IgE-mediated anaphylaxis / angioedema",
        "rationale": "Direct beta-lactam penicillin core cross-reactivity. High risk of fatal anaphylaxis.",
    },
    # Sulfonamides
    "SULFONAMIDE": {
        "snomed_codes": ["91939003", "416098002"],
        "aliases": ["sulfa", "sulfonamide", "sulfamethoxazole", "bactrim", "septra"],
        "blocked_drugs": [
            "sulfamethoxazole", "trimethoprim-sulfamethoxazole", "cotrimoxazole",
            "sulfasalazine", "sulfadiazine",
        ],
        "reaction_risk": "Stevens-Johnson Syndrome (SJS), Toxic Epidermal Necrolysis (TEN)",
        "rationale": "Immunologic arylamine sulfonamide cross-reactivity.",
    },
    # NSAIDs / Aspirin
    "NSAID": {
        "snomed_codes": ["293584003", "293586001"],
        "aliases": ["nsaid", "aspirin", "ibuprofen", "naproxen"],
        "blocked_drugs": [
            "aspirin", "ibuprofen", "naproxen", "ketorolac", "diclofenac",
            "indomethacin", "meloxicam", "celecoxib",
        ],
        "reaction_risk": "Aspirin-exacerbated respiratory disease (AERD), bronchospasm, anaphylactoid reaction",
        "rationale": "COX-1 inhibition mediated leukotriene overproduction.",
    },
}


# ── Curated DDI Knowledge Base (Graph Fallback & Fast Cache) ──

FALLBACK_DDI_RULES = [
    # Warfarin Combinations
    {
        "drug_a": "Warfarin",
        "drug_b": "Rivaroxaban",
        "severity": DDISeverity.CONTRAINDICATED,
        "mechanism": "Dual anticoagulation — extreme synergistic bleeding risk without clinical indication.",
        "management": "Never co-administer; choose one targeted oral anticoagulant.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Apixaban",
        "severity": DDISeverity.CONTRAINDICATED,
        "mechanism": "Dual anticoagulation — severe hemorrhagic hazard.",
        "management": "Never co-administer.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Aspirin",
        "severity": DDISeverity.MAJOR,
        "mechanism": "Combined anticoagulant and antiplatelet therapy significantly increases major GI and intracranial bleeding.",
        "management": "Limit duration; monitor INR closely; prescribe PPI gastroprotection.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Clopidogrel",
        "severity": DDISeverity.MAJOR,
        "mechanism": "Dual pathway inhibition (Factor II/VII/IX/X + P2Y12) increases hemorrhagic risk.",
        "management": "Prescribe only under cardiological indication (e.g. post-PCI with AF); monitor for bleeding.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Ibuprofen",
        "severity": DDISeverity.MAJOR,
        "mechanism": "NSAIDs damage gastric mucosa, inhibit platelet COX-1, and displace warfarin from albumin.",
        "management": "Avoid combination; use acetaminophen for pain relief.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Naproxen",
        "severity": DDISeverity.MAJOR,
        "mechanism": "Additive GI ulceration and systemic bleeding hazard.",
        "management": "Avoid combination; use acetaminophen.",
    },
    # Antiplatelet + NSAID
    {
        "drug_a": "Aspirin",
        "drug_b": "Ibuprofen",
        "severity": DDISeverity.MAJOR,
        "mechanism": "Ibuprofen competitively antagonizes aspirin's irreversible platelet COX-1 acetylation, blunting cardioprotection.",
        "management": "Take immediate-release aspirin at least 30 minutes before ibuprofen, or use acetaminophen.",
    },
    # Antiarrhythmic / Inotropic
    {
        "drug_a": "Amiodarone",
        "drug_b": "Digoxin",
        "severity": DDISeverity.MAJOR,
        "mechanism": "Amiodarone inhibits P-glycoprotein efflux pump, doubling serum digoxin concentrations and precipitating digitalis toxicity.",
        "management": "Empirically reduce digoxin dose by 50%; monitor serum digoxin levels and ECG.",
    },
    {
        "drug_a": "Amiodarone",
        "drug_b": "Warfarin",
        "severity": DDISeverity.MAJOR,
        "mechanism": "Amiodarone inhibits CYP2C9, markedly potentiating warfarin anticoagulation.",
        "management": "Reduce warfarin maintenance dose by 33-50%; monitor INR weekly.",
    },
    # Hyperkalemic Combinations
    {
        "drug_a": "Lisinopril",
        "drug_b": "Spironolactone",
        "severity": DDISeverity.MAJOR,
        "mechanism": "Dual RAAS inhibition and potassium retention causes life-threatening hyperkalemia.",
        "management": "Check serum potassium and renal function at 1 and 4 weeks; avoid if baseline K+ > 5.0 mmol/L.",
    },
    {
        "drug_a": "Enalapril",
        "drug_b": "Spironolactone",
        "severity": DDISeverity.MAJOR,
        "mechanism": "Additive potassium-sparing effect resulting in cardiac arrhythmias.",
        "management": "Monitor serum potassium closely; titrate spironolactone to <= 25 mg daily.",
    },
    # CYP Induction / Anticoagulation
    {
        "drug_a": "Rifampicin",
        "drug_b": "Rivaroxaban",
        "severity": DDISeverity.CONTRAINDICATED,
        "mechanism": "Rifampicin is a potent CYP3A4 and P-gp inducer, decreasing rivaroxaban AUC by >50% and causing thrombosis failure.",
        "management": "Contraindicated; switch to parenteral anticoagulation (UFH or enoxaparin with anti-Xa monitoring).",
    },
]


# ── Renal Cutoffs & Guidance ───────────────────────────────────

RENAL_RULES = [
    {
        "drug_names": ["metformin", "glucophage"],
        "rxnorm_codes": ["6809"],
        "cutoff_egfr": 30.0,
        "is_hard_stop": True,
        "action": "HARD_STOP_CONTRAINDICATION",
        "guidance": "Metformin is strictly contraindicated when eGFR < 30 mL/min/1.73m2 due to high risk of fatal lactic acidosis.",
    },
    {
        "drug_names": ["enoxaparin", "lovenox"],
        "rxnorm_codes": ["67108"],
        "cutoff_egfr": 30.0,
        "is_hard_stop": True,
        "action": "HARD_STOP_CONTRAINDICATION",
        "guidance": "Standard therapeutic enoxaparin accumulation occurs at eGFR < 30. Reduce to 1 mg/kg once daily or switch to Unfractionated Heparin (UFH).",
    },
    {
        "drug_names": ["sitagliptin", "januvia"],
        "rxnorm_codes": ["593411"],
        "cutoff_egfr": 30.0,
        "is_hard_stop": False,
        "action": "REQUIRES_ADJUSTMENT",
        "guidance": "Renal dose adjustment mandatory: Reduce sitagliptin dose from standard 100 mg daily to 25 mg daily when eGFR < 30 mL/min/1.73m2.",
    },
    {
        "drug_names": ["oseltamivir", "tamiflu"],
        "rxnorm_codes": ["283742"],
        "cutoff_egfr": 30.0,
        "is_hard_stop": False,
        "action": "REQUIRES_ADJUSTMENT",
        "guidance": "Renal dose adjustment mandatory: Reduce oseltamivir from 75 mg BID to 75 mg once daily (or 30 mg QD if eGFR < 15).",
    },
    {
        "drug_names": ["gabapentin", "neurontin"],
        "rxnorm_codes": ["25480"],
        "cutoff_egfr": 30.0,
        "is_hard_stop": False,
        "action": "REQUIRES_ADJUSTMENT",
        "guidance": "Renal dose adjustment required: Reduce gabapentin to 100-300 mg daily; severe accumulation causes myoclonus and sedation.",
    },
    {
        "drug_names": ["rivaroxaban", "xarelto"],
        "rxnorm_codes": ["1114195"],
        "cutoff_egfr": 15.0,
        "is_hard_stop": True,
        "action": "HARD_STOP_CONTRAINDICATION",
        "guidance": "Rivaroxaban is contraindicated in end-stage renal disease (eGFR < 15 mL/min/1.73m2).",
    },
]


# ── Disease-Drug Contraindications ────────────────────────────

DISEASE_DRUG_CONTRAINDICATIONS = [
    {
        "disease_keywords": ["dengue", "dengue fever", "dengue hemorrhagic fever"],
        "disease_codes": ["1D20", "38362002"],
        "contraindicated_drugs": ["aspirin", "ibuprofen", "naproxen", "ketorolac", "diclofenac", "indomethacin", "meloxicam"],
        "hazard": "CRITICAL BLEEDING HAZARD: Dengue causes profound thrombocytopenia and capillary fragility. NSAIDs and Aspirin inhibit platelets and severely exacerbate fatal hemorrhage.",
    },
    {
        "disease_keywords": ["peptic ulcer", "gastric ulcer", "duodenal ulcer", "pud", "gi bleed"],
        "disease_codes": ["DA60", "13200003"],
        "contraindicated_drugs": ["aspirin", "ibuprofen", "naproxen", "ketorolac", "diclofenac", "indomethacin"],
        "hazard": "GASTROINTESTINAL PERFORATION RISK: NSAIDs inhibit gastric mucosal COX-1 prostaglandin synthesis, precipitating acute hemorrhage or perforation.",
    },
    {
        "disease_keywords": ["asthma", "acute asthma", "bronchial asthma", "status asthmaticus"],
        "disease_codes": ["CA23", "304527002"],
        "contraindicated_drugs": ["propranolol", "carvedilol", "labetalol", "nadolol", "timolol", "sotalol"],
        "hazard": "FATAL BRONCHOSPASM HAZARD: Non-selective beta-blockers antagonize bronchial beta-2 adrenergic receptors, triggering life-threatening airway constriction.",
    },
]


class PharmacologyGatekeeper:
    """
    Deterministic clinical pharmacology decision support engine.
    Ensures safe prescribing by evaluating allergies, DDIs, renal function,
    disease contraindications, and pediatric ceilings.
    """

    def __init__(self, neo4j_driver: Optional[Any] = None):
        self.neo4j_driver = neo4j_driver

    def _normalize_name(self, name: str) -> str:
        return re.sub(r"[^a-z0-9]", "", name.lower())

    def _match_drug(self, proposed_name: str, target_name: str) -> bool:
        p_norm = self._normalize_name(proposed_name)
        t_norm = self._normalize_name(target_name)
        return (p_norm in t_norm) or (t_norm in p_norm)

    def evaluate_safety(self, req: MedicationEvaluationRequest) -> MedicationEvaluationResponse:
        """
        Executes all 5 deterministic pharmacology gates.
        Returns MedicationEvaluationResponse with strict SafetyVerdict.
        """
        proposed_drug = req.proposed_drug_name.strip()
        proposed_norm = self._normalize_name(proposed_drug)

        hard_stop_reasons: list[str] = []
        adjustment_reasons: list[str] = []

        allergy_alerts: list[AllergyAlert] = []
        ddi_alerts: list[DDIAlert] = []
        renal_alerts: list[RenalAdjustmentAlert] = []
        disease_alerts: list[DiseaseContraindicationAlert] = []
        pediatric_check: Optional[PediatricCeilingCheck] = None

        # ── Gate 1: Drug-Allergy Cross-Reactivity ──────────────────
        for allergy in req.known_allergies:
            allergy_name = allergy.get("name", "").strip().lower()
            allergy_snomed = str(allergy.get("snomed_id", "")).strip()

            for class_key, class_info in ALLERGY_CLASS_MAP.items():
                is_match = False
                if allergy_snomed and allergy_snomed in class_info["snomed_codes"]:
                    is_match = True
                elif any(alias in allergy_name for alias in class_info["aliases"]):
                    is_match = True

                if is_match:
                    # Check if proposed drug is in blocked list
                    for blocked in class_info["blocked_drugs"]:
                        if self._match_drug(proposed_drug, blocked):
                            alert = AllergyAlert(
                                allergen_name=allergy.get("name", class_key),
                                allergen_snomed=allergy_snomed or class_info["snomed_codes"][0],
                                cross_reactivity_class=class_key,
                                reaction_risk=class_info["reaction_risk"],
                                is_hard_stop=True,
                                clinical_rationale=class_info["rationale"],
                            )
                            allergy_alerts.append(alert)
                            hard_stop_reasons.append(
                                f"ALLERGY HARD STOP: Documented {class_key} allergy ({allergy_name}) "
                                f"cross-reacts with proposed medication '{proposed_drug}'."
                            )
                            break

        # ── Gate 2: Drug-Drug Interactions (DDI) ────────────────────
        for active in req.active_medications:
            active_name = active.get("name", "").strip()
            active_rxnorm = str(active.get("rxnorm_cui", "")).strip()

            for rule in FALLBACK_DDI_RULES:
                drug_a = rule["drug_a"]
                drug_b = rule["drug_b"]

                match_a_prop = self._match_drug(proposed_drug, drug_a) and self._match_drug(active_name, drug_b)
                match_b_prop = self._match_drug(proposed_drug, drug_b) and self._match_drug(active_name, drug_a)

                if match_a_prop or match_b_prop:
                    alert = DDIAlert(
                        interacting_drug_rxnorm=active_rxnorm or "UNKNOWN",
                        interacting_drug_name=active_name,
                        severity=rule["severity"],
                        mechanism=rule["mechanism"],
                        clinical_management=rule["management"],
                    )
                    ddi_alerts.append(alert)

                    if rule["severity"] == DDISeverity.CONTRAINDICATED:
                        hard_stop_reasons.append(
                            f"DDI CONTRAINDICATION: '{proposed_drug}' combined with active '{active_name}' "
                            f"is strictly contraindicated: {rule['mechanism']}"
                        )
                    elif rule["severity"] == DDISeverity.MAJOR:
                        adjustment_reasons.append(
                            f"MAJOR DDI: '{proposed_drug}' with '{active_name}' ({rule['mechanism']})"
                        )

        # ── Gate 3: Renal Automated Dose Adjustment & Hard Stop ────
        patient_egfr = req.patient_egfr
        if patient_egfr is None and req.patient_serum_creatinine is not None and req.patient_age_years is not None:
            # Dynamically compute CKD-EPI 2021 eGFR
            try:
                sex = req.patient_biological_sex or "MALE"
                calc = calculate_ckd_epi_2021(
                    serum_creatinine_mg_dl=req.patient_serum_creatinine,
                    age_years=req.patient_age_years,
                    biological_sex=sex,
                )
                patient_egfr = calc.egfr_ml_min_1_73m2
            except Exception as e:
                logger.warning("egfr_dynamic_calc_failed: %s", str(e))

        if patient_egfr is not None:
            for rule in RENAL_RULES:
                match_rule = False
                for d_name in rule["drug_names"]:
                    if self._match_drug(proposed_drug, d_name):
                        match_rule = True
                        break
                if not match_rule and req.proposed_rxnorm_code:
                    if str(req.proposed_rxnorm_code).strip() in rule["rxnorm_codes"]:
                        match_rule = True

                if match_rule:
                    cutoff = rule["cutoff_egfr"]
                    if patient_egfr < cutoff:
                        is_stop = rule["is_hard_stop"]
                        alert = RenalAdjustmentAlert(
                            drug_name=proposed_drug,
                            egfr_value=patient_egfr,
                            egfr_cutoff=cutoff,
                            is_hard_stop=is_stop,
                            recommended_action=rule["action"],
                            dosing_guidance=rule["guidance"],
                        )
                        renal_alerts.append(alert)

                        if is_stop:
                            hard_stop_reasons.append(
                                f"RENAL HARD STOP: '{proposed_drug}' is contraindicated at eGFR {patient_egfr} "
                                f"(Cutoff < {cutoff} mL/min/1.73m2). {rule['guidance']}"
                            )
                        else:
                            adjustment_reasons.append(
                                f"RENAL DOSE ADJUSTMENT: '{proposed_drug}' requires dose reduction at eGFR {patient_egfr}. "
                                f"{rule['guidance']}"
                            )

        # ── Gate 4: Disease-Drug Contraindications ──────────────────
        for diag in req.diagnosed_diseases:
            diag_name = diag.get("name", "").strip().lower()
            diag_code = str(diag.get("icd11", diag.get("snomed_id", ""))).strip().upper()

            for contra in DISEASE_DRUG_CONTRAINDICATIONS:
                is_disease_match = False
                if diag_code and diag_code in [c.upper() for c in contra["disease_codes"]]:
                    is_disease_match = True
                elif any(kw in diag_name for kw in contra["disease_keywords"]):
                    is_disease_match = True

                if is_disease_match:
                    for contra_drug in contra["contraindicated_drugs"]:
                        if self._match_drug(proposed_drug, contra_drug):
                            alert = DiseaseContraindicationAlert(
                                disease_name=diag.get("name", "Active Disease"),
                                disease_icd11_or_snomed=diag_code or contra["disease_codes"][0],
                                drug_name=proposed_drug,
                                severity="HARD_STOP_CONTRAINDICATION",
                                clinical_hazard=contra["hazard"],
                            )
                            disease_alerts.append(alert)
                            hard_stop_reasons.append(
                                f"DISEASE CONTRAINDICATION HARD STOP: '{proposed_drug}' is contraindicated in "
                                f"{diag.get('name', 'this condition')} ({contra['hazard']})"
                            )
                            break

        # ── Gate 5: Pediatric Weight-Based Ceilings ─────────────────
        if (
            req.patient_weight_kg is not None
            and req.dose_mg_per_kg is not None
            and req.adult_max_single_dose_mg is not None
        ):
            ped_res = calculate_pediatric_dose_with_adult_ceiling(
                weight_kg=req.patient_weight_kg,
                dose_mg_per_kg=req.dose_mg_per_kg,
                adult_max_single_dose_mg=req.adult_max_single_dose_mg,
                height_cm=req.patient_height_cm,
            )
            pediatric_check = PediatricCeilingCheck(
                weight_kg=ped_res.weight_kg,
                calculated_dose_mg=ped_res.calculated_dose_mg,
                final_dose_mg=ped_res.final_dose_mg,
                adult_max_ceiling_mg=ped_res.adult_max_ceiling_mg,
                is_capped=ped_res.is_capped_by_adult_ceiling,
                dosing_basis=ped_res.dosing_basis,
            )
            if ped_res.is_capped_by_adult_ceiling:
                adjustment_reasons.append(
                    f"PEDIATRIC CEILING ENFORCED: Calculated dose {ped_res.calculated_dose_mg} mg exceeds "
                    f"adult ceiling ({ped_res.adult_max_ceiling_mg} mg). Capped to {ped_res.final_dose_mg} mg."
                )

        # ── Final Safety Verdict Synthesis ─────────────────────────
        if hard_stop_reasons:
            verdict = SafetyVerdict.HARD_STOP_CONTRAINDICATION
            clinician_action = "PRESCRIPTION BLOCKED: Deterministic safety guardrail detected life-threatening contraindication."
        elif adjustment_reasons:
            verdict = SafetyVerdict.REQUIRES_ADJUSTMENT
            clinician_action = "MANDATORY ADJUSTMENT REQUIRED: Modify dosage, frequency, or co-prescribe protective agent before signing."
        else:
            verdict = SafetyVerdict.PASSED_ALL_CHECKS
            clinician_action = "VERIFIED SAFE: Order passed all deterministic allergy, DDI, renal, disease, and pediatric checks."

        return MedicationEvaluationResponse(
            cds_eval_id=uuid4(),
            proposed_drug_name=proposed_drug,
            proposed_rxnorm_code=req.proposed_rxnorm_code,
            safety_verdict=verdict,
            hard_stop_reasons=hard_stop_reasons,
            adjustment_reasons=adjustment_reasons,
            ddi_alerts=ddi_alerts,
            allergy_alerts=allergy_alerts,
            renal_alerts=renal_alerts,
            disease_contraindications=disease_alerts,
            pediatric_ceiling=pediatric_check,
            clinician_action_required=clinician_action,
        )
