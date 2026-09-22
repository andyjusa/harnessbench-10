# Deterministic Adaptive Orchestrator — HarnessBench-10

## Verdict

The adaptive structure recovered one failed hard task and reached 10/10 correctness, but it was too expensive and slow for default use. Use solo by default; reserve scout→worker for genuinely complex multi-file tasks. A terminal read-only reviewer that cannot trigger correction adds cost without changing the artifact.

## Conditions

- Benchmark/runner revision: `c63e58f28cfd650bb5cf6c35bda3e5127118a017`
- PTC OFF; `openai-codex/gpt-5.6-sol`; thinking `low`
- Baseline: solo for all 10 cases
- Adaptive: 3 easy→solo, 4 medium→worker, 2 hard + 1 long-running→scout→worker→reviewer
- Same fixtures, instructions, and deterministic verifiers

## Aggregate result

| Metric | Solo | Adaptive | Adaptive vs solo |
|---|---:|---:|---:|
| Correct | 9/10 | **10/10** | +1 task |
| Reported cost | **$0.6294** | $0.7450 | +18.4% |
| Wall time | **387.2 s** | 548.0 s | +41.5% |
| Model/backend calls | **56** | 73 | +30.4% |
| Tool calls | **56** | 79 | +41.1% |
| Input tokens | **70,792** | 74,340 | +5.0% |
| Output tokens | **7,924** | 10,980 | +38.6% |
| Cache-read tokens | **75,520** | 87,808 | +16.3% |
| Timeouts | 0 | 0 | — |

## Accuracy effect

Solo failed `05-extension-change`; adaptive scout→worker→reviewer passed it. All other paired arms passed. With one repetition, this is evidence of possible value on a complex multi-file change, not a stable one-point accuracy estimate.

## Stage analysis

The three reviewer stages consumed $0.1068, 10 model calls, and 12 tool calls—14.3% of total adaptive cost. Because reviewer output was not routed back to a correcting worker, reviewers could not change verifier outcomes. They were pure report overhead in this design.

Medium worker routing produced no accuracy gain over solo and was usually more expensive. The useful candidate seam is therefore narrower than the tested router: complex multi-file tasks may merit scout→worker; bounded medium tasks should remain solo.

## Recommended next policy

- Default: solo.
- Complex multi-file discovery: scout→worker.
- Reviewer: omit unless findings feed a bounded correction step.
- Laya: continue shadow-only until it can predict this narrow escalation condition.

## Limitations

One repetition, fixed solo→adaptive order, role behavior expressed through prompts, local processes rather than the production subagent extension, and no reviewer correction loop. Results are descriptive.
