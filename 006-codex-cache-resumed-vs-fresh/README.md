# #006 Cache hits: one resumed Codex session vs a fresh `codex exec` per task

**Question.** For a string of small tasks, is it cheaper to keep one Codex session going (`codex exec resume`, so the history is a cached prefix) or to start a fresh `codex exec` for every task?

**Short answer (this build, these tasks).** About the same. The resumed session read **1.8× the tokens** (1.62M vs 0.90M per 14 tasks) at a higher cache share (95% vs 88%), but estimated cost was within noise: **$0.352 vs $0.342** per 14 tasks (*estimates*, ranges overlap). Fresh runs paid more uncached input (105K vs 77K) and made more model calls (58 vs 44 per 14 tasks), because each one re-explored the folder from scratch; the resumed session paid to re-read its growing history. All 84 tasks passed (3 chains × 14 per arm).

## Setup

- Codex CLI `codex-cli 0.162.1`, model `gpt-6.1-sol`, default reasoning effort, ChatGPT Plus login, headless `codex exec --json`.
- Workload: the 14-package suite (`scripts/harness/fixtures/SUITE14`: N01–N03 noisy-log bugs, T01–T11 small edit tasks), one package per task, fixed order, one shared working directory per chain. Same per-task prompt in both arms: ``Make `node test.js` pass inside the package folder `<pkg>/` by fixing that package's code. Do not edit any test.js. Only work on <pkg>/ in this turn.``
- Arms:
  - `fresh exec per task`: a new `codex exec` for each package (`FRESH=1 chain.sh`), reps 1, 2, 3 (`results/runs.csv`).
  - `one resumed session`: first package with `codex exec`, then `codex exec resume <thread_id>` for the other 13. **Not re-run here**: these are the `default` arm of #012 (same config, same suite, same prompts), reps 1, 3, 4, copied to `results/resumed_from_012.csv`. #012's rep 2 was lost to a sandbox restart.
- Pass = the package's `node test.js` exits 0 and no `test.js` changed (hash check).
- Cost estimate: gpt-6.1-sol API list price $2.00/M uncached input, $0.10/M cached input, $10.00/M output (https://developers.openai.com/api/docs/models/gpt-6.1-sol, checked 2026-10-14). **All $ figures are estimates**; Plus is a flat subscription.

## Exact commands

```bash
source /workspace/tools/setup.sh
FRESH=1 scripts/harness/chain.sh . fresh 1     # one fresh-exec chain; reps 1-2 via scripts/run_fresh.sh, rep 3 the same way
# resumed arm: rows with cond=default from ../012-codex-early-vs-late-compaction/results/runs.csv
/workspace/tools/mlenv/bin/python scripts/analyze.py
```

## Results (2026-10-14, fresh reps 14:25–15:21 UTC; resumed reps 14:19–15:21 UTC)

| Arm | Chain | Tasks passed | Total tokens | Cached input | Uncached input | Output | Cache share | Model calls | Est. cost |
|---|---|---|---|---|---|---|---|---|---|
| fresh exec | r1 | 14/14 | 0.89M | 768K | 115.6K | 5.5K | 86.9% | 57 | $0.363 |
| fresh exec | r2 | 14/14 | 0.89M | 792K | 92.0K | 5.1K | 89.6% | 58 | $0.314 |
| fresh exec | r3 | 14/14 | 0.92M | 804K | 108.6K | 5.2K | 88.1% | 59 | $0.349 |
| resumed | r1 | 14/14 | 2.05M | 1,981K | 59.2K | 4.5K | 97.1% | 45 | $0.362 |
| resumed | r3 | 14/14 | 1.48M | 1,398K | 82.2K | 4.3K | 94.5% | 43 | $0.347 |
| resumed | r4 | 14/14 | 1.34M | 1,247K | 90.4K | 4.0K | 93.2% | 44 | $0.346 |

| Arm | Chains | Total tokens | Uncached input | Output | Cache share | Est. cost / 14 tasks (range) |
|---|---|---|---|---|---|---|
| fresh exec per task | 3 | 0.90M | 105.4K | 5.3K | 88.2% | $0.342 ($0.314–0.363) |
| one resumed session | 3 | 1.62M | 77.3K | 4.3K | 94.9% | $0.352 ($0.346–0.362) |

Chart: `results/chart.png` (input tokens per turn, uncached input per turn, token mix per arm).

### What the numbers say
1. **Fresh runs are flat; resumed runs grow.** A fresh run costs ~58–75K input tokens per task, every time. The resumed session starts near 60–90K and climbs to 120–180K per turn by task 14.
2. **Cache saves the resumed session.** 95% of its input was cache reads. Its uncached input per turn fell to 1–3K on most turns, while fresh runs paid 3–19K uncached per task (the first request of each new session).
3. **Net: a wash on cost at 14 tasks.** The resumed arm's extra 0.7M cached tokens (~$0.07) roughly cancel its savings on uncached input and output. Past ~14 tasks the resumed session's cost per turn keeps rising, so a longer string would favour fresh runs (or a resumed session with compaction; see #012, where compacting at 25K brought the resumed session to $0.275).
4. Wall time isn't comparable: arms ran in parallel with other experiments on the same account.

## Caveats
- n = 3 chains per arm, small independent tasks. The resumed arm was borrowed from #012 rather than run alongside, though same config and same day.
- Cache hits are decided server-side; a different time of day or load could change cache share.
- 5 fresh tasks hit transient 429 "Reconnecting…" retries (8 total) that Codex recovered from.
- Default reasoning effort; reasoning tokens were reported as 0.

## Files
- `scripts/harness/`: copy of the shared harness (`run_one.py`, `chain.sh`, `driver.sh`, `backfill.py`, fixtures)
- `scripts/run_fresh.sh`, `scripts/analyze.py`
- `results/runs.csv` (fresh arm, one row per task), `results/resumed_from_012.csv` (resumed arm), `results/per_turn.csv`, `results/summary.csv`, `results/summary_by_arm.csv`, `results/chain.log`
- `results/raw/*.jsonl`: raw `codex exec --json` streams for the fresh arm (resumed-arm raw streams are in the #012 repo)
