from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
MODULE_DIRS = [
    ROOT_DIR / "config" / "src",
    ROOT_DIR / "memory" / "src",
    ROOT_DIR / "ai-core" / "src",
    ROOT_DIR / "tools" / "src",
    ROOT_DIR / "integrations" / "src",
]

for module_dir in MODULE_DIRS:
    module_path = str(module_dir)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

