# HarnessBench-10

Ten deterministic Harbor 0.23.0 coding-agent tasks for paired harness comparisons. Every variant uses the same case manifest, containers, and verifiers; correctness (`reward.txt`) is the acceptance gate.

## Contents

- exactly 10 cases: 3 easy, 4 medium, 2 hard, 1 long-running
- offline, deterministic Python verifiers and Docker fixtures
- managed-Pi adapters: `managed-pi-ptc-on` and `managed-pi-ptc-off`
- strategy-neutral case/result schemas
- paired one-repetition PTC campaign contract (20 trials total)

## Setup and offline validation

```sh
uv sync --frozen
uv run python scripts/validate_offline.py
uv run python -m unittest discover -s tests -v
```

The offline validator parses every manifest with Harbor 0.23.0, copies each fixture to a temporary directory, runs its checked-in reference solution, and executes the verifier without Docker or model calls.

## Docker fixture smoke

Docker is optional for offline validation. To exercise one task container manually:

```sh
docker build -t harnessbench-01 cases/01-config-discovery/environment
docker run --rm harnessbench-01 python /app/project/tools/show_config.py
```

On ARM hosts, `python:3.12-slim` has a native ARM image. If a selected agent artifact is x86-only, run Docker with `--platform linux/amd64`; emulation timings must not be compared with native timings.

## Managed-Pi adapter contract

The adapter imports only Harbor's public API. It installs no private source and accepts no embedded credentials.

| Variable | Meaning |
| --- | --- |
| `HARNESSBENCH_PI_ARTIFACT` | Path to a mounted public managed-Pi build artifact; setup verifies that it exists. |
| `HARNESSBENCH_PI_COMMAND` | Command inside the task container. |
| `HARNESSBENCH_PI_ARGS_JSON` | Optional JSON array of fixed command arguments. |

The adapter appends the task instruction and sets `PI_PTC=1` for `ManagedPiPtcOn`, or `PI_PTC=0` for `ManagedPiPtcOff`. Harbor can load the classes by import path:

```sh
export HARNESSBENCH_PI_ARTIFACT=/mounted/pi
export HARNESSBENCH_PI_COMMAND=/mounted/pi
export HARNESSBENCH_PI_ARGS_JSON='["--model", "codex-fixed"]'
PYTHONPATH=src uv run harbor run \
  --path cases/01-config-discovery \
  --agent harnessbench.agents:ManagedPiPtcOn
```

Use `ManagedPiPtcOff` for the paired arm. Supply the same Codex model/settings to both arms through the mounted artifact's documented arguments. Do not put tokens in this repository.

## Campaign

`.autoresearch/contract.toml` freezes the tasks, evaluator, paired variants, repetitions, and hard USD 10 stop. `.autoresearch/program.md` describes execution and recording. Contract creation does **not** authorize paid inference; no paid run is performed by this repository's checks.

## Results

Each JSON result must conform to `schemas/result.schema.json`. `correct` must equal `(verifier_result == 1)`. Timing, turns, backend calls, all token/cache counters, cost, tool calls, retries, timeouts, and failures are mandatory.

## License

Apache-2.0. See `LICENSE`.
