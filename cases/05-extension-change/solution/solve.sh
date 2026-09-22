#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
cat > "$WORKSPACE/extension/registry.py" <<'PY'
TOOLS = {"read": {"label": "read"}, "timeout": {"label": "process · supervise"}}
PY
cat > "$WORKSPACE/extension/renderer.py" <<'PY'
def render(name, args, result, expanded=False):
    if name != "timeout":
        return name
    row = f"process · supervise {args.get('target', 'process')}"
    return row if not expanded else f"{row}\nstatus={result['status']} elapsed_ms={result['elapsed_ms']}"
PY
