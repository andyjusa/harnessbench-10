#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
cat > "$WORKSPACE/project/tools/show_config.py" <<'PY'
import json
from pathlib import Path

p = Path(__file__).resolve()
config = next((parent / ".pi/settings.json" for parent in p.parents if (parent / ".pi/settings.json").is_file()))
print(json.loads(config.read_text())["model"])
PY
