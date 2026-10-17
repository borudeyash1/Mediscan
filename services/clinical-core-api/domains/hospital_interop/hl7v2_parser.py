"""
HL7v2 Pipe/Bar Message Parser.
Parses standard HL7v2 MLLP payloads (ORU^R01 observation results and ADT^A01 admissions)
into structured entities and compliant HL7 FHIR R4 resources.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4
import structlog

logger = structlog.get_logger(__name__)


class HL7v2Parser:
    """Robust pipe/bar delimiter parser for HL7v2 messages."""

    def parse_message(self, raw_message: str) -> dict[str, Any]:
        """
        Parses raw HL7v2 pipe message into structured segments:
        Returns: {
            "message_type": "ORU^R01",
            "patient": {...},
            "observations": [...],
            "fhir_resources": [...]
        }
        """
        lines = [line.strip() for line in raw_message.strip().splitlines() if line.strip()]
        if not lines:
            raise ValueError("Empty HL7v2 message received")

        message_type = "UNKNOWN"
        patient_info: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []

        field_sep = "|"
        comp_sep = "^"

        for line in lines:
            seg_id = line[:3]
            fields = line.split(field_sep)

            if seg_id == "MSH":
                # MSH-9 is Message Type
                if len(fields) > 8:
                    message_type = fields[8]

            elif seg_id == "PID":
                # PID-3: Patient ID, PID-5: Patient Name (Family^Given), PID-7: DOB, PID-8: Sex
                pid_id = fields[3].split(comp_sep)[0] if len(fields) > 3 else f"pat_{uuid4().hex[:6]}"
                name_parts = fields[5].split(comp_sep) if len(fields) > 5 else ["Unknown"]
                family = name_parts[0] if name_parts else "Doe"
                given = name_parts[1] if len(name_parts) > 1 else "John"
                dob = fields[7] if len(fields) > 7 else "1985-01-01"
                gender = fields[8].lower() if len(fields) > 8 else "unknown"
                if gender in {"m", "male"}:
                    gender = "male"
                elif gender in {"f", "female"}:
                    gender = "female"

                patient_info = {
                    "patient_id": pid_id,
                    "family_name": family,
                    "given_name": given,
                    "birth_date": dob,
                    "gender": gender,
                }

            elif seg_id == "OBX":
                # OBX-2: Value Type (NM/ST), OBX-3: Identifier (Code^Desc^System),
                # OBX-5: Value, OBX-6: Units, OBX-7: Ref Range, OBX-8: Abnormal Flag
                val_type = fields[2] if len(fields) > 2 else "NM"
                code_parts = fields[3].split(comp_sep) if len(fields) > 3 else ["unknown", "Observation"]
                code = code_parts[0]
                desc = code_parts[1] if len(code_parts) > 1 else "Laboratory Observation"

                raw_val = fields[5] if len(fields) > 5 else ""
                numeric_val: Optional[float] = None
                try:
                    numeric_val = float(raw_val)
                except ValueError:
                    pass

                units = fields[6] if len(fields) > 6 else ""
                ref_range = fields[7] if len(fields) > 7 else ""
                abnormal_flag = fields[8] if len(fields) > 8 else ""

                observations.append({
                    "loinc_code": code,
                    "description": desc,
                    "value_type": val_type,
                    "raw_value": raw_val,
                    "numeric_value": numeric_val,
                    "units": units,
                    "reference_range": ref_range,
                    "abnormal_flag": abnormal_flag,
                })

        # Map to FHIR R4 Resources
        pat_id = patient_info.get("patient_id", f"pat_{uuid4().hex[:6]}")
        fhir_patient = {
            "resourceType": "Patient",
            "id": pat_id,
            "name": [{
                "family": patient_info.get("family_name", "Doe"),
                "given": [patient_info.get("given_name", "John")],
            }],
            "gender": patient_info.get("gender", "unknown"),
            "birthDate": patient_info.get("birth_date", "1985-01-01"),
        }

        fhir_observations = []
        for obs in observations:
            obs_id = f"obs_{uuid4().hex[:8]}"
            fhir_obs: dict[str, Any] = {
                "resourceType": "Observation",
                "id": obs_id,
                "status": "final",
                "subject": {"reference": f"Patient/{pat_id}"},
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": obs["loinc_code"],
                        "display": obs["description"],
                    }],
                    "text": obs["description"],
                },
            }
            if obs["numeric_value"] is not None:
                fhir_obs["valueQuantity"] = {
                    "value": obs["numeric_value"],
                    "unit": obs["units"],
                    "system": "http://unitsofmeasure.org",
                    "code": obs["units"],
                }
            else:
                fhir_obs["valueString"] = obs["raw_value"]

            if obs["reference_range"]:
                fhir_obs["referenceRange"] = [{"text": obs["reference_range"]}]

            if obs["abnormal_flag"]:
                fhir_obs["interpretation"] = [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": obs["abnormal_flag"],
                    }]
                }]

            fhir_observations.append(fhir_obs)

        return {
            "message_type": message_type,
            "patient": patient_info,
            "observations": observations,
            "fhir_resources": [fhir_patient] + fhir_observations,
        }


hl7v2_parser = HL7v2Parser()
