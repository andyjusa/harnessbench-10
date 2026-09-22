#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
cat > "$WORKSPACE/usage.py" <<'PY'
import json
import re

def total_tokens(lines):
    total = 0
    for line in lines:
        match = re.search(r"usage tokens=(\d+)", line)
        if match:
            total += int(match.group(1)); continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if event.get("event") == "usage" and isinstance(event.get("tokens"), int):
            total += event["tokens"]
    return total
PY
