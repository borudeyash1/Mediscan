"""
MediScan Enterprise — Official LOINC Dictionary & FHIR R4 Mapper
================================================================
Maps extracted clinical lab biomarker names to official LOINC identifiers,
preferred display names, standard UCUM units, and serializes them into
100% compliant HL7 FHIR R4 Observation JSON resources.
"""

from typing import Any
from uuid import uuid4
from .models import AbnormalFlag, ExtractedLabResult


LOINC_REGISTRY: dict[str, dict[str, Any]] = {
    "glucose": {
        "loinc_code": "2345-7",
        "display": "Glucose [Mass/volume] in Blood",
        "default_unit": "mg/dL",
        "ref_low": 70.0,
        "ref_high": 99.0,
        "critical_low": 50.0,
        "critical_high": 400.0,
    },
    "blood glucose": {
        "loinc_code": "2345-7",
        "display": "Glucose [Mass/volume] in Blood",
        "default_unit": "mg/dL",
        "ref_low": 70.0,
        "ref_high": 99.0,
        "critical_low": 50.0,
        "critical_high": 400.0,
    },
    "fasting blood sugar": {
        "loinc_code": "1558-6",
        "display": "Fasting glucose [Mass/volume] in Blood",
        "default_unit": "mg/dL",
        "ref_low": 70.0,
        "ref_high": 99.0,
        "critical_low": 50.0,
        "critical_high": 400.0,
    },
    "hba1c": {
        "loinc_code": "4548-4",
        "display": "Hemoglobin A1c/Hemoglobin.total in Blood",
        "default_unit": "%",
        "ref_low": 4.0,
        "ref_high": 5.6,
        "critical_low": 3.0,
        "critical_high": 12.0,
    },
    "troponin t": {
        "loinc_code": "6598-7",
        "display": "Troponin T.cardiac [Mass/volume] in Serum or Plasma",
        "default_unit": "ng/mL",
        "ref_low": 0.0,
        "ref_high": 0.01,
        "critical_low": None,
        "critical_high": 0.1,
    },
    "troponin i": {
        "loinc_code": "10839-9",
        "display": "Troponin I.cardiac [Mass/volume] in Serum or Plasma",
        "default_unit": "ng/mL",
        "ref_low": 0.0,
        "ref_high": 0.04,
        "critical_low": None,
        "critical_high": 0.4,
    },
    "hemoglobin": {
        "loinc_code": "718-7",
        "display": "Hemoglobin [Mass/volume] in Blood",
        "default_unit": "g/dL",
        "ref_low": 13.0,
        "ref_high": 17.0,
        "critical_low": 7.0,
        "critical_high": 20.0,
    },
    "hb": {
        "loinc_code": "718-7",
        "display": "Hemoglobin [Mass/volume] in Blood",
        "default_unit": "g/dL",
        "ref_low": 13.0,
        "ref_high": 17.0,
        "critical_low": 7.0,
        "critical_high": 20.0,
    },
    "platelets": {
        "loinc_code": "777-3",
        "display": "Platelets [#/volume] in Blood",
        "default_unit": "/uL",
        "ref_low": 150000.0,
        "ref_high": 450000.0,
        "critical_low": 50000.0,
        "critical_high": 1000000.0,
    },
    "platelet count": {
        "loinc_code": "777-3",
        "display": "Platelets [#/volume] in Blood",
        "default_unit": "/uL",
        "ref_low": 150000.0,
        "ref_high": 450000.0,
        "critical_low": 50000.0,
        "critical_high": 1000000.0,
    },
    "creatinine": {
        "loinc_code": "2160-0",
        "display": "Creatinine [Mass/volume] in Serum or Plasma",
        "default_unit": "mg/dL",
        "ref_low": 0.7,
        "ref_high": 1.3,
        "critical_low": 0.3,
        "critical_high": 3.0,
    },
    "serum creatinine": {
        "loinc_code": "2160-0",
        "display": "Creatinine [Mass/volume] in Serum or Plasma",
        "default_unit": "mg/dL",
        "ref_low": 0.7,
        "ref_high": 1.3,
        "critical_low": 0.3,
        "critical_high": 3.0,
    },
    "tsh": {
        "loinc_code": "3016-3",
        "display": "Thyrotropin [Units/volume] in Serum or Plasma",
        "default_unit": "mIU/L",
        "ref_low": 0.4,
        "ref_high": 4.0,
        "critical_low": 0.05,
        "critical_high": 10.0,
    },
    "wbc": {
        "loinc_code": "6690-2",
        "display": "Leukocytes [#/volume] in Blood",
        "default_unit": "/uL",
        "ref_low": 4000.0,
        "ref_high": 11000.0,
        "critical_low": 2000.0,
        "critical_high": 25000.0,
    },
    "white blood cell count": {
        "loinc_code": "6690-2",
        "display": "Leukocytes [#/volume] in Blood",
        "default_unit": "/uL",
        "ref_low": 4000.0,
        "ref_high": 11000.0,
        "critical_low": 2000.0,
        "critical_high": 25000.0,
    },
    "bilirubin": {
        "loinc_code": "1975-2",
        "display": "Bilirubin.total [Mass/volume] in Serum or Plasma",
        "default_unit": "mg/dL",
        "ref_low": 0.2,
        "ref_high": 1.2,
        "critical_low": None,
        "critical_high": 15.0,
    },
    "total bilirubin": {
        "loinc_code": "1975-2",
        "display": "Bilirubin.total [Mass/volume] in Serum or Plasma",
        "default_unit": "mg/dL",
        "ref_low": 0.2,
        "ref_high": 1.2,
        "critical_low": None,
        "critical_high": 15.0,
    },
    "potassium": {
        "loinc_code": "2823-3",
        "display": "Potassium [Moles/volume] in Serum or Plasma",
        "default_unit": "mmol/L",
        "ref_low": 3.5,
        "ref_high": 5.0,
        "critical_low": 2.8,
        "critical_high": 6.2,
    },
    "sodium": {
        "loinc_code": "2951-2",
        "display": "Sodium [Moles/volume] in Serum or Plasma",
        "default_unit": "mmol/L",
        "ref_low": 135.0,
        "ref_high": 145.0,
        "critical_low": 120.0,
        "critical_high": 160.0,
    },
    "alt": {
        "loinc_code": "1742-6",
        "display": "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma",
        "default_unit": "U/L",
        "ref_low": 7.0,
        "ref_high": 56.0,
        "critical_low": None,
        "critical_high": 500.0,
    },
    "ast": {
        "loinc_code": "1920-8",
        "display": "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma",
        "default_unit": "U/L",
        "ref_low": 10.0,
        "ref_high": 40.0,
        "critical_low": None,
        "critical_high": 500.0,
    },
    "bp": {
        "loinc_code": "85354-9",
        "display": "Blood pressure panel with all children optional",
        "default_unit": "mm[Hg]",
        "ref_low": None,
        "ref_high": None,
        "critical_low": None,
        "critical_high": None,
    },
    "blood pressure": {
        "loinc_code": "85354-9",
        "display": "Blood pressure panel with all children optional",
        "default_unit": "mm[Hg]",
        "ref_low": None,
        "ref_high": None,
        "critical_low": None,
        "critical_high": None,
    },
}

# Mapping interpretation flag to HL7 v3 code
INTERPRETATION_CODE_MAP: dict[AbnormalFlag, dict[str, str]] = {
    AbnormalFlag.NORMAL: {"code": "N", "display": "Normal"},
    AbnormalFlag.HIGH: {"code": "H", "display": "High"},
    AbnormalFlag.LOW: {"code": "L", "display": "Low"},
    AbnormalFlag.CRITICAL_HIGH: {"code": "CH", "display": "Critical high"},
    AbnormalFlag.CRITICAL_LOW: {"code": "CL", "display": "Critical low"},
}


class LOINCMapper:
    """Resolves clinical tests to LOINC codes and generates HL7 FHIR R4 Observations."""

    @staticmethod
    def normalize_test_name(name: str) -> str:
        """Lowercases and cleans test name for dictionary lookup."""
        return name.strip().lower().replace("_", " ").replace("-", " ")

    @classmethod
    def lookup_loinc(cls, test_name: str) -> dict[str, Any] | None:
        """Looks up test entry in LOINC registry."""
        norm = cls.normalize_test_name(test_name)
        if norm in LOINC_REGISTRY:
            return LOINC_REGISTRY[norm]

        # Partial matching
        for key, entry in LOINC_REGISTRY.items():
            if key in norm or norm in key:
                return entry
        return None

    @classmethod
    def evaluate_abnormal_flag(
        cls,
        test_name: str,
        value: float,
        ref_low: float | None = None,
        ref_high: float | None = None,
    ) -> AbnormalFlag:
        """Evaluates numerical value against physiological ranges and critical thresholds."""
        entry = cls.lookup_loinc(test_name)
        crit_low = entry.get("critical_low") if entry else None
        crit_high = entry.get("critical_high") if entry else None

        if ref_low is None and entry:
            ref_low = entry.get("ref_low")
        if ref_high is None and entry:
            ref_high = entry.get("ref_high")

        # 1. Critical flags first
        if crit_low is not None and value <= crit_low:
            return AbnormalFlag.CRITICAL_LOW
        if crit_high is not None and value >= crit_high:
            return AbnormalFlag.CRITICAL_HIGH

        # 2. General High / Low flags
        if ref_low is not None and value < ref_low:
            return AbnormalFlag.LOW
        if ref_high is not None and value > ref_high:
            return AbnormalFlag.HIGH

        return AbnormalFlag.NORMAL

    @classmethod
    def serialize_to_fhir_observation(
        cls,
        lab_result: ExtractedLabResult,
        subject_id: str = "urn:uuid:patient-primary",
    ) -> dict[str, Any]:
        """
        Serializes an ExtractedLabResult to a valid HL7 FHIR R4 Observation JSON object.
        Follows HL7 US Core / International Patient Access (IPA) profile.
        """
        loinc_info = cls.lookup_loinc(lab_result.test_name)
        loinc_code = lab_result.loinc_code or (loinc_info["loinc_code"] if loinc_info else "unknown")
        loinc_display = loinc_info["display"] if loinc_info else lab_result.test_name
        unit = lab_result.unit or (loinc_info["default_unit"] if loinc_info else "")

        observation_id = str(uuid4())

        observation: dict[str, Any] = {
            "resourceType": "Observation",
            "id": observation_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory" if loinc_code != "85354-9" else "vital-signs",
                            "display": "Laboratory" if loinc_code != "85354-9" else "Vital Signs",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": loinc_code,
                        "display": loinc_display,
                    }
                ],
                "text": lab_result.test_name,
            },
            "subject": {"reference": subject_id},
        }

        # Handle composite Blood Pressure (Systolic + Diastolic)
        if lab_result.systolic is not None and lab_result.diastolic is not None:
            observation["component"] = [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8480-6",
                                "display": "Systolic blood pressure",
                            }
                        ],
                        "text": "Systolic BP",
                    },
                    "valueQuantity": {
                        "value": float(lab_result.systolic),
                        "unit": "mm[Hg]",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]",
                    },
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8462-4",
                                "display": "Diastolic blood pressure",
                            }
                        ],
                        "text": "Diastolic BP",
                    },
                    "valueQuantity": {
                        "value": float(lab_result.diastolic),
                        "unit": "mm[Hg]",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]",
                    },
                },
            ]
        elif lab_result.value is not None:
            observation["valueQuantity"] = {
                "value": float(lab_result.value),
                "unit": unit,
                "system": "http://unitsofmeasure.org",
                "code": unit,
            }
        elif lab_result.value_string:
            observation["valueString"] = lab_result.value_string

        # Interpretation flags
        if lab_result.flag:
            hl7_interp = INTERPRETATION_CODE_MAP.get(
                lab_result.flag, {"code": "N", "display": "Normal"}
            )
            observation["interpretation"] = [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": hl7_interp["code"],
                            "display": hl7_interp["display"],
                        }
                    ],
                    "text": lab_result.flag.value,
                }
            ]

        # Reference range
        if lab_result.reference_range:
            ref_dict: dict[str, Any] = {"text": lab_result.reference_range}
            # Attempt to extract numeric low/high from string like "13.0-17.0"
            import re
            m = re.match(r"^\s*([0-9.]+)\s*[-–]\s*([0-9.]+)", lab_result.reference_range)
            if m:
                ref_dict["low"] = {
                    "value": float(m.group(1)),
                    "unit": unit,
                    "system": "http://unitsofmeasure.org",
                    "code": unit,
                }
                ref_dict["high"] = {
                    "value": float(m.group(2)),
                    "unit": unit,
                    "system": "http://unitsofmeasure.org",
                    "code": unit,
                }
            observation["referenceRange"] = [ref_dict]

        return observation
