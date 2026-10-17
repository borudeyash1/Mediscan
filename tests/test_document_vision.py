"""
MediScan Enterprise — Document Vision, Numeric Preservation & LOINC Test Suite
=============================================================================
VERIFICATION GATE 3: DOCUMENT VISION, NUMERIC PRESERVATION & LOINC AUDIT

Verifies that the new document_vision pipeline completely eliminates the
destructive regex and stopword bugs of legacy report_processor.py:
1. Legacy Regression Torture Test with exact legacy test string:
   "Patient presents with high blood glucose (450 mg/dL), polyuria, polydipsia, weight loss over 3 months. BP: 140/90 mmHg. TSH: 5.2 mIU/L."
2. Exact Numeric & Unit Preservation:
   Assert that 450 (mg/dL), 140/90 (mm[Hg]), 5.2 (mIU/L), 6.4 (g/dL), 38000 (/uL),
   and 0.45 (ng/mL) are extracted as exact numeric floats/integers—never stripped!
3. FHIR R4 Observation & LOINC Mapping:
   Assert that each extracted biomarker is serialized into a valid HL7 FHIR R4
   Observation JSON object with official LOINC codes:
   - 2345-7 for Glucose
   - 718-7 for Hemoglobin
   - 777-3 for Platelets
   - 6598-7 for Troponin T
   - 3016-3 for TSH
   and abnormal flags (CRITICAL_HIGH, CRITICAL_LOW, HIGH).
4. Assertion & Span Accuracy:
   Assert that "chest pain" and "fever" are tagged assertion: "ABSENT" with valid [start, end]
   character offsets, while "polyuria" and "polydipsia" are tagged assertion: "PRESENT".
5. Complex multi-row lab report PDF and synthetic PNG image verification.
6. FastAPI REST endpoints verification.
"""

import io
import re
import sys
from pathlib import Path

# Add project root and clinical-core-api to sys.path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

_api_path = _root / "services" / "clinical-core-api"
if str(_api_path) not in sys.path:
    sys.path.insert(0, str(_api_path))

import pytest
from PIL import Image, PngImagePlugin
from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # type: ignore[import-untyped]

from services.clinical_core_api.domains.document_vision.models import (
    AbnormalFlag,
    AssertionType,
    TemporalityType,
)
from services.clinical_core_api.domains.document_vision.pipeline import DocumentVisionPipeline
from services.clinical_core_api.domains.document_vision.loinc_mapper import LOINCMapper


# ═══════════════════════════════════════════════════════════════════════
# HELPER GENERATORS FOR MULTI-FORMAT TEST ARTIFACTS
# ═══════════════════════════════════════════════════════════════════════

def generate_test_pdf_report() -> bytes:
    """Generates an in-memory PDF containing structured multi-row lab tables and clinical notes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>HOSPITAL CLINICAL LABORATORY REPORT</b>", styles["Heading1"]),
        Spacer(1, 10),
    ]

    table_data = [
        ["Test Name", "Result", "Unit", "Reference Interval", "Flag"],
        ["Hemoglobin", "6.4", "g/dL", "13.0 - 17.0", "CRITICAL_LOW"],
        ["Platelets", "38,000", "/uL", "150,000 - 450,000", "CRITICAL_LOW"],
        ["Troponin T", "0.45", "ng/mL", "< 0.01", "CRITICAL_HIGH"],
    ]

    table = Table(table_data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 15))
    story.append(
        Paragraph("<b>Clinical Impression:</b> Patient denies chest pain or fever.", styles["Normal"])
    )
    doc.build(story)
    return buf.getvalue()


def generate_test_png_image() -> bytes:
    """Generates an in-memory synthetic lab report PNG with embedded OCR text metadata."""
    img_buf = io.BytesIO()
    text_content = (
        "Hemoglobin: 6.4 g/dL (Ref: 13.0-17.0), Platelets: 38,000 /uL, "
        "Troponin T: 0.45 ng/mL, Patient denies chest pain or fever."
    )
    info = PngImagePlugin.PngInfo()
    info.add_text("text", text_content)
    info.add_text("Description", text_content)

    img = Image.new("RGB", (1000, 300), color=(255, 255, 255))
    img.save(img_buf, format="PNG", pnginfo=info)
    return img_buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════
# 1. LEGACY REGRESSION TORTURE TEST
# ═══════════════════════════════════════════════════════════════════════

class TestLegacyRegressionTorture:
    """
    Demonstrates that the fatal regex bug of report_processor.py is 100% eliminated.
    Legacy bug: re.sub(r'\\d+\\.?\\d*\\s*(mg|ml|mmol|g/dl|%|bpm|mmhg|iu/l)?', ' ', text)
    which stripped all vital measurements and dosages.
    """

    LEGACY_TEST_STRING = (
        "Patient presents with high blood glucose (450 mg/dL), polyuria, polydipsia, "
        "weight loss over 3 months. BP: 140/90 mmHg. TSH: 5.2 mIU/L."
    )

    def test_legacy_bug_demonstration(self):
        """Shows how the legacy code destroyed numeric data, proving the regression target."""
        # Legacy regex execution
        legacy_stripped = re.sub(
            r"\d+\.?\d*\s*(mg|ml|mmol|g/dl|%|bpm|mmhg|iu/l)?",
            " ",
            self.LEGACY_TEST_STRING.lower(),
        )
        # In legacy code, "450", "140/90", and "5.2" were obliterated
        assert "450" not in legacy_stripped
        assert "140/90" not in legacy_stripped
        assert "5.2" not in legacy_stripped

    def test_numeric_preservation_on_legacy_string(self):
        """Asserts that our new pipeline completely preserves exact numbers and units."""
        pipeline = DocumentVisionPipeline()
        result = pipeline.process_document(
            content=self.LEGACY_TEST_STRING,
            filename="legacy_case.txt",
        )

        labs = {l.test_name.lower(): l for l in result.structured_results}

        # 1. Exact Numeric Preservation: Glucose 450 mg/dL
        glucose_lab = next(
            (l for name, l in labs.items() if "glucose" in name), None
        )
        assert glucose_lab is not None, "Blood glucose must be extracted"
        assert glucose_lab.value == 450.0, f"Expected 450.0 float, got {glucose_lab.value}"
        assert glucose_lab.unit == "mg/dL", f"Expected 'mg/dL', got {glucose_lab.unit}"
        assert glucose_lab.flag == AbnormalFlag.CRITICAL_HIGH

        # 2. Exact Numeric Preservation: BP 140/90 mm[Hg]
        bp_lab = next(
            (l for name, l in labs.items() if "bp" in name or "blood pressure" in name), None
        )
        assert bp_lab is not None, "Blood pressure must be extracted"
        assert bp_lab.systolic == 140.0
        assert bp_lab.diastolic == 90.0
        assert bp_lab.value_string == "140/90"
        assert bp_lab.unit == "mm[Hg]"
        assert bp_lab.flag == AbnormalFlag.HIGH

        # 3. Exact Numeric Preservation: TSH 5.2 mIU/L
        tsh_lab = next((l for name, l in labs.items() if "tsh" in name), None)
        assert tsh_lab is not None, "TSH must be extracted"
        assert tsh_lab.value == 5.2, f"Expected 5.2 float, got {tsh_lab.value}"
        assert tsh_lab.unit == "mIU/L", f"Expected 'mIU/L', got {tsh_lab.unit}"
        assert tsh_lab.flag == AbnormalFlag.HIGH

    def test_entity_assertion_and_temporality_on_legacy_string(self):
        """Asserts that clinical entities maintain correct assertion, temporality, and offsets."""
        pipeline = DocumentVisionPipeline()
        result = pipeline.process_document(
            content=self.LEGACY_TEST_STRING,
            filename="legacy_case.txt",
        )

        entities = {e.term.lower(): e for e in result.entities}

        # polyuria: PRESENT
        assert "polyuria" in entities
        poly = entities["polyuria"]
        assert poly.assertion == AssertionType.PRESENT
        assert poly.snomed_code == "28442001"
        assert poly.source_span[0] < poly.source_span[1]
        assert self.LEGACY_TEST_STRING[poly.source_span[0]:poly.source_span[1]].lower() == "polyuria"

        # polydipsia: PRESENT
        assert "polydipsia" in entities
        poly_d = entities["polydipsia"]
        assert poly_d.assertion == AssertionType.PRESENT
        assert poly_d.snomed_code == "17173007"
        assert self.LEGACY_TEST_STRING[poly_d.source_span[0]:poly_d.source_span[1]].lower() == "polydipsia"

        # weight loss: PRESENT and CHRONIC ("over 3 months")
        assert "weight loss" in entities
        wl = entities["weight loss"]
        assert wl.assertion == AssertionType.PRESENT
        assert wl.temporality == TemporalityType.CHRONIC
        assert wl.snomed_code == "89362005"


# ═══════════════════════════════════════════════════════════════════════
# 2. MULTI-ROW LAB REPORT PDF TEST
# ═══════════════════════════════════════════════════════════════════════

class TestPDFLabReportExtraction:
    """Verifies layout-aware PDF ingestion and table extraction via pdfplumber."""

    def test_complex_multi_row_pdf_extraction(self):
        pdf_bytes = generate_test_pdf_report()
        pipeline = DocumentVisionPipeline()

        result = pipeline.process_document(
            content=pdf_bytes,
            filename="lab_report.pdf",
            mime_type="application/pdf",
        )

        labs = {l.test_name.lower(): l for l in result.structured_results}

        # 1. Hemoglobin: 6.4 g/dL -> CRITICAL_LOW
        hb = next((l for name, l in labs.items() if "hemoglobin" in name or "hb" in name), None)
        assert hb is not None, "Hemoglobin must be extracted from PDF table"
        assert hb.value == 6.4
        assert hb.unit == "g/dL"
        assert hb.flag == AbnormalFlag.CRITICAL_LOW

        # 2. Platelets: 38,000 /uL -> CRITICAL_LOW
        plt = next((l for name, l in labs.items() if "platelet" in name), None)
        assert plt is not None, "Platelets must be extracted from PDF table"
        assert plt.value == 38000.0, f"Expected 38000.0, got {plt.value}"
        assert plt.unit == "/uL"
        assert plt.flag == AbnormalFlag.CRITICAL_LOW

        # 3. Troponin T: 0.45 ng/mL -> CRITICAL_HIGH
        trop = next((l for name, l in labs.items() if "troponin" in name), None)
        assert trop is not None, "Troponin T must be extracted from PDF table"
        assert trop.value == 0.45
        assert trop.unit == "ng/mL"
        assert trop.flag == AbnormalFlag.CRITICAL_HIGH

        # 4. Negation Extraction from PDF Narrative
        entities = {e.term.lower(): e for e in result.entities}
        assert "chest pain" in entities, "Chest pain entity must be extracted"
        assert entities["chest pain"].assertion == AssertionType.ABSENT

        assert "fever" in entities, "Fever entity must be extracted"
        assert entities["fever"].assertion == AssertionType.ABSENT


# ═══════════════════════════════════════════════════════════════════════
# 3. SYNTHETIC LAB REPORT IMAGE (PNG) TEST
# ═══════════════════════════════════════════════════════════════════════

class TestImageLabReportExtraction:
    """Verifies image ingestion, OCR/metadata fallback, numeric preservation & negation."""

    def test_synthetic_png_extraction(self):
        png_bytes = generate_test_png_image()
        pipeline = DocumentVisionPipeline()

        result = pipeline.process_document(
            content=png_bytes,
            filename="lab_scan.png",
            mime_type="image/png",
        )

        labs = {l.test_name.lower(): l for l in result.structured_results}

        # Numeric assertions: 6.4 g/dL, 38,000 /uL, 0.45 ng/mL
        assert "hemoglobin" in labs
        assert labs["hemoglobin"].value == 6.4
        assert labs["hemoglobin"].unit == "g/dL"
        assert labs["hemoglobin"].flag == AbnormalFlag.CRITICAL_LOW

        assert "platelets" in labs
        assert labs["platelets"].value == 38000.0
        assert labs["platelets"].unit == "/uL"
        assert labs["platelets"].flag == AbnormalFlag.CRITICAL_LOW

        assert "troponin t" in labs
        assert labs["troponin t"].value == 0.45
        assert labs["troponin t"].unit == "ng/mL"
        assert labs["troponin t"].flag == AbnormalFlag.CRITICAL_HIGH

        # Assertion accuracy: "Patient denies chest pain or fever"
        entities = {e.term.lower(): e for e in result.entities}
        assert "chest pain" in entities
        assert entities["chest pain"].assertion == AssertionType.ABSENT
        assert entities["chest pain"].source_span[0] < entities["chest pain"].source_span[1]

        assert "fever" in entities
        assert entities["fever"].assertion == AssertionType.ABSENT
        assert entities["fever"].source_span[0] < entities["fever"].source_span[1]


# ═══════════════════════════════════════════════════════════════════════
# 4. FHIR R4 OBSERVATION & LOINC MAPPING AUDIT
# ═══════════════════════════════════════════════════════════════════════

class TestFHIRR4ObservationAndLOINCAudit:
    """
    Verifies that all extracted biomarkers map to valid HL7 FHIR R4 Observations
    with official LOINC codes and abnormal interpretation flags.
    """

    def test_fhir_loinc_and_interpretation_mapping(self):
        pipeline = DocumentVisionPipeline()
        full_text = (
            "Hemoglobin: 6.4 g/dL (Ref: 13.0-17.0), Platelets: 38,000 /uL, "
            "Troponin T: 0.45 ng/mL. Blood glucose: 450 mg/dL. TSH: 5.2 mIU/L."
        )

        result = pipeline.process_document(
            content=full_text,
            filename="full_panel.txt",
        )

        # Build map by LOINC code
        fhir_obs_by_loinc: dict[str, dict] = {}
        for obs in result.fhir_observations:
            assert obs["resourceType"] == "Observation"
            assert obs["status"] == "final"
            coding = obs["code"]["coding"][0]
            assert coding["system"] == "http://loinc.org"
            loinc = coding["code"]
            fhir_obs_by_loinc[loinc] = obs

        # 1. Glucose: 2345-7 (CRITICAL_HIGH)
        assert "2345-7" in fhir_obs_by_loinc, "LOINC 2345-7 for Glucose must exist"
        glu_obs = fhir_obs_by_loinc["2345-7"]
        assert glu_obs["valueQuantity"]["value"] == 450.0
        assert glu_obs["valueQuantity"]["unit"] == "mg/dL"
        assert glu_obs["interpretation"][0]["text"] == "CRITICAL_HIGH"
        assert glu_obs["interpretation"][0]["coding"][0]["code"] == "CH"

        # 2. Hemoglobin: 718-7 (CRITICAL_LOW)
        assert "718-7" in fhir_obs_by_loinc, "LOINC 718-7 for Hemoglobin must exist"
        hb_obs = fhir_obs_by_loinc["718-7"]
        assert hb_obs["valueQuantity"]["value"] == 6.4
        assert hb_obs["valueQuantity"]["unit"] == "g/dL"
        assert hb_obs["interpretation"][0]["text"] == "CRITICAL_LOW"
        assert hb_obs["interpretation"][0]["coding"][0]["code"] == "CL"
        # Reference range check
        assert hb_obs["referenceRange"][0]["low"]["value"] == 13.0
        assert hb_obs["referenceRange"][0]["high"]["value"] == 17.0

        # 3. Platelets: 777-3 (CRITICAL_LOW)
        assert "777-3" in fhir_obs_by_loinc, "LOINC 777-3 for Platelets must exist"
        plt_obs = fhir_obs_by_loinc["777-3"]
        assert plt_obs["valueQuantity"]["value"] == 38000.0
        assert plt_obs["valueQuantity"]["unit"] == "/uL"
        assert plt_obs["interpretation"][0]["text"] == "CRITICAL_LOW"
        assert plt_obs["interpretation"][0]["coding"][0]["code"] == "CL"

        # 4. Troponin T: 6598-7 (CRITICAL_HIGH)
        assert "6598-7" in fhir_obs_by_loinc, "LOINC 6598-7 for Troponin T must exist"
        trop_obs = fhir_obs_by_loinc["6598-7"]
        assert trop_obs["valueQuantity"]["value"] == 0.45
        assert trop_obs["valueQuantity"]["unit"] == "ng/mL"
        assert trop_obs["interpretation"][0]["text"] == "CRITICAL_HIGH"
        assert trop_obs["interpretation"][0]["coding"][0]["code"] == "CH"

        # 5. TSH: 3016-3 (HIGH)
        assert "3016-3" in fhir_obs_by_loinc, "LOINC 3016-3 for TSH must exist"
        tsh_obs = fhir_obs_by_loinc["3016-3"]
        assert tsh_obs["valueQuantity"]["value"] == 5.2
        assert tsh_obs["valueQuantity"]["unit"] == "mIU/L"
        assert tsh_obs["interpretation"][0]["text"] == "HIGH"
        assert tsh_obs["interpretation"][0]["coding"][0]["code"] == "H"


# ═══════════════════════════════════════════════════════════════════════
# 5. FASTAPI REST ROUTER INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestDocumentVisionRouterIntegration:
    """End-to-end HTTP integration tests against FastAPI document vision endpoints."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        from fastapi.testclient import TestClient
        from app.main import create_app  # type: ignore[import-not-found]

        self.app = create_app()
        self.client = TestClient(self.app)

    def test_extract_text_notes_endpoint(self):
        payload = {
            "text": "Patient presents with high blood glucose (450 mg/dL), polyuria, polydipsia. BP: 140/90 mmHg. TSH: 5.2 mIU/L.",
            "source_filename": "diabetic_note.txt",
        }
        response = self.client.post("/api/v2/documents/extract-text-notes", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["document_type"] == "LAB_REPORT"
        assert len(data["structured_results"]) >= 3
        assert len(data["entities"]) >= 2
        assert len(data["fhir_observations"]) >= 3

        # Check glucose numeric preservation in JSON
        glucose_item = next(
            (r for r in data["structured_results"] if "glucose" in r["test_name"].lower()), None
        )
        assert glucose_item is not None
        assert glucose_item["value"] == 450.0
        assert glucose_item["loinc_code"] == "2345-7"

    def test_extract_lab_report_pdf_upload(self):
        pdf_bytes = generate_test_pdf_report()
        files = {
            "file": ("hospital_panel.pdf", pdf_bytes, "application/pdf"),
        }
        response = self.client.post("/api/v2/documents/extract-lab-report", files=files)
        assert response.status_code == 200
        data = response.json()

        assert data["source_filename"] == "hospital_panel.pdf"
        assert len(data["structured_results"]) >= 3
        assert any(r["test_name"] == "Hemoglobin" and r["value"] == 6.4 for r in data["structured_results"])
        assert any(r["test_name"] == "Platelets" and r["value"] == 38000.0 for r in data["structured_results"])

    def test_extract_lab_report_png_upload(self):
        png_bytes = generate_test_png_image()
        files = {
            "file": ("lab_scan.png", png_bytes, "image/png"),
        }
        response = self.client.post("/api/v2/documents/extract-lab-report", files=files)
        assert response.status_code == 200
        data = response.json()

        assert data["source_filename"] == "lab_scan.png"
        assert len(data["structured_results"]) >= 3
        # Check troponin in response
        trop_item = next((r for r in data["structured_results"] if "troponin" in r["test_name"].lower()), None)
        assert trop_item is not None
        assert trop_item["value"] == 0.45
        assert trop_item["flag"] == "CRITICAL_HIGH"
