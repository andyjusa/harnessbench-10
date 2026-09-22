# Improved PTC ON/OFF — HarnessBench-10

## Verdict

The batching instruction improved PTC mechanics, but not end-to-end utility. Keep PTC OFF as the default.

## Change

The PTC system instruction now forbids discovery for standard tools, asks the model to combine already-knowable operations, runs independent reads with `Promise.all`, and chains dependent calls when no model judgment is needed between them. No executor implementation or benchmark case changed.

- Benchmark revision: `9ad8af8871ae67e8d3879c58e2f8e466f42cdff3`
- Harness source HEAD: `bed5d9d5740e4c70aaecf084c58db572cd1f5a1f` with tested working-tree changes
- Improved `integration.mjs` SHA-256: `0e4e6af2c015c37d25453ad20c4310ca0774e44412dfbaba3a5d15b5ecd7465d`
- Pi 0.85.1; `openai-codex/gpt-5.6-sol`; thinking `low`

## Concurrent paired result

| Metric | PTC OFF | Improved PTC ON | ON vs OFF |
|---|---:|---:|---:|
| Correct | **10/10** | 9/10 | -1 task |
| Reported cost | **$0.4844** | $0.6019 | +24.3% |
| Wall time | **361.8 s** | 466.9 s | +29.1% |
| Model/backend calls | **49** | 52 | +6.1% |
| Tool calls | 48 | **42** | -12.5% |
| Input tokens | **50,624** | 53,281 | +5.2% |
| Output tokens | **6,671** | 10,133 | +51.9% |
| Cache-read tokens | **62,208** | 62,976 | +1.2% |
| Timeouts | 0 | 0 | — |

## Improvement versus the previous PTC ON run

| Metric | Previous ON | Improved ON | Change |
|---|---:|---:|---:|
| Correct | 9/10 | 9/10 | unchanged |
| Model/backend calls | 62 | **52** | -16.1% |
| Tool calls | 52 | **42** | -19.2% |
| Input tokens | 59,748 | **53,281** | -10.8% |
| Cache-read tokens | 85,376 | **62,976** | -26.2% |
| Reported cost | **$0.5977** | $0.6019 | +0.7% |
| Wall time | **415.0 s** | 466.9 s | +12.5% |
| Output tokens | **8,542** | 10,133 | +18.6% |

## Interpretation

The policy achieved its immediate target: fewer outer turns and fewer underlying tool calls. Those savings were offset by longer generated reasoning/code, so cost and latency did not improve. Accuracy remained 9/10, with the failure moving from config discovery to log regression, consistent with substantial one-shot model variance.

The failed `08-log-regression` implementation supported several invented nested JSON usage formats but missed the fixture’s required top-level `{"event":"usage","tokens":N}` format. PTC OFF passed the same task.

## Decision

- Do not promote improved PTC as the default.
- Retain the experiment as evidence that prompting alone can reduce call count but is insufficient to improve total efficiency.
- A future attempt should enforce orchestration structurally or target high-fan-out tasks, rather than adding more prompt text.

## Limitations

One repetition per arm, fixed OFF→ON order, local runner rather than Harbor containers, and Pi-reported usage metadata. Results are descriptive.
