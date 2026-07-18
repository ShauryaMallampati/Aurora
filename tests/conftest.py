from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / "src")
CURRENT = os.environ.get("PYTHONPATH")
os.environ["PYTHONPATH"] = SRC if not CURRENT else SRC + os.pathsep + CURRENT
