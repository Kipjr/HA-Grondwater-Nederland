"""Test helpers and integration import setup."""

import sys
from pathlib import Path


CUSTOM_COMPONENTS = Path(__file__).resolve().parents[1] / "custom_components"
if str(CUSTOM_COMPONENTS) not in sys.path:
    sys.path.insert(0, str(CUSTOM_COMPONENTS))
