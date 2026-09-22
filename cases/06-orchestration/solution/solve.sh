#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
cat > "$WORKSPACE/orchestrator.py" <<'PY'
import asyncio

async def collect(search_nodes, search_facts):
    nodes, facts = await asyncio.gather(search_nodes(), search_facts())
    return {"nodes": nodes, "facts": facts}
PY
