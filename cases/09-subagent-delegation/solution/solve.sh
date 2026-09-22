#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
cat > "$WORKSPACE/delegate.py" <<'PY'
import asyncio

async def delegate(tasks, worker, limit=2):
    if limit < 1:
        raise ValueError("limit must be positive")
    semaphore = asyncio.Semaphore(limit)
    async def one(task):
        async with semaphore:
            try:
                return await worker(task)
            except Exception as exc:
                return {"error": str(exc)}
    return await asyncio.gather(*(one(task) for task in tasks))
PY
