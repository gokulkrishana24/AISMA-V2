from __future__ import annotations

import sys
from pathlib import Path

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import uvicorn  # noqa: E402

from api.main import app  # noqa: E402

if __name__ == "__main__":
    print("[AISMA v2] Starting FastAPI Enterprise Backend Daemon on http://0.0.0.0:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

