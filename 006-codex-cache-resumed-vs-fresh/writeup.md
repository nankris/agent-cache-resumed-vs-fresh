# One long Codex session or a fresh one per task? At 14 tasks, it's a tie

*Draft. Tech in General experiment #006. Numbers are from 84 headless Codex tasks on 2026-10-14 (3 chains of 14 tasks per arm). All $ figures are estimates at API list price.*

If you hand a coding agent a list of small jobs, you can keep one session going or start fresh for each one. One session means the agent re-reads everything that happened so far on every turn. That sounds expensive, but the repeated part is cached, and cached input is billed at a twentieth of the normal rate. So which is cheaper?

## The setup

Codex CLI 0.162.1 (gpt-6.1-sol, ChatGPT Plus login) fixed the same 14 small JavaScript packages, one per task, in a fixed order:

- **fresh**: a new `codex exec` for every package
- **resumed**: one session, continued with `codex exec resume` for each package

Three chains of 14 each. Same prompt, same folder, same checks.

## What happened

All 84 tasks (42 per arm) passed. The token counts looked very different, but the cost didn't:

| | Tokens per 14 tasks | Cached share | Model calls | Est. cost |
|---|---|---|---|---|
| fresh exec per task | 0.90M | 88% | 58 | $0.342 |
| one resumed session | 1.62M | 95% | 44 | $0.352 |

The resumed session read 80% more tokens and cost about 3% more, which is inside the run-to-run spread (fresh chains ranged from $0.314 to $0.363).

## Why it nets out

The two arms pay in different places:

- **Fresh runs pay for new input.** Each new session's first request has to be read uncached, and the agent re-explores the folder every time: about 4 model calls per task. That's 105K uncached tokens per 14 tasks.
- **The resumed session pays for history.** By task 14 every turn re-sends 120–180K tokens. They're almost all cache hits, but 1.5M cache reads still add about 15 cents. It already knows the folder, so it needs about 3 calls per task and only 77K uncached tokens.

At 14 tasks those roughly cancel. The resumed session's cost per turn keeps climbing, though, so on a longer list fresh runs pull ahead, unless you also compact. In #012, the same resumed session with compaction at 25K tokens came in at $0.275, cheaper than either arm here.

## The takeaway

Don't keep a session alive just to save money on independent tasks. It's a tie at this length and gets worse as the session grows. Keep it alive when later tasks need earlier context, and turn on early compaction if you do.

*Caveats: 3 chains per arm; the resumed arm reuses #012's default runs rather than a separate run; cache hits are decided by the provider and can vary by load. Full tables and raw logs are in the repo README.*
