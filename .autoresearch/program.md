# Paired PTC ON/OFF campaign

This document defines a future campaign; it does not authorize paid inference.

1. Run `uv sync --frozen`, `uv run python scripts/validate_offline.py`, and the unit tests.
2. Freeze one Codex model, model settings, mounted managed-Pi artifact, command arguments, Harbor 0.23.0 lockfile, task tree hashes, and execution environment.
3. For each of the 10 manifest entries, run exactly one paired trial with `ManagedPiPtcOn` and one with `ManagedPiPtcOff` (20 trials total). Use the same task/evaluator and change only `PI_PTC`.
4. Before each launch, record a unique run ID, case ID, variant, resolved model/settings, artifact identity, task-tree hash, and remaining dollar budget. Do not launch if the next trial could cross the hard USD 10 aggregate limit.
5. Record every attempt, including failures/timeouts, against `schemas/result.schema.json`. Never omit a failed arm or retry silently. Correctness equals the binary verifier result and gates all efficiency comparisons.
6. Compare paired results only after all available arms have matching identities. Report correctness first, then wall time, model turns, backend calls, token/cache counts, cost, tool calls, retries, timeouts, and failures. One repetition supports a descriptive comparison only; adoption remains a manual decision.

Stop immediately on paid-budget exhaustion, model/settings drift, fixture/evaluator mutation, missing telemetry, external side effects, credentials in artifacts, or an unmatched paired arm. Do not use production or GPU resources.
