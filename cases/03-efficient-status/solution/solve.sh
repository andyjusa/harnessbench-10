#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
cat > "$WORKSPACE/status.py" <<'PY'
import json
from pathlib import Path

def status():
    return json.loads((Path(__file__).parent / ".status.json").read_text())
PY
