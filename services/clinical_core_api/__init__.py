"""
Package alias for clinical-core-api.
"""
import sys
from pathlib import Path

_api_path = Path(__file__).resolve().parent.parent / "clinical-core-api"
if str(_api_path) not in sys.path:
    sys.path.insert(0, str(_api_path))
