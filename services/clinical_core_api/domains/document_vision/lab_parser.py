"""
MediScan Enterprise — Numeric-Preserving Clinical Lab Parser
============================================================
Replaces the destructive regex bug of report_processor.py.
Preserves exact numerical values, decimal precision, UCUM units,
reference ranges, and evaluates clinical flags (NORMAL, HIGH, LOW,
CRITICAL_HIGH, CRITICAL_LOW).
"""

import re
from typing import Any
from .loinc_mapper import LOINCMapper
from .models import AbnormalFlag, ExtractedLabResult


# Regex patterns for clinical measurements
# Matches test name followed by optional colon/parenthesis, value, and unit
UNIT_NORMALIZATION = {
    "mg/dl": "mg/dL",
    "mg/l": "mg/L",
    "g/dl": "g/dL",
    "g/l": "g/L",
    "mmol/l": "mmol/L",
    "umol/l": "umol/L",
    "miu/l": "mIU/L",
    "uiu/ml": "mIU/L",
    "iu/l": "IU/L",
    "u/l": "U/L",
    "ng/ml": "ng/mL",
    "pg/ml": "pg/mL",
    "ug/dl": "ug/dL",
    "mcg/dl": "ug/dL",
    "mmhg": "mm[Hg]",
    "mm[hg]": "mm[Hg]",
    "/ul": "/uL",
    "k/ul": "/uL",
    "cells/mcl": "/uL",
    "/mcl": "/uL",
    "%": "%",
    "bpm": "/min",
    "/min": "/min",
}


class NumericPreservingLabParser:
    """Parser that deterministically extracts lab values and vitals while preserving numbers."""

    KNOWN_TESTS = [
        "blood glucose",
        "fasting blood sugar",
        "glucose",
        "hba1c",
        "troponin t",
        "troponin i",
        "troponin",
        "hemoglobin",
        "platelet count",
        "platelets",
        "serum creatinine",
        "creatinine",
        "total bilirubin",
        "bilirubin",
        "tsh",
        "white blood cell count",
        "wbc",
        "potassium",
        "sodium",
        "alt",
        "ast",
        "blood pressure",
        "bp",
        "hb",
    ]

    @classmethod
    def normalize_unit(cls, raw_unit: str | None) -> str | None:
        """Normalizes unit string to standard UCUM representation."""
        if not raw_unit:
            return None
        cleaned = raw_unit.strip().lower()
        return UNIT_NORMALIZATION.get(cleaned, raw_unit.strip())

    @classmethod
    def parse_number(cls, raw_val: str) -> float:
        """Parses string with potential commas (e.g. 38,000) into exact float."""
        cleaned = raw_val.replace(",", "").strip()
        return float(cleaned)

    @classmethod
    def extract_blood_pressure(cls, text: str) -> list[ExtractedLabResult]:
        """Extracts Blood Pressure (Systolic / Diastolic) from text."""
        results: list[ExtractedLabResult] = []
        # Matches patterns like: BP: 140/90 mmHg, Blood Pressure: 120/80 mm[Hg], BP 140/90
        bp_pattern = re.compile(
            r"(?i)\b(?:BP|Blood\s+Pressure)\s*[:=]?\s*([0-9]{2,3})\s*/\s*([0-9]{2,3})\s*(?:mm\s*\[?hg\]?)?",
            re.IGNORECASE,
        )

        for match in bp_pattern.finditer(text):
            sys_val = float(match.group(1))
            dia_val = float(match.group(2))
            span = match.span()

            # Flag evaluation: SBP >= 140 or DBP >= 90 is HIGH (Hypertension)
            # SBP >= 180 or DBP >= 120 is CRITICAL_HIGH (Hypertensive Crisis)
            flag = AbnormalFlag.NORMAL
            if sys_val >= 180 or dia_val >= 120:
                flag = AbnormalFlag.CRITICAL_HIGH
            elif sys_val >= 140 or dia_val >= 90:
                flag = AbnormalFlag.HIGH
            elif sys_val < 90 or dia_val < 60:
                flag = AbnormalFlag.LOW

            loinc_entry = LOINCMapper.lookup_loinc("blood pressure")

            results.append(
                ExtractedLabResult(
                    test_name="Blood Pressure",
                    loinc_code=loinc_entry["loinc_code"] if loinc_entry else "85354-9",
                    value=sys_val,
                    value_string=f"{int(sys_val)}/{int(dia_val)}",
                    systolic=sys_val,
                    diastolic=dia_val,
                    unit="mm[Hg]",
                    reference_range="< 120/80 mm[Hg]",
                    flag=flag,
                    confidence=0.98,
                    source_span=span,
                )
            )

        return results

    @classmethod
    def extract_inline_labs(cls, text: str) -> list[ExtractedLabResult]:
        """
        Extracts inline lab findings preserving decimal precision and units.
        Handles cases like:
        - "high blood glucose (450 mg/dL)"
        - "TSH: 5.2 mIU/L"
        - "Hemoglobin: 6.4 g/dL (Ref: 13.0-17.0)"
        - "Platelets: 38,000 /uL"
        - "Troponin T: 0.45 ng/mL"
        """
        results: list[ExtractedLabResult] = []

        # Sort known tests by length descending so multi-word tests match first
        sorted_tests = sorted(cls.KNOWN_TESTS, key=len, reverse=True)
        # Exclude bp from inline generic regex since it's handled specifically
        test_keywords = [t for t in sorted_tests if t not in ["bp", "blood pressure"]]
        test_regex_alt = "|".join(re.escape(t) for t in test_keywords)

        # Pattern:
        # (qualifier)? (test_name) [optional punctuation/parens] (number with optional commas and decimals) [space]? (unit)? [optional ref range]
        pattern = re.compile(
            rf"(?i)(?P<qualifier>high|low|critical|elevated)?\s*"
            rf"(?P<test>{test_regex_alt})"
            rf"\s*(?:[:=]|\(|\bis\b)?\s*"
            rf"(?P<val>[0-9]{{1,3}}(?:,[0-9]{{3}})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)"
            rf"\s*(?P<unit>mg/dL|mg/L|g/dL|g/L|mmol/L|umol/L|mIU/L|uIU/mL|IU/L|U/L|ng/mL|pg/mL|ug/dL|mcg/dL|/uL|k/uL|cells/mcL|/mcL|%)?"
            rf"(?:\s*\(?(?:Ref|Reference|Range)?\s*[:=]?\s*(?P<ref>[0-9.]+\s*[-–]\s*[0-9.]+)\)?)?",
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):
            test_raw = match.group("test").strip()
            val_str = match.group("val").strip()
            unit_raw = match.group("unit")
            ref_raw = match.group("ref")
            span = match.span()

            num_val = cls.parse_number(val_str)
            norm_unit = cls.normalize_unit(unit_raw)

            loinc_entry = LOINCMapper.lookup_loinc(test_raw)
            if not norm_unit and loinc_entry:
                norm_unit = loinc_entry.get("default_unit")

            ref_range = ref_raw.strip() if ref_raw else None
            if not ref_range and loinc_entry and loinc_entry.get("ref_low") is not None:
                ref_range = f"{loinc_entry['ref_low']} - {loinc_entry['ref_high']} {norm_unit or ''}".strip()

            # Flag evaluation
            ref_low = None
            ref_high = None
            if ref_range:
                ref_m = re.match(r"^\s*([0-9.]+)\s*[-–]\s*([0-9.]+)", ref_range)
                if ref_m:
                    ref_low = float(ref_m.group(1))
                    ref_high = float(ref_m.group(2))

            flag = LOINCMapper.evaluate_abnormal_flag(
                test_name=test_raw,
                value=num_val,
                ref_low=ref_low,
                ref_high=ref_high,
            )

            # If user explicitly qualified as high or low
            qualifier = match.group("qualifier")
            if qualifier:
                q_lower = qualifier.lower()
                if "critical" in q_lower:
                    flag = AbnormalFlag.CRITICAL_HIGH if num_val > (ref_high or 0) else AbnormalFlag.CRITICAL_LOW
                elif "high" in q_lower or "elevated" in q_lower:
                    if flag not in [AbnormalFlag.CRITICAL_HIGH, AbnormalFlag.HIGH]:
                        flag = AbnormalFlag.HIGH
                elif "low" in q_lower:
                    if flag not in [AbnormalFlag.CRITICAL_LOW, AbnormalFlag.LOW]:
                        flag = AbnormalFlag.LOW

            results.append(
                ExtractedLabResult(
                    test_name=test_raw,
                    loinc_code=loinc_entry["loinc_code"] if loinc_entry else None,
                    value=num_val,
                    value_string=val_str,
                    unit=norm_unit,
                    reference_range=ref_range,
                    flag=flag,
                    confidence=0.96,
                    source_span=span,
                )
            )

        return results

    @classmethod
    def extract_table_rows(cls, text: str) -> list[ExtractedLabResult]:
        """Extracts structured lab results from pipe-delimited or tabular lines."""
        results: list[ExtractedLabResult] = []

        lines = text.splitlines()
        for line in lines:
            if "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    test_cand = parts[0]
                    # Check if test_cand matches any known test
                    loinc_entry = LOINCMapper.lookup_loinc(test_cand)
                    if loinc_entry:
                        # Find value and unit in following columns
                        val_num = None
                        unit_str = None
                        ref_str = None
                        flag_str = None

                        for col in parts[1:]:
                            # Check if numeric
                            num_match = re.search(r"([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)", col)
                            if num_match and val_num is None:
                                try:
                                    val_num = cls.parse_number(num_match.group(1))
                                    # see if unit in same col
                                    unit_part = col[num_match.end():].strip()
                                    if unit_part:
                                        unit_str = cls.normalize_unit(unit_part)
                                    continue
                                except ValueError:
                                    pass

                            # Check if unit
                            norm_u = cls.normalize_unit(col)
                            if norm_u != col and unit_str is None:
                                unit_str = norm_u
                                continue

                            # Check if reference range
                            if re.search(r"[0-9.]+\s*[-–]\s*[0-9.]+", col):
                                ref_str = col.strip()
                                continue

                            # Check if flag
                            if col.upper() in ["NORMAL", "HIGH", "LOW", "CRITICAL_HIGH", "CRITICAL_LOW", "H", "L", "CH", "CL"]:
                                flag_str = col.upper()

                        if val_num is not None:
                            if not unit_str and loinc_entry:
                                unit_str = loinc_entry.get("default_unit")

                            flag = AbnormalFlag.NORMAL
                            if flag_str in ["CRITICAL_HIGH", "CH"]:
                                flag = AbnormalFlag.CRITICAL_HIGH
                            elif flag_str in ["CRITICAL_LOW", "CL"]:
                                flag = AbnormalFlag.CRITICAL_LOW
                            elif flag_str in ["HIGH", "H"]:
                                flag = AbnormalFlag.HIGH
                            elif flag_str in ["LOW", "L"]:
                                flag = AbnormalFlag.LOW
                            else:
                                flag = LOINCMapper.evaluate_abnormal_flag(test_cand, val_num)

                            results.append(
                                ExtractedLabResult(
                                    test_name=test_cand,
                                    loinc_code=loinc_entry["loinc_code"],
                                    value=val_num,
                                    value_string=str(val_num),
                                    unit=unit_str,
                                    reference_range=ref_str,
                                    flag=flag,
                                    confidence=0.97,
                                    source_span=None,
                                )
                            )

        return results

    @classmethod
    def parse(cls, text: str) -> list[ExtractedLabResult]:
        """
        Parses all lab findings from text (Blood pressure, inline narrative, and table rows),
        deduplicating by test name and prioritizing higher-precision matches.
        """
        all_results: list[ExtractedLabResult] = []

        # 1. Blood pressure extraction
        bp_results = cls.extract_blood_pressure(text)
        all_results.extend(bp_results)

        # 2. Inline labs
        inline_results = cls.extract_inline_labs(text)
        all_results.extend(inline_results)

        # 3. Table rows
        table_results = cls.extract_table_rows(text)
        all_results.extend(table_results)

        # Deduplicate results: if a test is already extracted from inline/table, keep the one with reference range / loinc
        deduped: dict[str, ExtractedLabResult] = {}
        for res in all_results:
            key = LOINCMapper.normalize_test_name(res.test_name)
            if key not in deduped:
                deduped[key] = res
            else:
                existing = deduped[key]
                # If new has reference range or higher confidence, replace
                if res.reference_range and not existing.reference_range:
                    deduped[key] = res
                elif res.flag in [AbnormalFlag.CRITICAL_HIGH, AbnormalFlag.CRITICAL_LOW] and existing.flag not in [AbnormalFlag.CRITICAL_HIGH, AbnormalFlag.CRITICAL_LOW]:
                    deduped[key] = res

        return list(deduped.values())
