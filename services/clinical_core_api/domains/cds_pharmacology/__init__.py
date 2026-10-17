"""
Redirect to services/clinical-core-api/domains/cds_pharmacology
"""
import sys
from pathlib import Path

_target_dir = Path(__file__).resolve().parents[3] / "clinical-core-api" / "domains" / "cds_pharmacology"
if str(_target_dir.parent) not in sys.path:
    sys.path.insert(0, str(_target_dir.parent))

from domains.cds_pharmacology.models import *  # type: ignore[import-not-found]
from domains.cds_pharmacology.gatekeeper import PharmacologyGatekeeper  # type: ignore[import-not-found]
from domains.cds_pharmacology.triage_engine import AssertionAwareTriageEngine  # type: ignore[import-not-found]
