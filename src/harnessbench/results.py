"""Result validation with correctness as the acceptance gate."""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED_METRICS = {
    "wall_time_seconds", "model_turns", "backend_calls", "input_tokens",
    "output_tokens", "cache_read_tokens", "cache_write_tokens", "cost_usd",
    "tool_calls", "retries", "timeouts", "failures",
}


def load_result(path: str | Path) -> dict:
    result = json.loads(Path(path).read_text())
    missing = REQUIRED_METRICS - result.keys()
    if missing:
        raise ValueError(f"missing metrics: {', '.join(sorted(missing))}")
    if result.get("verifier_result") not in (0, 1) or result.get("correct") != (result["verifier_result"] == 1):
        raise ValueError("correctness must equal the binary verifier result")
    result["accepted"] = result["correct"]
    return result
