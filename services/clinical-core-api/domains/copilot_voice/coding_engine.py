"""
Autonomous Medical Coding Generator & Anti-Hallucination Verification Gate.
Maintains canonical lexicons for ICD-10-CM, ICD-11, SNOMED-CT, and CPT.
Deterministically strips any hallucinated or unverified code.
"""

from typing import Any, Optional, Sequence
import structlog
from .models import VerifiedMedicalCode

logger = structlog.get_logger(__name__)

# Canonical Lexicon of Validated Healthcare Terminology
VALID_CODE_LEXICON: dict[str, dict[str, dict[str, Any]]] = {
    "ICD-10-CM": {
        "I21.0": {"desc": "ST elevation (STEMI) myocardial infarction of anterior wall", "hcc": "HCC86"},
        "I21.1": {"desc": "ST elevation (STEMI) myocardial infarction of inferior wall", "hcc": "HCC86"},
        "I21.3": {"desc": "ST elevation (STEMI) myocardial infarction of unspecified site", "hcc": "HCC86"},
        "I21.4": {"desc": "Non-ST elevation (NSTEMI) myocardial infarction", "hcc": "HCC86"},
        "I20.0": {"desc": "Unstable angina", "hcc": "HCC87"},
        "I20.9": {"desc": "Angina pectoris, unspecified", "hcc": None},
        "I50.9": {"desc": "Heart failure, unspecified", "hcc": "HCC85"},
        "I10": {"desc": "Essential (primary) hypertension", "hcc": None},
        "E11.22": {"desc": "Type 2 diabetes mellitus with diabetic chronic kidney disease", "hcc": "HCC18"},
        "E11.9": {"desc": "Type 2 diabetes mellitus without complications", "hcc": "HCC19"},
        "E11.65": {"desc": "Type 2 diabetes mellitus with hyperglycemia", "hcc": "HCC18"},
        "E10.9": {"desc": "Type 1 diabetes mellitus without complications", "hcc": "HCC19"},
        "N18.30": {"desc": "Chronic kidney disease, stage 3 unspecified", "hcc": "HCC138"},
        "N18.31": {"desc": "Chronic kidney disease, stage 3a", "hcc": "HCC138"},
        "N18.32": {"desc": "Chronic kidney disease, stage 3b", "hcc": "HCC138"},
        "N18.4": {"desc": "Chronic kidney disease, stage 4 (severe)", "hcc": "HCC137"},
        "N18.5": {"desc": "Chronic kidney disease, stage 5", "hcc": "HCC136"},
        "N17.9": {"desc": "Acute kidney failure, unspecified", "hcc": "HCC135"},
        "J44.1": {"desc": "Chronic obstructive pulmonary disease with (acute) exacerbation", "hcc": "HCC111"},
        "J44.9": {"desc": "Chronic obstructive pulmonary disease, unspecified", "hcc": "HCC111"},
        "J45.901": {"desc": "Unspecified asthma with (acute) exacerbation", "hcc": None},
        "J18.9": {"desc": "Pneumonia, unspecified organism", "hcc": "HCC114"},
        "A90": {"desc": "Dengue fever [classical dengue]", "hcc": None},
        "A41.9": {"desc": "Sepsis, unspecified organism", "hcc": "HCC2"},
        "R07.9": {"desc": "Chest pain, unspecified", "hcc": None},
        "R07.2": {"desc": "Precordial pain", "hcc": None},
        "R06.02": {"desc": "Shortness of breath", "hcc": None},
        "R06.00": {"desc": "Dyspnea, unspecified", "hcc": None},
        "R50.9": {"desc": "Fever, unspecified", "hcc": None},
        "R53.83": {"desc": "Other fatigue", "hcc": None},
        "R51.9": {"desc": "Headache, unspecified", "hcc": None},
        "R10.9": {"desc": "Abdominal pain, unspecified", "hcc": None},
        "K21.9": {"desc": "Gastro-esophageal reflux disease without esophagitis", "hcc": None},
        "M05.9": {"desc": "Rheumatoid arthritis with rheumatoid factor, unspecified", "hcc": "HCC40"},
        "G40.909": {"desc": "Epilepsy, unspecified, not intractable, without status epilepticus", "hcc": "HCC79"},
        "G43.909": {"desc": "Migraine, unspecified, not intractable, without status migrainosus", "hcc": None},
        "F32.9": {"desc": "Major depressive disorder, single episode, unspecified", "hcc": "HCC59"},
        "F41.1": {"desc": "Generalized anxiety disorder", "hcc": None},
        "D64.9": {"desc": "Anemia, unspecified", "hcc": None},
        "E03.9": {"desc": "Hypothyroidism, unspecified", "hcc": None},
    },
    "ICD-11": {
        "BA41.0": {"desc": "Acute myocardial infarction with ST elevation", "hcc": None},
        "BA41.1": {"desc": "Acute myocardial infarction without ST elevation", "hcc": None},
        "BA00": {"desc": "Essential hypertension", "hcc": None},
        "5A11": {"desc": "Type 2 diabetes mellitus", "hcc": None},
        "GB61.3": {"desc": "Chronic kidney disease, stage 3b", "hcc": None},
        "GB61.4": {"desc": "Chronic kidney disease, stage 4", "hcc": None},
        "CA22.0": {"desc": "Chronic obstructive pulmonary disease with acute exacerbation", "hcc": None},
        "CA23": {"desc": "Asthma", "hcc": None},
        "1D20": {"desc": "Dengue", "hcc": None},
        "MD11.0": {"desc": "Chest pain", "hcc": None},
        "MD32": {"desc": "Dyspnoea", "hcc": None},
    },
    "SNOMED-CT": {
        "22298006": {"desc": "Myocardial infarction", "hcc": None},
        "401303003": {"desc": "Acute ST segment elevation myocardial infarction", "hcc": None},
        "401314000": {"desc": "Acute non-ST segment elevation myocardial infarction", "hcc": None},
        "38341003": {"desc": "Hypertensive disorder, systemic arterial", "hcc": None},
        "44054006": {"desc": "Diabetes mellitus type 2", "hcc": None},
        "433144002": {"desc": "Chronic kidney disease stage 3B", "hcc": None},
        "433146000": {"desc": "Chronic kidney disease stage 4", "hcc": None},
        "13645005": {"desc": "Chronic obstructive lung disease", "hcc": None},
        "195967001": {"desc": "Asthma", "hcc": None},
        "38362002": {"desc": "Dengue fever", "hcc": None},
        "91302008": {"desc": "Sepsis", "hcc": None},
        "29857009": {"desc": "Chest pain", "hcc": None},
        "267036007": {"desc": "Dyspnea", "hcc": None},
        "386661006": {"desc": "Fever", "hcc": None},
        "84229001": {"desc": "Fatigue", "hcc": None},
    },
    "CPT": {
        "99203": {"desc": "Office or other outpatient visit for evaluation and management of new patient, low complexity", "hcc": None},
        "99204": {"desc": "Office or other outpatient visit for evaluation and management of new patient, moderate complexity (45-59 mins)", "hcc": None},
        "99205": {"desc": "Office or other outpatient visit for evaluation and management of new patient, high complexity (60-74 mins)", "hcc": None},
        "99213": {"desc": "Office or other outpatient visit for evaluation and management of established patient, low complexity (20-29 mins)", "hcc": None},
        "99214": {"desc": "Office or other outpatient visit for evaluation and management of established patient, moderate complexity (30-39 mins)", "hcc": None},
        "99215": {"desc": "Office or other outpatient visit for evaluation and management of established patient, high complexity (40-54 mins)", "hcc": None},
        "93000": {"desc": "Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report", "hcc": None},
        "71046": {"desc": "Radiologic examination, chest; 2 views", "hcc": None},
        "80053": {"desc": "Comprehensive metabolic panel (CMP)", "hcc": None},
        "85025": {"desc": "Complete blood count (CBC) with automated differential", "hcc": None},
        "83036": {"desc": "Hemoglobin; glycosylated (A1C)", "hcc": None},
        "84484": {"desc": "Troponin, quantitative", "hcc": None},
    },
}


class AutonomousCodingEngine:
    """
    Deterministic anti-hallucination medical coding engine.
    Cross-checks proposed codes against certified healthcare vocabularies.
    """

    def __init__(self):
        self.lexicon = VALID_CODE_LEXICON

    def verify_code(self, code: str, code_system: str) -> Optional[VerifiedMedicalCode]:
        """
        Verify a single code string against the given code system.
        Returns VerifiedMedicalCode if strictly valid, None if hallucinated/unrecognized.
        """
        clean_code = code.strip().upper()
        clean_system = code_system.strip().upper()

        # Normalize system aliases
        if clean_system in {"ICD-10", "ICD10", "ICD-10-CM"}:
            system_key = "ICD-10-CM"
        elif clean_system in {"ICD-11", "ICD11"}:
            system_key = "ICD-11"
        elif clean_system in {"SNOMED", "SNOMED-CT", "SNOMEDCT"}:
            system_key = "SNOMED-CT"
        elif clean_system in {"CPT", "CPT-4"}:
            system_key = "CPT"
        else:
            system_key = code_system

        system_dict = self.lexicon.get(system_key)
        if not system_dict:
            return None

        # Check exact code match
        if clean_code in system_dict:
            info = system_dict[clean_code]
            return VerifiedMedicalCode(
                code=clean_code,
                code_system=system_key,
                description=info["desc"],
                is_verified=True,
                hcc_category=info.get("hcc"),
                confidence=1.0,
            )

        # Check case-insensitive match
        for valid_c, info in system_dict.items():
            if valid_c.upper() == clean_code:
                return VerifiedMedicalCode(
                    code=valid_c,
                    code_system=system_key,
                    description=info["desc"],
                    is_verified=True,
                    hcc_category=info.get("hcc"),
                    confidence=1.0,
                )

        # Hallucinated or invalid code
        logger.warning(
            "medical_coding.hallucination_detected",
            rejected_code=code,
            code_system=code_system,
        )
        return None

    def filter_and_verify_codes(
        self,
        candidate_codes: Sequence[dict[str, Any] | str],
        default_system: str = "ICD-10-CM",
        evidence_ids: Optional[list[str]] = None,
    ) -> list[VerifiedMedicalCode]:
        """
        Anti-Hallucination Gate:
        Accepts candidate code objects or strings from LLM output.
        Returns ONLY validated codes from canonical lexicon, stripping fakes.
        """
        verified_results: list[VerifiedMedicalCode] = []
        seen_keys: set[tuple[str, str]] = set()

        for cand in candidate_codes:
            if isinstance(cand, str):
                code_str = cand
                system = default_system
            elif isinstance(cand, dict):
                code_str = str(cand.get("code", "")).strip()
                system = str(cand.get("code_system", cand.get("system", default_system))).strip()
            else:
                continue

            verified = self.verify_code(code_str, system)
            if verified:
                key = (verified.code_system, verified.code)
                if key not in seen_keys:
                    seen_keys.add(key)
                    if evidence_ids:
                        verified.evidence_utterance_ids = list(evidence_ids)
                    verified_results.append(verified)

        return verified_results

    def suggest_codes_for_encounter(
        self,
        symptoms: list[str],
        suspected_conditions: list[str],
        is_high_complexity: bool = False,
        evidence_ids: Optional[list[str]] = None,
    ) -> dict[str, list[VerifiedMedicalCode]]:
        """
        Generate comprehensive, strictly verified code bundles for an encounter.
        """
        e_ids = evidence_ids or []
        icd10_candidates: list[str] = []
        icd11_candidates: list[str] = []
        snomed_candidates: list[str] = []
        cpt_candidates: list[str] = []

        # Map suspected conditions to candidates
        cond_text = " ".join([c.lower() for c in suspected_conditions + symptoms])

        if "stemi" in cond_text or "myocardial infarction" in cond_text or "heart attack" in cond_text:
            icd10_candidates.append("I21.0")
            icd11_candidates.append("BA41.0")
            snomed_candidates.append("22298006")
            cpt_candidates.extend(["93000", "84484"])

        if "chest pain" in cond_text:
            icd10_candidates.append("R07.9")
            icd11_candidates.append("MD11.0")
            snomed_candidates.append("29857009")

        if "diabetes" in cond_text or "t2dm" in cond_text:
            if "ckd" in cond_text or "kidney" in cond_text:
                icd10_candidates.append("E11.22")
                icd10_candidates.append("N18.32")
                icd11_candidates.append("GB61.3")
                snomed_candidates.append("433144002")
            else:
                icd10_candidates.append("E11.9")
                icd11_candidates.append("5A11")
                snomed_candidates.append("44054006")
            cpt_candidates.append("83036")

        if "hypertension" in cond_text or "high blood pressure" in cond_text:
            icd10_candidates.append("I10")
            icd11_candidates.append("BA00")
            snomed_candidates.append("38341003")

        if "dyspnea" in cond_text or "shortness of breath" in cond_text:
            icd10_candidates.append("R06.02")
            icd11_candidates.append("MD32")
            snomed_candidates.append("267036007")

        if "dengue" in cond_text:
            icd10_candidates.append("A90")
            icd11_candidates.append("1D20")
            snomed_candidates.append("38362002")
            cpt_candidates.append("85025")

        if "copd" in cond_text:
            icd10_candidates.append("J44.1")
            icd11_candidates.append("CA22.0")
            snomed_candidates.append("13645005")

        if "asthma" in cond_text:
            icd10_candidates.append("J45.901")
            icd11_candidates.append("CA23")
            snomed_candidates.append("195967001")

        # Evaluation & Management (E/M) CPT selection
        if is_high_complexity or len(icd10_candidates) >= 2:
            cpt_candidates.append("99215")  # Level 5 high complexity
        else:
            cpt_candidates.append("99214")  # Level 4 moderate complexity

        return {
            "icd10": self.filter_and_verify_codes(icd10_candidates, default_system="ICD-10-CM", evidence_ids=e_ids),
            "icd11": self.filter_and_verify_codes(icd11_candidates, default_system="ICD-11", evidence_ids=e_ids),
            "snomed": self.filter_and_verify_codes(snomed_candidates, default_system="SNOMED-CT", evidence_ids=e_ids),
            "cpt": self.filter_and_verify_codes(cpt_candidates, default_system="CPT", evidence_ids=e_ids),
        }
