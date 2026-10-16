"""
Domains redirect.
"""
from pathlib import Path
import sys

_domains_path = Path(__file__).resolve().parent.parent.parent / "clinical-core-api" / "domains"
if str(_domains_path) not in sys.path:
    sys.path.insert(0, str(_domains_path))
