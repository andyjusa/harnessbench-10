# Typed PTC ON/OFF — HarnessBench-10

## Verdict

Typed direct bindings recovered correctness and reduced model/tool calls, but raw JSON-schema injection made PTC materially more expensive and slower than native tools. Keep PTC OFF as the default.

## Implementation

Each turn receives the active tools as typed signatures and binds them directly with `tools.use(...)`. The model used no `tools.call`, `tools.list`, or `tools.describe` calls in this campaign. This is closer to the paper’s generated typed-function module, while retaining the JavaScript VM and real Pi tools.

- Benchmark revision: `e57f61b3aae5f9f3910b3a481f5b24bbd9a3bdb1`
- Typed `integration.mjs` SHA-256: `b9e3c1b34ec18ce2178e7fa99e136b47898b2a53a4eb0afb61f6272a53b44344`
- Pi 0.85.1; `openai-codex/gpt-5.6-sol`; thinking `low`

## Concurrent paired result

| Metric | PTC OFF | Typed PTC ON | ON vs OFF |
|---|---:|---:|---:|
| Correct | 10/10 | 10/10 | tied |
| Reported cost | **$0.4818** | $0.6311 | +31.0% |
| Wall time | **371.8 s** | 441.4 s | +18.7% |
| Model/backend calls | 50 | **47** | -6.0% |
| Tool calls | 50 | **37** | -26.0% |
| Input tokens | **49,669** | 61,312 | +23.4% |
| Output tokens | **6,857** | 9,906 | +44.5% |
| Cache-read tokens | 55,552 | **54,656** | -1.6% |
| Timeouts | 0 | 0 | — |

## Interpretation

The typed interface achieved the expected behavioral effect: correct direct bindings, no discovery/dispatcher calls, fewer model turns, and substantially fewer tool calls. Unlike the paper’s compact Python stubs, this prototype injects complete raw JSON schemas. That context overhead, plus longer generated JavaScript, outweighed the call savings on these mostly small sequential coding tasks.

The benchmark also has a 10/10 native-tool ceiling, so it cannot demonstrate an accuracy gain beyond parity. Typed PTC was useful on some higher-complexity cases—for example extension change used 6 versus 8 model calls and 5 versus 10 tool calls—but did not win in aggregate.

## Decision

- Keep native tools as the default for ordinary coding loops.
- Preserve typed PTC as a candidate for high-fan-out orchestration.
- If revisited, compile schemas into compact TypeScript/Python-like signatures once, rather than injecting raw JSON schema every turn.

## Limitations

One repetition per arm, fixed OFF→ON order, local execution rather than Harbor containers, and Pi-reported usage metadata. The paper evaluates function-call argument correctness on BFCL; this campaign evaluates end-to-end coding tasks.
